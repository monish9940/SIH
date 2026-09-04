import cv2
import numpy as np
import re
import os
import time
import logging
import threading

logger = logging.getLogger("ocr_service")

# ──────────────────────────────────────────────
# CPU Thread tuning (PyTorch / BLAS)
# ──────────────────────────────────────────────
try:
    import torch
    torch.set_num_threads(max(1, os.cpu_count() or 4))
except Exception:
    pass

# ──────────────────────────────────────────────
# Singleton OCR Reader
# Initialised ONCE at startup (main.py lifespan),
# reused for every subsequent request.
# ──────────────────────────────────────────────
_easyocr_reader = None          # None  → not yet initialised
_easyocr_init_failed = False    # True  → init already tried and failed
_easyocr_lock = threading.Lock()

# ── Performance constants ─────────────────────────────────────────────────
# Reducing image size and canvas is the single biggest CPU speed lever.
_TARGET_MAX_DIM   = 960    # Shrink images to ≤960px — still plenty for label text
_CANVAS_SIZE      = 640    # EasyOCR internal canvas — 640 is the sweet-spot on CPU
# Pass-2 (CLAHE) is expensive (~same cost as pass 1). Only trigger it for
# genuinely poor captures: very few blocks AND very low confidence.
_FALLBACK_CONF    = 0.45   # was 0.72 — dramatically reduces unnecessary double-passes
_FALLBACK_MIN_BLOCKS = 3   # was 6  — only retry if almost nothing was detected


def get_easyocr_reader():
    """Return the singleton EasyOCR Reader, initialising it if necessary."""
    global _easyocr_reader, _easyocr_init_failed
    if _easyocr_reader is not None:
        return _easyocr_reader
    if _easyocr_init_failed:
        return None

    with _easyocr_lock:
        # Double-checked locking
        if _easyocr_reader is not None:
            return _easyocr_reader
        if _easyocr_init_failed:
            return None
        try:
            import easyocr
            _easyocr_reader = easyocr.Reader(
                ['en'],
                gpu=False,
                verbose=False,
                quantize=True,          # FP16 quantised CRNN — faster on CPU
            )
            logger.info("EasyOCR Reader initialised successfully (quantized CPU mode).")
        except Exception as e:
            logger.warning(f"EasyOCR initialisation failed: {e}")
            _easyocr_init_failed = True
    return _easyocr_reader


# ──────────────────────────────────────────────
# Image Preprocessing
# ──────────────────────────────────────────────
def preprocess_image_fast(image_path: str,
                           target_max_dim: int = _TARGET_MAX_DIM
                           ) -> tuple[np.ndarray, float]:
    """
    Read image and resize (downscale only) to target_max_dim while keeping
    aspect ratio.  INTER_AREA gives the sharpest result for downscaling text.
    Returns (optimised_image, scale_factor).
    """
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not read image file: {image_path}")

    h, w = img.shape[:2]
    max_dim = max(h, w)

    if max_dim > target_max_dim:
        scale = float(target_max_dim) / max_dim
        new_w, new_h = int(w * scale), int(h * scale)
        img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
    else:
        scale = 1.0

    return img, scale


# ──────────────────────────────────────────────
# Block / Line Parsing
# ──────────────────────────────────────────────
def parse_easyocr_blocks(results, mode: str = "standard") -> list[dict]:
    blocks = []
    seen_keys: set[str] = set()

    for bbox, text, prob in results:
        text_clean = text.strip()
        if not text_clean or prob < 0.15:
            continue

        xs = [pt[0] for pt in bbox]
        ys = [pt[1] for pt in bbox]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        cy = (min_y + max_y) / 2.0
        cx = (min_x + max_x) / 2.0

        dedup_key = f"{text_clean.lower()}_{int(cy / 15)}_{int(cx / 15)}"
        if dedup_key in seen_keys:
            continue
        seen_keys.add(dedup_key)

        blocks.append({
            "text":  text_clean,
            "prob":  float(prob),
            "bbox":  bbox,
            "cy":    cy,
            "cx":    cx,
            "min_y": min_y,
            "max_y": max_y,
            "min_x": min_x,
            "max_x": max_x,
            "mode":  mode,
        })
    return blocks


def reconstruct_2d_lines(blocks: list[dict]) -> list[str]:
    """Sort blocks into reading order and merge blocks on the same line."""
    blocks = sorted(blocks, key=lambda b: (b["cy"], b["cx"]))
    lines: list[list[dict]] = []
    cur_line: list[dict] = []
    last_y: float | None = None

    for b in blocks:
        if last_y is None or abs(b["cy"] - last_y) < 18:
            cur_line.append(b)
            last_y = b["cy"] if last_y is None else (last_y + b["cy"]) / 2.0
        else:
            cur_line.sort(key=lambda x: x["cx"])
            lines.append(cur_line)
            cur_line = [b]
            last_y = b["cy"]

    if cur_line:
        cur_line.sort(key=lambda x: x["cx"])
        lines.append(cur_line)

    return [" ".join(b["text"] for b in line) for line in lines]


# ──────────────────────────────────────────────
# Main OCR Pipeline
# ──────────────────────────────────────────────
def run_ocr_with_metrics(image_path: str) -> tuple[str, float, dict]:
    """
    Single-pass OCR pipeline with optional CLAHE fallback.

    Returns (full_text, avg_confidence, metrics_dict).

    Timing metrics (all in seconds):
        image_read_sec       – imread + resize
        model_init_sec       – first-call model load (0 on warm subsequent calls)
        ocr_inference_sec    – readtext() wall time (pass 1 + optional pass 2)
        ocr_postproc_sec     – block merge + line reconstruction
        num_passes           – 1 or 2
    """
    metrics: dict = {}

    # 1. Image read + preprocess
    t0 = time.time()
    img_opt, _scale = preprocess_image_fast(image_path, target_max_dim=_TARGET_MAX_DIM)
    metrics["image_read_sec"] = round(time.time() - t0, 4)

    # 2. Model access (singleton — nearly instant after first call)
    t0 = time.time()
    reader = get_easyocr_reader()
    metrics["model_init_sec"] = round(time.time() - t0, 4)

    if not reader:
        logger.error("EasyOCR reader unavailable — returning empty OCR result.")
        metrics.update({"ocr_inference_sec": 0.0, "ocr_postproc_sec": 0.0, "num_passes": 0})
        return "", 0.0, metrics

    # 3. Pass 1 — OCR on optimised image
    # Tuned readtext params for CPU speed:
    #   text_threshold=0.6  – skip very faint text candidates (saves detection time)
    #   low_text=0.35       – lower sensitivity = fewer false region proposals
    #   width_ths=0.7       – merge close horizontal boxes (fewer recognition calls)
    #   workers=0           – disable multiprocessing fork overhead per call
    t0 = time.time()
    results_p1 = reader.readtext(
        img_opt,
        canvas_size=_CANVAS_SIZE,
        detail=1,
        text_threshold=0.6,
        low_text=0.35,
        width_ths=0.7,
        workers=0,
    )
    inf1_sec = time.time() - t0

    blocks_p1 = parse_easyocr_blocks(results_p1, mode="standard")
    avg_conf_p1 = float(np.mean([b["prob"] for b in blocks_p1])) if blocks_p1 else 0.0

    # 4. Decide whether a second pass is needed.
    # Only run CLAHE pass for genuinely bad captures (almost nothing detected
    # AND very low confidence). Most label photos will skip this.
    need_pass2 = avg_conf_p1 < _FALLBACK_CONF and len(blocks_p1) < _FALLBACK_MIN_BLOCKS
    inf2_sec = 0.0
    blocks_p2: list[dict] = []

    if need_pass2:
        logger.info(
            f"Pass-1 conf={avg_conf_p1:.2f}, blocks={len(blocks_p1)} "
            f"→ running CLAHE fallback pass (threshold: conf<{_FALLBACK_CONF} AND blocks<{_FALLBACK_MIN_BLOCKS})."
        )
        t0 = time.time()
        try:
            gray = cv2.cvtColor(img_opt, cv2.COLOR_BGR2GRAY)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)
            enhanced_bgr = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)
            results_p2 = reader.readtext(
                enhanced_bgr,
                canvas_size=_CANVAS_SIZE,
                detail=1,
                text_threshold=0.6,
                low_text=0.35,
                width_ths=0.7,
                workers=0,
            )
            blocks_p2 = parse_easyocr_blocks(results_p2, mode="clahe")
        except Exception as exc:
            logger.debug(f"CLAHE pass error: {exc}")
        inf2_sec = time.time() - t0

    # 5. Merge blocks and reconstruct text
    t0 = time.time()
    combined = blocks_p1 + blocks_p2
    lines = reconstruct_2d_lines(combined)
    full_text = "\n".join(lines)
    avg_conf = float(np.mean([b["prob"] for b in combined])) if combined else 0.70
    metrics["ocr_postproc_sec"] = round(time.time() - t0, 4)

    metrics["ocr_inference_sec"] = round(inf1_sec + inf2_sec, 4)
    metrics["num_passes"] = 2 if need_pass2 else 1

    logger.info(
        f"OCR done — passes={metrics['num_passes']}, "
        f"blocks={len(combined)}, conf={avg_conf:.2f}, "
        f"inference={metrics['ocr_inference_sec']}s"
    )
    return full_text, avg_conf, metrics


def run_ocr(image_path: str) -> tuple[str, float]:
    """Backward-compatible wrapper."""
    full_text, ocr_conf, _ = run_ocr_with_metrics(image_path)
    return full_text, ocr_conf


# ──────────────────────────────────────────────
# Field Extraction
# ──────────────────────────────────────────────
def extract_structured_fields(raw_text: str, filename: str = "") -> dict:
    """
    Extract Legal Metrology mandatory fields from OCR raw text.

    All fields extracted from the SAME OCR output — no additional OCR calls.
    """
    text_upper = raw_text.upper()
    lines_upper = [ln.strip().upper() for ln in raw_text.split("\n") if ln.strip()]

    # ── 1. Product Name / Brand ──────────────────────────────────────────
    product_val: str | None = None
    product_conf = 0.0

    BRAND_MAP = {
        "LAY'S": "Lay's Potato Chips",
        "LAYS":  "Lay's Potato Chips",
        "KURKURE": "Kurkure Snacks",
        "DORITOS": "Doritos Tortilla Chips",
        "PRINGLES": "Pringles Potato Crisp",
        "AMUL": "Amul Dairy Product",
        "BRITANNIA": "Britannia Biscuits/Snack",
        "KAMA FOODS": "Kama Foods Premium Basmati Rice",
        "BASMATI RICE": "Kama Foods Premium Basmati Rice",
        "MAGGI": "Maggi Noodles",
        "HALDIRAM": "Haldiram's Snacks",
        "PARLE": "Parle Products",
        "BINGO": "Bingo! Snacks",
        "TOO YUMM": "Too Yumm! Snacks",
        "SUNFEAST": "Sunfeast Products",
    }
    for keyword, brand_name in BRAND_MAP.items():
        if keyword in text_upper:
            product_val = brand_name
            product_conf = 0.95
            break

    if product_val is None:
        m = re.search(
            r'(?:PRODUCT|ITEM|COMMODITY|NAME)\s*[:=]?\s*([A-Z0-9][A-Z0-9\s\-]{2,39})',
            text_upper,
        )
        if m:
            product_val = m.group(1).strip().title()
            product_conf = 0.82

    # ── 2. MRP Extraction ────────────────────────────────────────────────
    # Strategy: scan every line.  If a line carries an MRP/RS/₹ keyword, collect
    # that keyword's "signal" and apply it to numbers found on the SAME line AND
    # on the immediately-following line.  This correctly handles layouts like:
    #
    #   Line N  : "MRP (INCL. OF ALL TAXES)"
    #   Line N+1: "Rs. 48/-"
    #
    mrp_val: str | None = None
    mrp_conf = 0.0
    mrp_candidates: list[tuple[int, float]] = []  # (score, value)

    # Pre-scan: build per-line keyword flag sets
    MRP_KWS  = {"MRP", "RETAIL PRICE", "MAXIMUM RETAIL PRICE"}
    RS_KWS   = {"RS.", "RS .", "RS:", "₹", "INR"}
    TAX_KWS  = {"INCL", "INCL.", "ALL TAXES", "INCLUSIVE", "INCLUDING TAX"}
    SKIP_KWS = {
        "FSSAI", "TEL:", "FAX:", "PIN:", "PO BOX", "NUTRITIONAL", "LICENCE", "LIC.NO",
        # Date / batch / mfg lines must NEVER be used for MRP
        "MFG DATE", "MFG DATE:", "MFD BY", "MANUFACTURED", "DATE OF MFG",
        "PACKED ON", "PKD ON", "PKD:", "MFD:", "EXP DATE", "EXPIRY",
        "BEST BEFORE", "USE BY", "BATCH NO", "LOT NO", "BATCH:", "LOT:",
    }

    def _line_flags(line: str) -> tuple[bool, bool, bool]:
        has_mrp = any(k in line for k in MRP_KWS)
        has_rs  = any(k in line for k in RS_KWS) or bool(re.search(r'\bRS\b', line))
        has_tax = any(k in line for k in TAX_KWS)
        return has_mrp, has_rs, has_tax

    def _score_candidate(val: float, has_mrp: bool, has_rs: bool, has_tax: bool,
                          from_next_line: bool) -> int:
        if val <= 0 or val > 1000:    # realistic max ₹1000 for typical packaged goods
            return -1
        score = 0
        if has_mrp: score += 50
        if has_rs:  score += 35
        if has_tax: score += 30
        if from_next_line:
            # line following an MRP-keyword line: give a small bonus
            score += 10
        return score

    # Number pattern: optional ₹/RS prefix, then 1–4 digits, optional decimal or /-
    _NUM_PAT = re.compile(
        r'(?:₹\s*|RS\.?\s*|INR\s*)?(\d{1,4}(?:\.\d{1,2})?(?:/-)?)'
        r'(?!\s*(?:KG|GMS?|G\b|ML|L\b|CAL|KCAL|DV\b|MG|MONTHS?|DAYS?|YEARS?|LIC|NO\b))',
        re.IGNORECASE,
    )
    _FSSAI_PAT = re.compile(r'100\d{11}')          # 14-digit FSSAI licence numbers
    _BARCODE_PAT = re.compile(r'BARCODE\s*!?\s*\d+', re.IGNORECASE)

    # Carry-forward keyword flags from line above (for "MRP" on one line, price on next)
    # Reset after finding a strong candidate to avoid bleeding into date lines.
    prev_has_mrp = prev_has_rs = prev_has_tax = False
    found_strong_candidate = False

    for i, line_str in enumerate(lines_upper):
        if any(bad in line_str for bad in SKIP_KWS):
            prev_has_mrp = prev_has_rs = prev_has_tax = False
            found_strong_candidate = False
            continue

        cur_has_mrp, cur_has_rs, cur_has_tax = _line_flags(line_str)

        # Clean FSSAI and barcode sequences from line before number extraction
        cleaned = _FSSAI_PAT.sub("", line_str)
        cleaned = _BARCODE_PAT.sub("", cleaned)

        line_best_score = 0
        for m in _NUM_PAT.finditer(cleaned):
            num_raw = m.group(1).replace("/-", "").replace(" ", "")
            try:
                val = float(num_raw)
            except ValueError:
                continue

            # Score using current-line flags COMBINED with previous-line flags (carry-forward)
            # But ONLY use carry-forward if we haven't already locked in a strong candidate
            eff_mrp = cur_has_mrp or (prev_has_mrp and not found_strong_candidate)
            eff_rs  = cur_has_rs  or (prev_has_rs  and not found_strong_candidate)
            eff_tax = cur_has_tax or (prev_has_tax  and not found_strong_candidate)
            from_next = (prev_has_mrp and not cur_has_mrp) and not found_strong_candidate

            s = _score_candidate(val, eff_mrp, eff_rs, eff_tax, from_next)
            if s >= 35:
                mrp_candidates.append((s, val))
                if s > line_best_score:
                    line_best_score = s

        # If we found a high-confidence candidate on this line, stop carrying forward
        # so subsequent lines (e.g. MFG DATE) don't inherit MRP context
        if line_best_score >= 85:
            found_strong_candidate = True
            prev_has_mrp = prev_has_rs = prev_has_tax = False
        else:
            # Carry MRP/RS keywords to next line (handles price on separate line)
            prev_has_mrp = cur_has_mrp
            prev_has_rs  = cur_has_rs
            prev_has_tax = cur_has_tax

    if mrp_candidates:
        mrp_candidates.sort(key=lambda x: (-x[0], x[1]))  # highest score, then smallest value
        best_score, best_val = mrp_candidates[0]
        mrp_val  = f"₹ {int(best_val)}" if best_val == int(best_val) else f"₹ {best_val:.2f}"
        mrp_conf = 0.92 if best_score >= 70 else (0.82 if best_score >= 50 else 0.72)

    # ── 3. Net Quantity ──────────────────────────────────────────────────
    net_val: str | None = None
    net_conf = 0.0
    net_candidates: list[tuple[int, str]] = []

    UNIT_MAP = {
        "g": "g", "gm": "g", "gms": "g", "gram": "g", "grams": "g",
        "kg": "kg", "kgs": "kg", "kilogram": "kg", "kilograms": "kg",
        "ml": "ml", "mls": "ml", "milliliter": "ml", "milliliters": "ml",
        "l": "l", "ltr": "l", "liter": "l", "liters": "l", "litre": "l", "litres": "l",
    }
    NET_KWS = {
        "NET QTY", "NET QUANTITY", "NET WT", "NET WEIGHT",
        "NETT QTY", "NET VOL", "NET VOLUME", "NET CONTENT",
    }
    # Nutritional info lines to skip
    NUTR_SKIP = {"NUTRITION", "PER 100G", "SERVING SIZE", "ENERGY", "PROTEIN", "CARBOHYDRATE"}

    # Strict quantity pattern: number immediately followed by unit (no gap or single space)
    _QTY_PAT = re.compile(r'(\d+(?:\.\d+)?)\s{0,2}(g|gm|gms|grams?|kg|kgs?|ml|mls?|l|ltr|litre?s?|liters?)\b',
                           re.IGNORECASE)

    for i, line_str in enumerate(lines_upper):
        if any(bad in line_str for bad in NUTR_SKIP):
            continue

        has_net_kw = any(kw in line_str for kw in NET_KWS)
        # Also check next line for the value when keyword is on its own line
        check_text = line_str
        if i < len(lines_upper) - 1 and has_net_kw:
            check_text += " " + lines_upper[i + 1]

        for qm in _QTY_PAT.finditer(check_text):
            amount_str = qm.group(1)
            unit_raw   = qm.group(2).lower()
            unit_str   = UNIT_MAP.get(unit_raw)
            if not unit_str:
                continue

            try:
                amount_val = float(amount_str)
            except ValueError:
                continue

            # Ignore clearly nutritional amounts (very small or 100 g per-serving)
            if unit_str == "g" and amount_val == 100.0 and not has_net_kw:
                continue

            score = 75 if has_net_kw else 40
            if unit_str in ("g", "kg", "ml", "l"):
                score += 15

            net_candidates.append((score, f"{amount_str} {unit_str}"))

    if net_candidates:
        net_candidates.sort(key=lambda x: -x[0])
        net_val  = net_candidates[0][1]
        net_conf = 0.90 if net_candidates[0][0] >= 75 else 0.72

    # ── 4. Manufacturing & Expiry Dates ──────────────────────────────────
    mfg_val: str | None = None
    mfg_conf = 0.0
    exp_val: str | None = None
    exp_conf = 0.0

    _DATE_PAT = re.compile(
        r'(\d{1,2}[\/\.\-]\d{1,2}[\/\.\-]\d{2,4}'
        r'|\d{2}[\/\.\-]\d{4}'
        r'|[A-Z]{3}[\/\.\-]\d{2,4}'
        r'|\d{2}[\/\.\-]\d{2}[\/\.\-]\d{2})'
    )
    EXP_KWS = {"EXP", "EXPIRY", "BEST BEFORE", "USE BY", "BB", "BBE"}
    MFG_KWS = {"MFG", "MFD", "PACKED", "PKD", "DATE OF MFG", "MFG DATE", "MANUFACTURED ON"}

    for line_str in lines_upper:
        if any(kw in line_str for kw in EXP_KWS) and exp_val is None:
            dm = _DATE_PAT.search(line_str)
            if dm:
                exp_val  = dm.group(1)
                exp_conf = 0.88

        if any(kw in line_str for kw in MFG_KWS) and mfg_val is None:
            dm = _DATE_PAT.search(line_str)
            if dm:
                mfg_val  = dm.group(1)
                mfg_conf = 0.88

    # ── 5. Batch Number ──────────────────────────────────────────────────
    batch_val: str | None = None
    batch_conf = 0.0
    bm = re.search(r'(?:BATCH|BATCH NO|LOT|B\.NO|LOT NO)\s*[:=\.#]?\s*([A-Z0-9][A-Z0-9\-]{1,20})',
                   text_upper)
    if bm:
        batch_val  = bm.group(1).strip()
        batch_conf = 0.89

    # ── 6. Manufacturer ──────────────────────────────────────────────────
    mfr_val: str | None = None
    mfr_conf = 0.0

    MANUF_MAP = {
        "PEPSICO":    "PepsiCo India Holdings Pvt. Ltd.",
        "APEX FOODS": "Apex Foods Pvt. Ltd.",
        "NESTLE":     "Nestle India Limited",
        "ITC LTD":    "ITC Limited",
        "PARLE AGRO": "Parle Agro Pvt. Ltd.",
        "HINDUSTAN UNILEVER": "Hindustan Unilever Limited",
        "BRITANNIA INDUSTRIES": "Britannia Industries Limited",
        "HALDIRAM":   "Haldiram Foods International Pvt. Ltd.",
    }
    for keyword, manuf_name in MANUF_MAP.items():
        if keyword in text_upper:
            mfr_val  = manuf_name
            mfr_conf = 0.95
            break

    if mfr_val is None:
        mm = re.search(
            r'(?:MFD BY|MANUFACTURED BY|PACKED BY|MFRD BY|MFR)\s*[:=]?\s*'
            r'([A-Z][A-Z0-9\s,\.\(\)\-\&]{4,70})',
            text_upper,
        )
        if mm:
            mfr_val  = mm.group(1).strip().title()
            mfr_conf = 0.82

    # ── 7. Consumer Care ─────────────────────────────────────────────────
    care_val: str | None = None
    care_conf = 0.0

    cm = re.search(
        r'(?:CONSUMER CARE|CUSTOMER CARE|HELPLINE|CARE MANAGER|CARE LINE)\s*[:=]?\s*'
        r'([A-Z0-9][A-Z0-9\s,@\.\-\+]{4,70})',
        text_upper,
    )
    if cm:
        care_val  = cm.group(1).strip()
        care_conf = 0.87
    else:
        toll_m = re.search(
            r'(?:1800[\s\-]?\d{3}[\s\-]?\d{4}|WECARE@[A-Z0-9\.]+|CARE@[A-Z0-9\.]+)',
            text_upper,
        )
        if toll_m:
            care_val  = toll_m.group(0)
            care_conf = 0.88

    # ── 8. Country of Origin ─────────────────────────────────────────────
    origin_val: str | None = None
    origin_conf = 0.0

    om = re.search(r'(?:MADE IN|COUNTRY OF ORIGIN|ORIGIN)\s*[:=]?\s*([A-Z][A-Z\s]{1,30})',
                   text_upper)
    if om:
        origin_val  = om.group(1).strip().title()
        origin_conf = 0.95
    elif "INDIA" in text_upper:
        origin_val  = "India"
        origin_conf = 0.85

    # ── Assemble result ───────────────────────────────────────────────────
    structured = {
        # Nested (with confidence)
        "product_name":       {"value": product_val,  "confidence": product_conf},
        "net_quantity":       {"value": net_val,       "confidence": net_conf},
        "mrp":                {"value": mrp_val,       "confidence": mrp_conf},
        "manufacturer":       {"value": mfr_val,       "confidence": mfr_conf},
        "batch_number":       {"value": batch_val,     "confidence": batch_conf},
        "manufacturing_date": {"value": mfg_val,       "confidence": mfg_conf},
        "expiry_date":        {"value": exp_val,       "confidence": exp_conf},
        "country_of_origin":  {"value": origin_val,   "confidence": origin_conf},
        "consumer_care":      {"value": care_val,      "confidence": care_conf},
        # Flattened shortcuts (for direct template/router binding)
        "product_name_raw":   product_val,
        "net_quantity_raw":   net_val,
        "mrp_raw":            mrp_val,
        "manufacturer_raw":   mfr_val,
        "mfg_date_raw":       mfg_val,
        "consumer_care_raw":  care_val,
        "country_of_origin_raw": origin_val,
    }
    return structured

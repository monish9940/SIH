import cv2
import numpy as np
import re
import os
import time
import logging
import threading
import gc
from app.config import settings

logger = logging.getLogger("ocr_service")

# ──────────────────────────────────────────────
# CPU Thread tuning (PyTorch / BLAS)
# Configure via settings to prevent excessive memory allocation overhead
# ──────────────────────────────────────────────
try:
    import torch
    torch.set_num_threads(settings.OCR_CPU_THREADS)
    if hasattr(torch, "set_num_interop_threads"):
        try:
            torch.set_num_interop_threads(settings.OCR_CPU_THREADS)
        except Exception:
            pass
except Exception:
    pass

# ──────────────────────────────────────────────
# Singleton OCR Reader
# Initialised ONCE at startup (main.py lifespan),
# reused for every subsequent request.
# ──────────────────────────────────────────────
_easyocr_reader = None
_easyocr_lock = threading.Lock()
_ocr_ready = False
_easyocr_init_error = None

MODEL_DIR = os.getenv("EASYOCR_MODEL_DIR", "/app/models/easyocr" if os.path.exists("/app") else os.path.join(os.getcwd(), "models", "easyocr"))
MODEL_DIR = os.path.abspath(MODEL_DIR)
try:
    os.makedirs(MODEL_DIR, exist_ok=True)
except Exception:
    pass

# ── Performance constants ─────────────────────────────────────────────────
_TARGET_MAX_DIM   = settings.OCR_MAX_IMAGE_DIM   # Max dimension for fast image downscaling
_CANVAS_SIZE      = 1024   # EasyOCR internal canvas size for CPU processing
_FALLBACK_CONF    = settings.OCR_CONFIDENCE_THRESHOLD
_FALLBACK_MIN_BLOCKS = 3   # only retry if almost nothing was detected
_REGION_AWARE     = settings.OCR_REGION_AWARE     # Enable region-aware OCR pipeline

# ── Region-aware OCR constants ────────────────────────────────────────────
_MIN_REGION_AREA_RATIO = 0.002   # Minimum region area as fraction of image area
_REGION_PADDING_FRAC   = 0.08    # Padding around detected regions (fraction of region size)
_REGION_MERGE_GAP      = 25      # Pixels: merge regions closer than this
_MIN_IMAGE_AREA_FOR_REGIONS = 200 * 200  # Only use region detection on images large enough
_LOW_CONF_THRESHOLD    = 0.55    # Regions below this get selective reprocessing
_MIN_REGIONS_FOR_BENEFIT = 2     # Need at least this many regions for region-OCR to help


# ──────────────────────────────────────────────
# Region Detection (lightweight OpenCV, no ML)
# ──────────────────────────────────────────────
def _detect_text_regions(img: np.ndarray) -> list[dict]:
    """
    Detect likely text-containing regions using lightweight OpenCV techniques.
    Returns list of region dicts with keys: x, y, w, h, area, label.

    Strategy:
    1. Convert to grayscale and apply adaptive threshold
    2. Morphological close to connect nearby text characters into blocks
    3. Find contours of connected components
    4. Filter out non-text regions (barcodes, blanks, tiny noise)
    """
    h, w = img.shape[:2]
    img_area = h * w

    # Grayscale + bilateral filter (preserves edges, smooths noise)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img.copy()

    # Adaptive threshold to highlight text against background
    binary = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV, blockSize=15, C=8
    )

    # Morphological close: connect nearby text characters into blocks
    # Use a wide horizontal kernel to merge characters on the same line
    kernel_h = cv2.getStructuringElement(cv2.MORPH_RECT, (max(w // 15, 12), 3))
    closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel_h)

    # Vertical dilation to merge lines that are close vertically
    kernel_v = cv2.getStructuringElement(cv2.MORPH_RECT, (1, max(h // 40, 5)))
    closed = cv2.dilate(closed, kernel_v, iterations=2)

    # Find contours of the connected regions
    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    regions = []
    min_area = img_area * _MIN_REGION_AREA_RATIO

    for cnt in contours:
        x, y, rw, rh = cv2.boundingRect(cnt)
        area = rw * rh

        # Filter: too small (noise)
        if area < min_area:
            continue

        # Filter: too narrow or too short (decorative lines/borders)
        if rw < 15 or rh < 8:
            continue

        # Filter: extreme aspect ratio — likely barcode (very tall & narrow vertical lines)
        aspect = rw / max(rh, 1)
        if aspect > 20 or aspect < 0.05:
            continue

        # Filter: barcode detection — check for high-frequency vertical edges in the region
        if _is_barcode_region(gray, x, y, rw, rh):
            continue

        # Filter: blank region — very low pixel density in the binary mask
        region_binary = binary[y:y+rh, x:x+rw]
        pixel_density = np.count_nonzero(region_binary) / max(area, 1)
        if pixel_density < 0.02:
            continue

        # Classify region by vertical position
        cy = y + rh / 2
        vert_pos = cy / h
        if vert_pos < 0.20:
            label = "product_name"
        elif vert_pos < 0.45:
            label = "declarations"
        elif vert_pos < 0.65:
            label = "pricing_ingredients"
        elif vert_pos < 0.80:
            label = "manufacturer"
        else:
            label = "fssai_consumer_care"

        regions.append({
            "x": x, "y": y, "w": rw, "h": rh,
            "area": area, "label": label,
            "vert_pos": vert_pos,
        })

    return regions


def _is_barcode_region(gray: np.ndarray, x: int, y: int, w: int, h: int) -> bool:
    """Quick heuristic: barcodes have high-frequency vertical edge patterns."""
    if w < 30 or h < 20:
        return False
    crop = gray[y:y+h, x:x+w]
    # Sobel vertical edges
    sobel_x = cv2.Sobel(crop, cv2.CV_64F, 1, 0, ksize=3)
    # Count zero-crossings (alternating black/white bars)
    sign_changes = np.sum(np.diff(np.sign(sobel_x.mean(axis=0))) != 0)
    # Barcodes have many alternating edges relative to width
    return sign_changes > w * 0.3


def _merge_nearby_regions(regions: list[dict], gap: int = _REGION_MERGE_GAP) -> list[dict]:
    """Merge overlapping or nearby regions to reduce number of OCR calls."""
    if not regions:
        return []

    # Sort by y then x
    regions = sorted(regions, key=lambda r: (r["y"], r["x"]))
    merged = [regions[0].copy()]

    for r in regions[1:]:
        last = merged[-1]
        # Check if regions overlap or are within gap distance
        overlap_x = (r["x"] <= last["x"] + last["w"] + gap) and (r["x"] + r["w"] >= last["x"] - gap)
        overlap_y = (r["y"] <= last["y"] + last["h"] + gap) and (r["y"] + r["h"] >= last["y"] - gap)

        if overlap_x and overlap_y:
            # Merge: expand the last region to encompass both
            new_x = min(last["x"], r["x"])
            new_y = min(last["y"], r["y"])
            new_x2 = max(last["x"] + last["w"], r["x"] + r["w"])
            new_y2 = max(last["y"] + last["h"], r["y"] + r["h"])
            last["x"] = new_x
            last["y"] = new_y
            last["w"] = new_x2 - new_x
            last["h"] = new_y2 - new_y
            last["area"] = last["w"] * last["h"]
            # Keep the label of the larger region
            if r["area"] > last["area"]:
                last["label"] = r["label"]
        else:
            merged.append(r.copy())

    return merged


def _pad_region(region: dict, img_h: int, img_w: int) -> dict:
    """Add padding around a region, clamped to image bounds."""
    r = region.copy()
    pad_x = int(r["w"] * _REGION_PADDING_FRAC)
    pad_y = int(r["h"] * _REGION_PADDING_FRAC)
    # Minimum padding of 5 pixels
    pad_x = max(pad_x, 5)
    pad_y = max(pad_y, 5)

    r["x"] = max(0, r["x"] - pad_x)
    r["y"] = max(0, r["y"] - pad_y)
    r["w"] = min(img_w - r["x"], r["w"] + 2 * pad_x)
    r["h"] = min(img_h - r["y"], r["h"] + 2 * pad_y)
    return r


def _run_region_ocr(reader, img: np.ndarray, regions: list[dict]) -> list[dict]:
    """
    Run EasyOCR on each region crop and remap bounding boxes to full-image coords.
    Returns combined list of parsed blocks (same format as parse_easyocr_blocks output).
    """
    import torch
    all_blocks = []

    for region in regions:
        x, y, w, h = region["x"], region["y"], region["w"], region["h"]
        crop = img[y:y+h, x:x+w]

        if crop.size == 0 or crop.shape[0] < 8 or crop.shape[1] < 15:
            continue

        try:
            with torch.no_grad():
                results = reader.readtext(
                    crop,
                    canvas_size=min(_CANVAS_SIZE, max(w, h) + 100),
                    detail=1,
                    text_threshold=0.6,
                    low_text=0.35,
                    width_ths=0.7,
                    workers=0,
                )
        except Exception as err:
            logger.debug(f"Region OCR error at ({x},{y},{w},{h}): {err}")
            continue

        # Parse and remap coordinates to full-image space
        for bbox, text, prob in results:
            text_clean = text.strip()
            if not text_clean or prob < 0.15:
                continue

            # Remap bounding box: offset by region origin
            remapped_bbox = [[pt[0] + x, pt[1] + y] for pt in bbox]
            xs = [pt[0] for pt in remapped_bbox]
            ys = [pt[1] for pt in remapped_bbox]
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)
            cy = (min_y + max_y) / 2.0
            cx = (min_x + max_x) / 2.0

            all_blocks.append({
                "text":  text_clean,
                "prob":  float(prob),
                "bbox":  remapped_bbox,
                "cy":    cy,
                "cx":    cx,
                "min_y": min_y,
                "max_y": max_y,
                "min_x": min_x,
                "max_x": max_x,
                "mode":  "region",
                "region_label": region.get("label", "unknown"),
            })

    return all_blocks


def _selective_reprocess(reader, img: np.ndarray, blocks: list[dict],
                         regions: list[dict]) -> tuple[list[dict], list[str]]:
    """
    Confidence-based selective reprocessing: only low-confidence regions get
    CLAHE enhancement + re-OCR. NOT the entire image.
    Returns (updated_blocks, list_of_reprocessed_region_labels).
    """
    import torch

    # Group blocks by region label and compute per-region confidence
    region_confs: dict[str, list[float]] = {}
    for b in blocks:
        label = b.get("region_label", "unknown")
        region_confs.setdefault(label, []).append(b["prob"])

    reprocessed = []
    new_blocks = []

    for region in regions:
        label = region.get("label", "unknown")
        confs = region_confs.get(label, [])
        avg_conf = float(np.mean(confs)) if confs else 0.0

        if avg_conf >= _LOW_CONF_THRESHOLD and len(confs) > 0:
            # Region is fine — keep existing blocks
            new_blocks.extend([b for b in blocks if b.get("region_label") == label])
            continue

        # Low confidence or no blocks — reprocess this region with CLAHE
        x, y, w, h = region["x"], region["y"], region["w"], region["h"]
        crop = img[y:y+h, x:x+w]
        if crop.size == 0:
            new_blocks.extend([b for b in blocks if b.get("region_label") == label])
            continue

        try:
            gray_crop = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY) if len(crop.shape) == 3 else crop
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray_crop)
            enhanced_bgr = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)

            with torch.no_grad():
                results = reader.readtext(
                    enhanced_bgr,
                    canvas_size=min(_CANVAS_SIZE, max(w, h) + 100),
                    detail=1,
                    text_threshold=0.6,
                    low_text=0.35,
                    width_ths=0.7,
                    workers=0,
                )

            enhanced_blocks = []
            for bbox, text, prob in results:
                text_clean = text.strip()
                if not text_clean or prob < 0.15:
                    continue
                remapped_bbox = [[pt[0] + x, pt[1] + y] for pt in bbox]
                xs_r = [pt[0] for pt in remapped_bbox]
                ys_r = [pt[1] for pt in remapped_bbox]
                min_xr, max_xr = min(xs_r), max(xs_r)
                min_yr, max_yr = min(ys_r), max(ys_r)
                enhanced_blocks.append({
                    "text": text_clean, "prob": float(prob),
                    "bbox": remapped_bbox,
                    "cy": (min_yr + max_yr) / 2.0,
                    "cx": (min_xr + max_xr) / 2.0,
                    "min_y": min_yr, "max_y": max_yr,
                    "min_x": min_xr, "max_x": max_xr,
                    "mode": "region_clahe",
                    "region_label": label,
                })

            # Use enhanced result only if it's actually better
            enhanced_avg = float(np.mean([b["prob"] for b in enhanced_blocks])) if enhanced_blocks else 0.0
            if enhanced_avg > avg_conf or (not confs and enhanced_blocks):
                new_blocks.extend(enhanced_blocks)
                reprocessed.append(label)
            else:
                new_blocks.extend([b for b in blocks if b.get("region_label") == label])

        except Exception as exc:
            logger.debug(f"Selective reprocess error for region {label}: {exc}")
            new_blocks.extend([b for b in blocks if b.get("region_label") == label])

    # Include any blocks that don't belong to a classified region
    classified_labels = {r.get("label") for r in regions}
    orphan_blocks = [b for b in blocks if b.get("region_label", "unknown") not in classified_labels]
    new_blocks.extend(orphan_blocks)

    return new_blocks, reprocessed


def _compute_ocr_quality_score(blocks: list[dict], fields: dict,
                               reprocessed: list[str], method: str) -> dict:
    """Compute a quality score indicating overall OCR result quality."""
    # Block count score (0-25)
    block_score = min(25, len(blocks) * 3)

    # Confidence score (0-35)
    avg_conf = float(np.mean([b["prob"] for b in blocks])) if blocks else 0.0
    conf_score = avg_conf * 35

    # Field extraction score (0-40): count how many critical fields were found
    critical_fields = ["mrp", "net_quantity", "manufacturer", "manufacturing_date",
                       "product_name", "consumer_care"]
    fields_found = 0
    for f in critical_fields:
        val = fields.get(f, {})
        if isinstance(val, dict) and val.get("value"):
            fields_found += 1
        elif val and not isinstance(val, dict):
            fields_found += 1
    field_score = (fields_found / len(critical_fields)) * 40

    total = round(block_score + conf_score + field_score, 1)

    # Grade
    if total >= 85:
        grade = "EXCELLENT"
    elif total >= 70:
        grade = "GOOD"
    elif total >= 50:
        grade = "FAIR"
    else:
        grade = "POOR"

    return {
        "score": total,
        "grade": grade,
        "avg_confidence": round(avg_conf, 3),
        "blocks_detected": len(blocks),
        "fields_extracted": fields_found,
        "fields_total": len(critical_fields),
        "reprocessed_regions": reprocessed,
        "method": method,
    }




def is_ocr_ready() -> bool:
    """Return True only if EasyOCR reader is instantiated and ready."""
    global _easyocr_reader, _ocr_ready
    return _easyocr_reader is not None and _ocr_ready is True


def get_easyocr_reader():
    """Return the singleton EasyOCR Reader, initialising it if necessary."""
    global _easyocr_reader, _ocr_ready, _easyocr_init_error
    if _easyocr_reader is not None and _ocr_ready:
        return _easyocr_reader

    with _easyocr_lock:
        if _easyocr_reader is not None and _ocr_ready:
            return _easyocr_reader

        if _easyocr_init_error is not None:
            logger.error(f"EasyOCR reader cannot be retrieved due to prior startup error: {_easyocr_init_error}")
            return None

        t0 = time.perf_counter()
        logger.info("EASYOCR INIT START")
        logger.info(f"EASYOCR MODEL DIR: {MODEL_DIR}")
        try:
            import easyocr
            import torch
            with torch.no_grad():
                reader = easyocr.Reader(
                    ['en'],
                    gpu=settings.OCR_USE_GPU,
                    verbose=False,
                    quantize=True,
                    model_storage_directory=MODEL_DIR,
                    user_network_directory=MODEL_DIR,
                    download_enabled=True,
                )
            gc.collect()
            _easyocr_reader = reader
            _ocr_ready = True
            _easyocr_init_error = None
            duration = time.perf_counter() - t0
            logger.info(f"EASYOCR INIT COMPLETE | duration={duration:.2f}s")
            logger.info("EASYOCR READER READY")
        except Exception as e:
            err_msg = str(e)
            logger.error(f"EASYOCR INIT FAILED | error={err_msg}", exc_info=True)
            _easyocr_reader = None
            _ocr_ready = False
            _easyocr_init_error = err_msg
            return None

    return _easyocr_reader


# ──────────────────────────────────────────────
# Image Preprocessing
# ──────────────────────────────────────────────
def preprocess_image_fast(image_path: str,
                           target_max_dim: int = _TARGET_MAX_DIM
                           ) -> tuple[np.ndarray, float]:
    """Read and downscale image while preserving aspect ratio.
    Returns the resized image and the scale factor applied.
    """
    # Existing implementation unchanged – kept for compatibility
    """
    Read image and resize (downscale only) to target_max_dim while keeping
    aspect ratio. Supports JPG, PNG, WEBP, BMP via OpenCV + PIL fallback.
    Returns (optimised_image, scale_factor).
    Raises ValueError("Unable to decode uploaded image") if decoding fails.
    """
    if not os.path.exists(image_path):
        raise ValueError("Unable to decode uploaded image")

    img = cv2.imread(image_path)
    if img is None:
        try:
            from PIL import Image
            with Image.open(image_path) as pil_img:
                pil_img = pil_img.convert("RGB")
                img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        except Exception as err:
            logger.error(f"PIL fallback failed to read image {image_path}: {err}")
            img = None

    if img is None or img.size == 0 or len(img.shape) < 2:
        raise ValueError("Unable to decode uploaded image")

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
# Block / Line Parsing (unchanged)
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
def _run_fullimage_ocr(reader, img_opt: np.ndarray) -> tuple[list[dict], float, float]:
    """
    Original full-image OCR pipeline (preserved for fallback).
    Returns (blocks, avg_confidence, inference_seconds).
    """
    import torch
    t0 = time.time()
    try:
        with torch.no_grad():
            results = reader.readtext(
                img_opt,
                canvas_size=_CANVAS_SIZE,
                detail=1,
                text_threshold=0.6,
                low_text=0.35,
                width_ths=0.7,
                workers=0,
            )
    except Exception as err:
        logger.error(f"EasyOCR full-image error: {err}")
        results = []
    inf_sec = time.time() - t0

    blocks = parse_easyocr_blocks(results, mode="standard")
    avg_conf = float(np.mean([b["prob"] for b in blocks])) if blocks else 0.0
    return blocks, avg_conf, inf_sec


def run_ocr_with_metrics(image_path: str) -> tuple[str, float, dict]:
    """
    Region-aware OCR pipeline with automatic fallback to full-image OCR.

    Returns (full_text, avg_confidence, metrics_dict).

    Timing metrics (all in seconds):
        image_read_sec       – imread + resize
        model_init_sec       – first-call model load (0 on warm subsequent calls)
        region_detection_sec – OpenCV region detection time
        ocr_inference_sec    – readtext() wall time (region or full-image)
        reprocess_sec        – confidence-based selective reprocessing time
        ocr_postproc_sec     – block merge + line reconstruction
        extraction_sec       – structured field extraction time
        total_sec            – wall-clock total for the entire pipeline
        num_regions          – how many text regions were detected
        num_passes           – 1 or 2 (for backward compat)
        method               – "region" or "fullimage"
        ocr_quality          – quality score dict
    """
    t_total_start = time.time()
    metrics: dict = {}

    # ── 1. Image read + preprocess ────────────────────────────────────────
    t0 = time.time()
    img_opt, _scale = preprocess_image_fast(image_path, target_max_dim=_TARGET_MAX_DIM)
    metrics["image_read_sec"] = round(time.time() - t0, 4)

    # ── 2. Model access (singleton) ───────────────────────────────────────
    t0 = time.time()
    reader = get_easyocr_reader()
    metrics["model_init_sec"] = round(time.time() - t0, 4)

    if not reader:
        logger.error("EasyOCR reader unavailable — returning empty OCR result.")
        metrics.update({
            "ocr_inference_sec": 0.0, "ocr_postproc_sec": 0.0,
            "num_passes": 0, "region_detection_sec": 0.0,
            "reprocess_sec": 0.0, "extraction_sec": 0.0,
            "total_sec": 0.0, "num_regions": 0, "method": "none",
        })
        return "", 0.0, metrics

    h, w = img_opt.shape[:2]
    img_area = h * w
    use_regions = (
        _REGION_AWARE
        and img_area >= _MIN_IMAGE_AREA_FOR_REGIONS
    )

    # ── 3. Region detection (lightweight OpenCV) ──────────────────────────
    regions = []
    if use_regions:
        t0 = time.time()
        raw_regions = _detect_text_regions(img_opt)
        merged_regions = _merge_nearby_regions(raw_regions)
        # Pad regions for OCR margin
        regions = [_pad_region(r, h, w) for r in merged_regions]
        metrics["region_detection_sec"] = round(time.time() - t0, 4)

        # Check if region detection found enough distinct regions to be beneficial
        # If regions cover >90% of image area, full-image OCR is likely faster
        total_region_area = sum(r["w"] * r["h"] for r in regions)
        region_coverage = total_region_area / img_area if img_area > 0 else 1.0

        if len(regions) < _MIN_REGIONS_FOR_BENEFIT or region_coverage > 0.90:
            logger.info(
                f"Region detection: {len(regions)} regions, coverage={region_coverage:.1%} "
                f"→ falling back to full-image OCR (insufficient benefit)"
            )
            use_regions = False
            regions = []
    else:
        metrics["region_detection_sec"] = 0.0

    # ── 4. OCR execution ──────────────────────────────────────────────────
    reprocessed_regions: list[str] = []
    reprocess_sec = 0.0

    if use_regions and regions:
        # ── 4a. Region-based OCR ──────────────────────────────────────────
        logger.info(f"Region-aware OCR: {len(regions)} text regions detected")
        for i, r in enumerate(regions):
            logger.info(f"  Region {i}: label={r['label']} pos=({r['x']},{r['y']}) size={r['w']}x{r['h']}")

        t0 = time.time()
        blocks_region = _run_region_ocr(reader, img_opt, regions)
        region_ocr_sec = time.time() - t0
        avg_conf_region = float(np.mean([b["prob"] for b in blocks_region])) if blocks_region else 0.0

        # Quick field extraction check on region results
        temp_lines_r = reconstruct_2d_lines(blocks_region)
        temp_text_r = "\n".join(temp_lines_r)
        temp_fields_r = extract_structured_fields(temp_text_r)

        # Count critical fields found
        critical_keys = ["mrp", "net_quantity", "manufacturer", "manufacturing_date"]
        region_fields_found = sum(
            1 for k in critical_keys
            if isinstance(temp_fields_r.get(k), dict) and temp_fields_r[k].get("value")
        )

        # ── 4a.1 Selective reprocessing on low-confidence regions ─────────
        if settings.OCR_ENABLE_FALLBACK and avg_conf_region < _FALLBACK_CONF:
            t0_rp = time.time()
            blocks_region, reprocessed_regions = _selective_reprocess(
                reader, img_opt, blocks_region, regions
            )
            reprocess_sec = time.time() - t0_rp
            if reprocessed_regions:
                logger.info(f"Selective reprocessing: enhanced {reprocessed_regions}")

        # ── 4a.2 Fallback safety: compare region vs full-image ────────────
        # If region-OCR found very few blocks or missed critical fields,
        # run full-image OCR and pick the better result
        if len(blocks_region) < _FALLBACK_MIN_BLOCKS or region_fields_found < 2:
            logger.info(
                f"Region OCR produced {len(blocks_region)} blocks, "
                f"{region_fields_found} fields → running full-image fallback for comparison"
            )
            blocks_full, avg_conf_full, inf_full_sec = _run_fullimage_ocr(reader, img_opt)
            temp_lines_f = reconstruct_2d_lines(blocks_full)
            temp_text_f = "\n".join(temp_lines_f)
            temp_fields_f = extract_structured_fields(temp_text_f)
            full_fields_found = sum(
                1 for k in critical_keys
                if isinstance(temp_fields_f.get(k), dict) and temp_fields_f[k].get("value")
            )

            # Use whichever result extracted more critical fields (accuracy > speed)
            if full_fields_found > region_fields_found or (
                full_fields_found == region_fields_found and avg_conf_full > avg_conf_region
            ):
                logger.info(
                    f"Full-image OCR better: {full_fields_found} fields vs {region_fields_found} "
                    f"→ using full-image result"
                )
                blocks = blocks_full
                metrics["ocr_inference_sec"] = round(region_ocr_sec + reprocess_sec + inf_full_sec, 4)
                metrics["method"] = "fullimage_fallback"
                metrics["num_regions"] = len(regions)
            else:
                blocks = blocks_region
                metrics["ocr_inference_sec"] = round(region_ocr_sec + reprocess_sec, 4)
                metrics["method"] = "region"
                metrics["num_regions"] = len(regions)
        else:
            blocks = blocks_region
            metrics["ocr_inference_sec"] = round(region_ocr_sec + reprocess_sec, 4)
            metrics["method"] = "region"
            metrics["num_regions"] = len(regions)

    else:
        # ── 4b. Full-image OCR (original pipeline) ────────────────────────
        blocks_p1, avg_conf_p1, inf1_sec = _run_fullimage_ocr(reader, img_opt)

        # Quick field extraction check
        temp_lines = reconstruct_2d_lines(blocks_p1)
        temp_text = "\n".join(temp_lines)
        preliminary_fields = extract_structured_fields(temp_text)

        mrp_found = bool(preliminary_fields.get("mrp", {}).get("value"))
        net_qty_found = bool(preliminary_fields.get("net_quantity", {}).get("value"))
        mfr_found = bool(preliminary_fields.get("manufacturer", {}).get("value"))
        important_fields_found = (mrp_found and net_qty_found) or (mrp_found and mfr_found)

        # CLAHE fallback (existing logic, unchanged)
        need_pass2 = (
            settings.OCR_ENABLE_FALLBACK
            and not important_fields_found
            and (avg_conf_p1 < _FALLBACK_CONF or len(blocks_p1) < _FALLBACK_MIN_BLOCKS)
        )
        inf2_sec = 0.0
        blocks_p2: list[dict] = []

        if need_pass2:
            logger.info(
                f"Pass-1 conf={avg_conf_p1:.2f}, blocks={len(blocks_p1)}, "
                f"fields_found={important_fields_found} → running CLAHE fallback pass."
            )
            t0 = time.time()
            try:
                gray = cv2.cvtColor(img_opt, cv2.COLOR_BGR2GRAY)
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                enhanced = clahe.apply(gray)
                enhanced_bgr = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)
                import torch
                with torch.no_grad():
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

        blocks = blocks_p1 + blocks_p2
        metrics["ocr_inference_sec"] = round(inf1_sec + inf2_sec, 4)
        metrics["method"] = "fullimage"
        metrics["num_regions"] = 0

    metrics["reprocess_sec"] = round(reprocess_sec, 4)
    metrics["num_passes"] = 2 if reprocess_sec > 0 or metrics.get("method") == "fullimage_fallback" else 1

    # ── 5. Deduplicate blocks (important when merging region results) ─────
    seen_keys: set[str] = set()
    deduped_blocks: list[dict] = []
    for b in blocks:
        dedup_key = f"{b['text'].lower().strip()}_{int(b['cy'] / 15)}_{int(b['cx'] / 15)}"
        if dedup_key not in seen_keys:
            seen_keys.add(dedup_key)
            deduped_blocks.append(b)
    blocks = deduped_blocks

    # ── 6. Merge blocks and reconstruct text ──────────────────────────────
    t0 = time.time()
    lines = reconstruct_2d_lines(blocks)
    full_text = "\n".join(lines)
    avg_conf = float(np.mean([b["prob"] for b in blocks])) if blocks else 0.70
    metrics["ocr_postproc_sec"] = round(time.time() - t0, 4)

    # ── 7. Field extraction + quality score ───────────────────────────────
    t0 = time.time()
    final_fields = extract_structured_fields(full_text)
    metrics["extraction_sec"] = round(time.time() - t0, 4)

    quality = _compute_ocr_quality_score(
        blocks, final_fields, reprocessed_regions, metrics.get("method", "unknown")
    )
    metrics["ocr_quality"] = quality
    metrics["regions_reprocessed"] = reprocessed_regions

    # ── 8. Total time ─────────────────────────────────────────────────────
    metrics["total_sec"] = round(time.time() - t_total_start, 4)

    logger.info(
        f"OCR done — method={metrics['method']}, regions={metrics['num_regions']}, "
        f"blocks={len(blocks)}, conf={avg_conf:.2f}, "
        f"inference={metrics['ocr_inference_sec']}s, total={metrics['total_sec']}s, "
        f"quality={quality['grade']}({quality['score']})"
    )

    # Run GC once at the end of the pipeline
    gc.collect()

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
    MRP_KWS  = {"MRP", "M.R.P.", "M.R.P", "RETAIL PRICE", "MAXIMUM RETAIL PRICE"}
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

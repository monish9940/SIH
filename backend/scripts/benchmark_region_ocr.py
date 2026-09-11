"""
Benchmark: Region-Aware OCR vs Full-Image OCR
Runs both pipelines on sample_label.jpg and compares:
  - Processing time (with full breakdown)
  - Extracted fields (accuracy comparison)
  - Quality scores
  - CPU/RAM usage
"""
import sys, io, os, time, tracemalloc

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, '.')

from app.services.ocr_service import (
    run_ocr_with_metrics, extract_structured_fields, get_easyocr_reader,
    preprocess_image_fast, _run_fullimage_ocr, parse_easyocr_blocks,
    reconstruct_2d_lines, _detect_text_regions, _merge_nearby_regions,
    _pad_region, _CANVAS_SIZE, _TARGET_MAX_DIM, _REGION_AWARE,
)
from app.config import settings

IMAGE = "sample_label.jpg"
NUM_RUNS = 3

if not os.path.exists(IMAGE):
    print(f"ERROR: {IMAGE} not found in {os.getcwd()}")
    sys.exit(1)

# ═══════════════════════════════════════════════════════════════════════════
# Pre-warm
# ═══════════════════════════════════════════════════════════════════════════
print("=" * 65)
print("BENCHMARK: Region-Aware OCR vs Full-Image OCR")
print(f"  Image           : {IMAGE}")
print(f"  canvas_size     : {_CANVAS_SIZE}")
print(f"  target_max_dim  : {_TARGET_MAX_DIM}")
print(f"  region_aware    : {_REGION_AWARE}")
print(f"  runs per mode   : {NUM_RUNS}")
print("=" * 65)

print("\nPre-warming EasyOCR singleton...")
t0 = time.time()
reader = get_easyocr_reader()
warmup = time.time() - t0
print(f"  Model warm-up: {warmup:.2f}s")
if not reader:
    print("ERROR: EasyOCR reader failed to initialize")
    sys.exit(1)

# ═══════════════════════════════════════════════════════════════════════════
# Part 1: Full-Image OCR (baseline)
# ═══════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 65)
print("PART 1: FULL-IMAGE OCR (baseline, OCR_REGION_AWARE=false)")
print("=" * 65)

# Temporarily force full-image mode
import app.services.ocr_service as ocr_mod
original_region_aware = ocr_mod._REGION_AWARE
ocr_mod._REGION_AWARE = False

fullimage_results = []
for run in range(1, NUM_RUNS + 1):
    tracemalloc.start()
    t_start = time.time()
    raw_text, conf, metrics = run_ocr_with_metrics(IMAGE)
    t_total = time.time() - t_start
    current_mem, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    fields = extract_structured_fields(raw_text)
    fullimage_results.append({
        "run": run, "raw_text": raw_text, "conf": conf,
        "metrics": metrics, "fields": fields,
        "total_sec": t_total,
        "peak_mem_mb": round(peak_mem / 1024 / 1024, 2),
    })

    print(f"\n  --- Run {run} ---")
    print(f"    Image read         : {metrics.get('image_read_sec', 0)}s")
    print(f"    Model init         : {metrics.get('model_init_sec', 0)}s")
    print(f"    Region detection   : {metrics.get('region_detection_sec', 0)}s")
    print(f"    OCR inference      : {metrics.get('ocr_inference_sec', 0)}s")
    print(f"    Reprocessing       : {metrics.get('reprocess_sec', 0)}s")
    print(f"    Post-process       : {metrics.get('ocr_postproc_sec', 0)}s")
    print(f"    Field extraction   : {metrics.get('extraction_sec', 0)}s")
    print(f"    Method             : {metrics.get('method', 'N/A')}")
    print(f"    TOTAL              : {t_total:.3f}s")
    print(f"    Peak RAM           : {fullimage_results[-1]['peak_mem_mb']} MB")
    print(f"    Confidence         : {conf:.3f}")
    print(f"    MRP                : {fields.get('mrp_raw')}")
    print(f"    Net Qty            : {fields.get('net_quantity_raw')}")
    print(f"    Manufacturer       : {fields.get('manufacturer_raw')}")
    print(f"    MFG Date           : {fields.get('mfg_date_raw')}")
    print(f"    Consumer Care      : {fields.get('consumer_care_raw')}")
    print(f"    Product Name       : {fields.get('product_name_raw')}")
    quality = metrics.get('ocr_quality', {})
    if quality:
        print(f"    Quality            : {quality.get('grade', 'N/A')} ({quality.get('score', 0)})")

# ═══════════════════════════════════════════════════════════════════════════
# Part 2: Region-Aware OCR (optimized)
# ═══════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 65)
print("PART 2: REGION-AWARE OCR (optimized, OCR_REGION_AWARE=true)")
print("=" * 65)

ocr_mod._REGION_AWARE = True

region_results = []
for run in range(1, NUM_RUNS + 1):
    tracemalloc.start()
    t_start = time.time()
    raw_text, conf, metrics = run_ocr_with_metrics(IMAGE)
    t_total = time.time() - t_start
    current_mem, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    fields = extract_structured_fields(raw_text)
    region_results.append({
        "run": run, "raw_text": raw_text, "conf": conf,
        "metrics": metrics, "fields": fields,
        "total_sec": t_total,
        "peak_mem_mb": round(peak_mem / 1024 / 1024, 2),
    })

    print(f"\n  --- Run {run} ---")
    print(f"    Image read         : {metrics.get('image_read_sec', 0)}s")
    print(f"    Model init         : {metrics.get('model_init_sec', 0)}s")
    print(f"    Region detection   : {metrics.get('region_detection_sec', 0)}s")
    print(f"    Regions found      : {metrics.get('num_regions', 0)}")
    print(f"    OCR inference      : {metrics.get('ocr_inference_sec', 0)}s")
    print(f"    Reprocessing       : {metrics.get('reprocess_sec', 0)}s")
    print(f"    Post-process       : {metrics.get('ocr_postproc_sec', 0)}s")
    print(f"    Field extraction   : {metrics.get('extraction_sec', 0)}s")
    print(f"    Method             : {metrics.get('method', 'N/A')}")
    print(f"    TOTAL              : {t_total:.3f}s")
    print(f"    Peak RAM           : {region_results[-1]['peak_mem_mb']} MB")
    print(f"    Confidence         : {conf:.3f}")
    print(f"    MRP                : {fields.get('mrp_raw')}")
    print(f"    Net Qty            : {fields.get('net_quantity_raw')}")
    print(f"    Manufacturer       : {fields.get('manufacturer_raw')}")
    print(f"    MFG Date           : {fields.get('mfg_date_raw')}")
    print(f"    Consumer Care      : {fields.get('consumer_care_raw')}")
    print(f"    Product Name       : {fields.get('product_name_raw')}")
    quality = metrics.get('ocr_quality', {})
    if quality:
        print(f"    Quality            : {quality.get('grade', 'N/A')} ({quality.get('score', 0)})")
    reprocessed = metrics.get('regions_reprocessed', [])
    if reprocessed:
        print(f"    Reprocessed regions : {reprocessed}")

# Restore
ocr_mod._REGION_AWARE = original_region_aware

# ═══════════════════════════════════════════════════════════════════════════
# Part 3: Comparison Summary
# ═══════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 65)
print("COMPARISON SUMMARY")
print("=" * 65)

avg_full_time = sum(r["total_sec"] for r in fullimage_results) / NUM_RUNS
avg_region_time = sum(r["total_sec"] for r in region_results) / NUM_RUNS
avg_full_inf = sum(r["metrics"]["ocr_inference_sec"] for r in fullimage_results) / NUM_RUNS
avg_region_inf = sum(r["metrics"]["ocr_inference_sec"] for r in region_results) / NUM_RUNS
avg_full_mem = sum(r["peak_mem_mb"] for r in fullimage_results) / NUM_RUNS
avg_region_mem = sum(r["peak_mem_mb"] for r in region_results) / NUM_RUNS

speedup = (avg_full_time - avg_region_time) / avg_full_time * 100 if avg_full_time > 0 else 0

# Field accuracy comparison
EXPECTED_FIELDS = {
    "mrp_raw": "₹ 525",
    "net_quantity_raw": "5.0 kg",
    "manufacturer_raw": "Apex Foods Pvt. Ltd.",
    "mfg_date_raw": "12/01/2026",
    "product_name_raw": "Kama Foods Premium Basmati Rice",
}

def count_correct(result_list, expected):
    correct = 0
    total = len(expected)
    for key, exp_val in expected.items():
        vals = [r["fields"].get(key) for r in result_list]
        # Count as correct if majority of runs match
        from collections import Counter
        most_common = Counter(vals).most_common(1)
        if most_common and most_common[0][0] == exp_val:
            correct += 1
    return correct, total

full_correct, full_total = count_correct(fullimage_results, EXPECTED_FIELDS)
region_correct, region_total = count_correct(region_results, EXPECTED_FIELDS)

print(f"\n  {'Metric':<30} {'Full-Image':>14} {'Region-Aware':>14}")
print(f"  {'-'*58}")
print(f"  {'Avg total time':<30} {avg_full_time:>13.3f}s {avg_region_time:>13.3f}s")
print(f"  {'Avg OCR inference':<30} {avg_full_inf:>13.3f}s {avg_region_inf:>13.3f}s")
print(f"  {'Avg peak RAM':<30} {avg_full_mem:>12.2f}MB {avg_region_mem:>12.2f}MB")
print(f"  {'Fields correct':<30} {full_correct:>10}/{full_total} {region_correct:>10}/{region_total}")
print(f"  {'Speed improvement':<30} {'baseline':>14} {f'{speedup:+.1f}%':>14}")

# Per-field comparison
print(f"\n  {'Field':<25} {'Full-Image':>20} {'Region-Aware':>20} {'Match':>8}")
print(f"  {'-'*75}")
for key, exp in EXPECTED_FIELDS.items():
    full_val = fullimage_results[-1]["fields"].get(key)
    region_val = region_results[-1]["fields"].get(key)
    match = "✓" if full_val == region_val == exp else ("~" if region_val == exp else "✗")
    label = key.replace("_raw", "").replace("_", " ").title()
    print(f"  {label:<25} {str(full_val):>20} {str(region_val):>20} {match:>8}")

# Quality comparison
full_quality = fullimage_results[-1]["metrics"].get("ocr_quality", {})
region_quality = region_results[-1]["metrics"].get("ocr_quality", {})
if full_quality and region_quality:
    print(f"\n  {'Quality Score':<30} {full_quality.get('score', 'N/A'):>14} {region_quality.get('score', 'N/A'):>14}")
    print(f"  {'Quality Grade':<30} {full_quality.get('grade', 'N/A'):>14} {region_quality.get('grade', 'N/A'):>14}")

print(f"\n{'='*65}")
print("BENCHMARK COMPLETE")
print(f"{'='*65}")

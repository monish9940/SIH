import time, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, '.')
from app.services.ocr_service import run_ocr_with_metrics, extract_structured_fields, get_easyocr_reader

print("=== Pre-warming OCR model ===")
t0 = time.time()
get_easyocr_reader()
print(f"Model warm-up: {time.time()-t0:.2f}s")

IMAGE = "sample_label.jpg"
print()
print(f"=== Running 3 passes on {IMAGE} ===")
for run in range(1, 4):
    t0 = time.time()
    raw_text, conf, metrics = run_ocr_with_metrics(IMAGE)
    t_ocr = time.time() - t0

    t1 = time.time()
    fields = extract_structured_fields(raw_text)
    t_ext = time.time() - t1

    print(f"--- Run {run} ---")
    print(f"  Image read    : {metrics['image_read_sec']}s")
    print(f"  Model init    : {metrics['model_init_sec']}s")
    print(f"  OCR inference : {metrics['ocr_inference_sec']}s  (passes={metrics['num_passes']})")
    print(f"  Post-process  : {metrics['ocr_postproc_sec']}s")
    print(f"  Field extract : {round(t_ext,4)}s")
    print(f"  TOTAL         : {round(t_ocr+t_ext,2)}s")
    print(f"  avg_conf      : {conf:.2f}")
    print(f"  MRP           : {fields['mrp_raw']}")
    print(f"  Net Qty       : {fields['net_quantity_raw']}")
    print(f"  Manufacturer  : {fields['manufacturer_raw']}")
    print(f"  MFG Date      : {fields['mfg_date_raw']}")
    print()

import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, '.')
from app.services.ocr_service import run_ocr_with_metrics, extract_structured_fields, get_easyocr_reader

print("=== Pre-warming OCR model ===")
get_easyocr_reader()

IMAGE = "sample_label.jpg"
raw_text, conf, metrics = run_ocr_with_metrics(IMAGE)

print("=== Raw OCR Text ===")
print(raw_text)
print()
print("=== Extracted Fields ===")
fields = extract_structured_fields(raw_text)
for k, v in fields.items():
    if not k.endswith("_raw"):
        print(f"  {k}: {v}")

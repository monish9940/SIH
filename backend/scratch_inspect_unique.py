import sys
import os
from PIL import Image

sys.path.insert(0, '.')
from app.services.ocr_service import run_ocr_with_metrics, extract_structured_fields
from app.services.compliance_engine import evaluate_compliance

unique_paths = [
    'e:/sih/backend/uploads/INSP-2026-09826A48.jpg',
    'e:/sih/backend/uploads/INSP-2026-0E5FF586.webp',
    'e:/sih/backend/uploads/INSP-2026-12B7CBD7.jpg',
    'e:/sih/backend/uploads/INSP-2026-1D16888A.jpg',
    'e:/sih/backend/uploads/INSP-2026-5C7EFFC0.jpg',
    'e:/sih/backend/uploads/INSP-2026-61DBFB75.jpeg',
    'e:/sih/backend/uploads/INSP-2026-C9491885.jpeg'
]

for p in unique_paths:
    print('='*70)
    print(f"Path: {p}")
    if not os.path.exists(p):
        print("File does not exist.")
        continue
    im = Image.open(p)
    print(f"Dimensions: {im.size}, Format: {im.format}, Mode: {im.mode}")
    
    ocr_res = run_ocr_with_metrics(p)
    print(f"OCR Method: {ocr_res['ocr_method']}")
    print(f"Fallback Triggered: {ocr_res['fallback_triggered']}")
    print(f"OCR Inference Time: {ocr_res['ocr_inference_time_ms']} ms")
    print(f"Total Analysis Time: {ocr_res['total_ocr_time_ms']} ms")
    print(f"Quality Score: {ocr_res['quality_score']} ({ocr_res['quality_label']})")
    print(f"Raw Text Snippet: {repr(ocr_res['raw_text'][:200])}")
    
    fields = extract_structured_fields(ocr_res['raw_text'], ocr_res['text_blocks'])
    print(f"Extracted Fields:")
    print(f"  - Product Name: {fields.get('product_name_raw')}")
    print(f"  - MRP: {fields.get('mrp_raw')}")
    print(f"  - Net Qty: {fields.get('net_quantity_raw')}")
    print(f"  - Mfr: {fields.get('manufacturer_raw')}")
    print(f"  - Date: {fields.get('manufacture_date_raw')}")
    
    comp = evaluate_compliance(fields, ocr_res)
    print(f"Compliance Status: {comp.get('status')}")
    print(f"Pass count: {comp.get('pass_count')}, Fail count: {comp.get('fail_count')}, Needs review: {comp.get('needs_review_count')}")
    for r in comp.get('rules', []):
        print(f"  * {r['rule_id']} ({r['rule_name']}): {r['status']} - {r['reason']}")

import sys
import os
import time
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, '.')
from app.services.ocr_service import run_ocr_with_metrics, extract_structured_fields
from app.services.compliance_engine import evaluate_compliance

test_scenarios = [
    (
        "1. Large clear product label",
        "e:/sih/backend/uploads/INSP-2026-5C7EFFC0.jpg"
    ),
    (
        "2. Label containing logos/barcodes/non-text areas",
        "e:/sih/backend/uploads/INSP-2026-12B7CBD7.jpg"
    ),
    (
        "3. Low-quality or blurry label",
        "e:/sih/backend/uploads/INSP-2026-0E5FF586.webp"
    ),
    (
        "4. Label with MRP and Net Quantity",
        "e:/sih/backend/uploads/INSP-2026-61DBFB75.jpeg"
    ),
    (
        "5. Label with missing MRP",
        "e:/sih/backend/uploads/test_missing_mrp.jpg"
    ),
    (
        "6. Label with missing Net Quantity",
        "e:/sih/backend/uploads/test_missing_net_qty.jpg"
    )
]

print("=" * 80)
print("             FINAL REAL-WORLD OCR & COMPLIANCE VALIDATION REPORT")
print("=" * 80)
print()

for name, p in test_scenarios:
    print("-" * 80)
    print(f"TEST SCENARIO: {name}")
    print(f"File: {os.path.basename(p)}")
    
    if not os.path.exists(p):
        print("  STATUS: FILE NOT FOUND")
        continue

    im = Image.open(p)
    file_size_kb = os.path.getsize(p) / 1024.0
    print(f"Image Spec: {im.size[0]}x{im.size[1]} px | Format: {im.format} | Size: {file_size_kb:.1f} KB")

    t_start = time.time()
    raw_text, ocr_conf, metrics = run_ocr_with_metrics(p)
    t_total = time.time() - t_start

    extracted = extract_structured_fields(raw_text, os.path.basename(p))
    comp = evaluate_compliance(extracted)

    def get_field(k):
        val = extracted.get(k)
        if isinstance(val, dict):
            return val.get('value')
        return val

    mrp = get_field('mrp') or get_field('mrp_raw')
    net_qty = get_field('net_quantity') or get_field('net_quantity_raw')
    mfr = get_field('manufacturer') or get_field('manufacturer_raw')
    mfg_date = get_field('manufacturing_date') or get_field('mfg_date_raw')

    fallback_triggered = (metrics.get('method') == 'fullimage_fallback') or (metrics.get('num_passes', 1) > 1)

    print(f"- OCR method used:      {metrics.get('method')}")
    print(f"- OCR inference time:  {metrics.get('ocr_inference_sec', 0)*1000:.2f} ms")
    print(f"- Total analysis time: {t_total*1000:.2f} ms")
    print(f"- MRP extracted:       {mrp}")
    print(f"- Net Quantity:        {net_qty}")
    print(f"- Manufacturer:        {mfr}")
    print(f"- Date extracted:      {mfg_date}")
    print(f"- Fallback triggered:  {fallback_triggered}")
    print(f"- Compliance result:   {comp.get('status')} (Score: {comp.get('score')})")

    # Specific compliance rule check prints
    for check in comp.get('checks', []):
        rid = check['rule_id']
        st = check['status']
        exp = check.get('explanation', '')
        if rid in ['RULE_6_1_A', 'RULE_6_1_C', 'RULE_6_1_E', 'RULE_6_1_N', 'RULE_6_1_D', 'RULE_7', 'RULE_11']:
            print(f"    * [{st}] {rid}: {exp}")
    print()

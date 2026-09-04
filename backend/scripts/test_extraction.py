"""
Unit tests for extract_structured_fields() — runs in milliseconds, no OCR needed.
Tests the exact field extraction logic against known OCR text samples.
"""
import sys
sys.path.insert(0, '.')
from app.services.ocr_service import extract_structured_fields

PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"

def check(label, got, expected):
    ok = (got == expected)  # works for None==None too
    status = PASS if ok else FAIL
    print(f"  [{status}] {label}: got={got!r}  expected={expected!r}")
    return ok

results = []

# ─────────────────────────────────────────────────────────────────────
# TEST 1: Sample label (MFG DATE on line after MRP should not bleed)
# ─────────────────────────────────────────────────────────────────────
print("\n=== TEST 1: Sample Label (MRP + MFG DATE adjacency) ===")
t1_text = """POTATO CHIPS PACKET
CRISP CHIPS
NET QTY: 50 G
MRP: RS. 20.00 INCL TAXES
MFG DATE: 01/2026
MFD BY: QUALITY PACKAGERS PVT LTD"""

f = extract_structured_fields(t1_text)
results.append(check("MRP",          f["mrp_raw"],          "₹ 20"))
results.append(check("Net Qty",      f["net_quantity_raw"], "50 g"))
results.append(check("Manufacturer", f["manufacturer_raw"], "Quality Packagers Pvt Ltd"))
results.append(check("MFG Date",     f["mfg_date_raw"],     "01/2026"))

# ─────────────────────────────────────────────────────────────────────
# TEST 2: Lay's-style label (MRP on one line, price on NEXT line)
# ─────────────────────────────────────────────────────────────────────
print("\n=== TEST 2: Lay's-Style Label (price on next line) ===")
t2_text = """LAY'S POTATO CHIPS
PepsiCo India Holdings Pvt. Ltd.
Net Qty: 80 g
MRP (INCL. OF ALL TAXES)
Rs. 48/-
Consumer Care: 1800 123 4567
Mfg Date: 08/2026
Best Before: 08/2027"""

f = extract_structured_fields(t2_text)
results.append(check("Product",      f["product_name_raw"], "Lay's Potato Chips"))
results.append(check("MRP",          f["mrp_raw"],          "₹ 48"))
results.append(check("Net Qty",      f["net_quantity_raw"], "80 g"))
results.append(check("Manufacturer", f["manufacturer_raw"], "PepsiCo India Holdings Pvt. Ltd."))

# ─────────────────────────────────────────────────────────────────────
# TEST 3: Nutritional table should NOT produce net qty
# ─────────────────────────────────────────────────────────────────────
print("\n=== TEST 3: Nutritional Numbers Should NOT match Net Qty ===")
t3_text = """BRITANNIA BISCUITS
Net Weight: 100 g
Nutrition Info (per 100g): Energy 430 kcal, Protein 8 g
MRP: Rs. 35
MFG: 03/2026
Batch: B123"""

f = extract_structured_fields(t3_text)
results.append(check("Net Qty is 100g", f["net_quantity_raw"], "100 g"))
results.append(check("MRP",              f["mrp_raw"],          "₹ 35"))
results.append(check("Batch",           f["batch_number"]["value"], "B123"))

# ─────────────────────────────────────────────────────────────────────
# TEST 4: MRP on same line as RS and taxes
# ─────────────────────────────────────────────────────────────────────
print("\n=== TEST 4: All on one line ===")
t4_text = """KURKURE MASALA MUNCH
Manufactured by: PepsiCo India
Net Qty: 65 g
MRP Rs. 20/- (Incl. of all taxes)
Best Before: SEP/2026"""

f = extract_structured_fields(t4_text)
results.append(check("Product",  f["product_name_raw"], "Kurkure Snacks"))
results.append(check("MRP",      f["mrp_raw"],          "₹ 20"))
results.append(check("Net Qty",  f["net_quantity_raw"], "65 g"))
results.append(check("Exp Date", f["expiry_date"]["value"], "SEP/2026"))

# ─────────────────────────────────────────────────────────────────────
# TEST 5: No MRP keyword — should return None (NEEDS_REVIEW)
# ─────────────────────────────────────────────────────────────────────
print("\n=== TEST 5: Missing MRP Keyword → None ===")
t5_text = """SNACK PRODUCT
Net Qty: 30 g
Made in India"""

f = extract_structured_fields(t5_text)
results.append(check("MRP is None", f["mrp_raw"], None))
results.append(check("Origin",      f["country_of_origin_raw"], "India"))

# ─────────────────────────────────────────────────────────────────────
# TEST 6: High MRP (₹999) — should still be extracted
# ─────────────────────────────────────────────────────────────────────
print("\n=== TEST 6: High MRP ===")
t6_text = """AMUL GHEE 1 KG
Net Qty: 1 kg
MRP: Rs. 620/- Incl. Taxes
Mfg: 01/2026  Exp: 12/2026"""

f = extract_structured_fields(t6_text)
results.append(check("Product", f["product_name_raw"], "Amul Dairy Product"))
results.append(check("MRP",     f["mrp_raw"],          "₹ 620"))
results.append(check("Net Qty", f["net_quantity_raw"], "1 kg"))

# ─────────────────────────────────────────────────────────────────────
print(f"\n{'='*50}")
passed = sum(1 for r in results if r)
total  = len(results)
print(f"RESULT: {passed}/{total} tests passed")
if passed == total:
    print("ALL TESTS PASSED ✓")
else:
    print(f"FAILED: {total - passed} test(s) need attention")

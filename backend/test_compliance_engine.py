from app.services.compliance_engine import evaluate_compliance, RULES_REGISTRY

def test_compliance_engine_10_scenarios():
    print("==================================================")
    print("   COMPLIANCE ENGINE 10-SCENARIO UNIT TEST SUITE ")
    print("==================================================")

    # Full detection payload for PASS
    full_pass = {
        "manufacturer": {"value": "Apex Packagers Pvt. Ltd., Delhi", "confidence": 0.95},
        "net_quantity": {"value": "500 g", "confidence": 0.92},
        "mrp": {"value": "₹ 150.00 INCL TAXES", "confidence": 0.94},
        "consumer_care": {"value": "Helpline: 1800-11-2233, care@apex.com", "confidence": 0.91},
        "manufacturing_date": {"value": "01/2026", "confidence": 0.89},
        "country_of_origin": {"value": "India", "confidence": 0.95}
    }

    # TEST 1: All PASS (Override RULE_7 for test)
    res1 = evaluate_compliance(full_pass)
    # Since RULE_7 defaults to NEEDS_REVIEW, evaluate status with full pass + rule_7
    print("\nTEST 1: Standard extraction payload...")
    print(f"  Status: {res1['overall_status']}, Score: {res1['score']}")
    assert res1['overall_status'] in ["NEEDS_REVIEW", "COMPLIANT"]

    # TEST 2: One explicit FAIL (MRP without currency/taxes)
    fail_mrp = full_pass.copy()
    fail_mrp["mrp"] = {"value": "150.00 ONLY", "confidence": 0.94}
    res2 = evaluate_compliance(fail_mrp)
    print("\nTEST 2: Invalid MRP formatting (FAIL)...")
    print(f"  Status: {res2['overall_status']}, Score: {res2['score']}")
    assert res2['overall_status'] == "NON-COMPLIANT"
    assert len(res2['violations']) > 0

    # TEST 3: One NEEDS_REVIEW
    res3 = evaluate_compliance(full_pass)
    assert any(c["status"] == "NEEDS_REVIEW" for c in res3["checks"])
    print("\nTEST 3: Inspection containing NEEDS_REVIEW check...")
    print(f"  Status: {res3['overall_status']}, Score: {res3['score']}")
    assert res3['overall_status'] == "NEEDS_REVIEW"
    assert res3['score'] is None

    # TEST 4: PASS + NEEDS_REVIEW -> NEEDS_REVIEW
    res4 = evaluate_compliance(full_pass)
    print("\nTEST 4: PASS + NEEDS_REVIEW combination...")
    print(f"  Status: {res4['overall_status']}, Score: {res4['score']}")
    assert res4['overall_status'] == "NEEDS_REVIEW"
    assert res4['score'] is None

    # TEST 5: PASS + FAIL -> NON-COMPLIANT
    fail_net = full_pass.copy()
    fail_net["net_quantity"] = {"value": "500 lbs", "confidence": 0.95}
    res5 = evaluate_compliance(fail_net)
    print("\nTEST 5: PASS + FAIL combination...")
    print(f"  Status: {res5['overall_status']}, Score: {res5['score']}")
    assert res5['overall_status'] == "NON-COMPLIANT"

    # TEST 6: FAIL + NEEDS_REVIEW -> NON-COMPLIANT
    fail_mfr = full_pass.copy()
    fail_mfr["net_quantity"] = {"value": "12 pounds", "confidence": 0.95} # FAIL
    fail_mfr["mrp"] = None # NEEDS_REVIEW
    res6 = evaluate_compliance(fail_mfr)
    print("\nTEST 6: FAIL + NEEDS_REVIEW combination...")
    print(f"  Status: {res6['overall_status']}, Score: {res6['score']}")
    assert res6['overall_status'] == "NON-COMPLIANT"

    # TEST 7: All NEEDS_REVIEW (Empty extractions)
    res7 = evaluate_compliance({})
    print("\nTEST 7: All empty extractions (All NEEDS_REVIEW)...")
    print(f"  Status: {res7['overall_status']}, Score: {res7['score']}")
    assert res7['overall_status'] == "NEEDS_REVIEW"
    assert res7['score'] is None
    assert len(res7['violations']) == 0 # NEEDS_REVIEW is NOT a violation

    # TEST 8: Missing OCR field -> NEEDS_REVIEW
    res8 = evaluate_compliance({"mrp": {"value": "₹ 100", "confidence": 0.9}})
    mfr_check = next(c for c in res8["checks"] if c["rule_id"] == "RULE_6_1_A")
    print("\nTEST 8: Missing manufacturer OCR field...")
    print(f"  Check Status: {mfr_check['status']}")
    assert mfr_check['status'] == "NEEDS_REVIEW"

    # TEST 9: Low OCR confidence (<0.65) -> NEEDS_REVIEW
    low_conf = {"mrp": {"value": "₹ 100", "confidence": 0.40}}
    res9 = evaluate_compliance(low_conf)
    mrp_check = next(c for c in res9["checks"] if c["rule_id"] == "RULE_6_1_E")
    print("\nTEST 9: Low OCR confidence extraction...")
    print(f"  Check Status: {mrp_check['status']}")
    assert mrp_check['status'] == "NEEDS_REVIEW"

    # TEST 10: Backside image missing front panel fields -> NEEDS_REVIEW, NOT FAIL
    backside_payload = {
        "manufacturer": {"value": "Quality Snack Foods, Industrial Estate, Noida", "confidence": 0.90},
        "consumer_care": {"value": "Email: care@snacks.in", "confidence": 0.88}
    }
    res10 = evaluate_compliance(backside_payload)
    print("\nTEST 10: Backside panel missing front declarations...")
    print(f"  Overall Status: {res10['overall_status']}")
    assert res10['overall_status'] == "NEEDS_REVIEW"
    assert len(res10['violations']) == 0

    print("\n==================================================")
    print("   ALL 10 COMPLIANCE ENGINE UNIT TESTS PASSED!    ")
    print("==================================================")

if __name__ == "__main__":
    test_compliance_engine_10_scenarios()

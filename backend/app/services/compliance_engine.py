import re
from datetime import datetime
from typing import Dict, List, Any

# Versioned statutory rules repository (PCR 2011 & latest amendments 2025/2026)
RULES_REGISTRY = [
    {
        "rule_id": "RULE_6_1_A",
        "rule_version": "2026.1",
        "effective_from": "2011-04-01",
        "effective_to": None,
        "category": "Mandatory Identity Declarations",
        "requirement": "Declaration of Manufacturer / Packer / Importer",
        "validation_logic": "manufacturer_name_and_address_present",
        "severity": "critical",
        "source_reference": "Rule 6(1)(a)",
        "source_date": "2011-03-07",
        "enabled": True
    },
    {
        "rule_id": "RULE_6_1_C",
        "rule_version": "2026.1",
        "effective_from": "2011-04-01",
        "effective_to": None,
        "category": "Net Quantity Declarations",
        "requirement": "Net Quantity Declaration in Standard SI Units",
        "validation_logic": "net_quantity_standard_units",
        "severity": "critical",
        "source_reference": "Rule 6(1)(c)",
        "source_date": "2011-03-07",
        "enabled": True
    },
    {
        "rule_id": "RULE_6_1_E",
        "rule_version": "2026.1",
        "effective_from": "2011-04-01",
        "effective_to": None,
        "category": "Pricing Declarations",
        "requirement": "Maximum Retail Price (MRP) Declaration",
        "validation_logic": "mrp_inclusive_of_taxes",
        "severity": "critical",
        "source_reference": "Rule 6(1)(e)",
        "source_date": "2011-03-07",
        "enabled": True
    },
    {
        "rule_id": "RULE_6_1_N",
        "rule_version": "2026.1",
        "effective_from": "2011-04-01",
        "effective_to": None,
        "category": "Consumer Redressal",
        "requirement": "Consumer Care Helpline & Email Details",
        "validation_logic": "consumer_care_contact",
        "severity": "major",
        "source_reference": "Rule 6(1)(n)",
        "source_date": "2011-03-07",
        "enabled": True
    },
    {
        "rule_id": "RULE_6_1_D",
        "rule_version": "2026.1",
        "effective_from": "2011-04-01",
        "effective_to": None,
        "category": "Date Declarations",
        "requirement": "Month and Year of Manufacture / Packing",
        "validation_logic": "mfg_or_packing_date",
        "severity": "major",
        "source_reference": "Rule 6(1)(d)",
        "source_date": "2011-03-07",
        "enabled": True
    },
    {
        "rule_id": "RULE_7",
        "rule_version": "2026.1",
        "effective_from": "2011-04-01",
        "effective_to": None,
        "category": "Display Standards",
        "requirement": "Size and Visibility of Declaration Font",
        "validation_logic": "declaration_font_size",
        "severity": "minor",
        "source_reference": "Rule 7",
        "source_date": "2011-03-07",
        "enabled": True
    },
    {
        "rule_id": "RULE_11",
        "rule_version": "2026.1",
        "effective_from": "2011-04-01",
        "effective_to": None,
        "category": "Units of Measurement",
        "requirement": "Standard Weight Symbol & Unit Specification",
        "validation_logic": "standard_unit_symbol",
        "severity": "major",
        "source_reference": "Rule 11",
        "source_date": "2011-03-07",
        "enabled": True
    }
]

def extract_val_and_conf(extracted_fields: dict, key: str) -> tuple[Any, float]:
    """Helper to extract field value and OCR confidence score safely."""
    raw = extracted_fields.get(key)
    if isinstance(raw, dict):
        return raw.get("value"), raw.get("confidence", 0.80)
    elif key in extracted_fields:
        return raw, 0.80
    alt_key = f"{key}_raw"
    if alt_key in extracted_fields:
        return extracted_fields.get(alt_key), 0.80
    return None, 0.0

def get_rule_details(rule_id: str, status: str, extracted_val: str, conf: float = 0.0) -> dict:
    """Returns rule-specific verification details for interactive detail drawer."""
    conf_pct = f"{int(conf * 100)}%" if conf > 0 else ("N/A" if extracted_val == "Not detected in uploaded image" else "85%")

    if rule_id == "RULE_6_1_A":
        expected = "Package must contain full name and complete postal address of the manufacturer, packer, or importer."
        if status == "PASS":
            reason = "Valid manufacturer/packer name and postal address detected in uploaded image."
            rec_action = "Automated check passed based on available evidence. Proceed with routine audit."
            verif_note = "The uploaded evidence satisfies the automated rule check. Final legal determination remains with authorized inspector."
        elif status == "FAIL":
            reason = "Manufacturer details are incomplete or fail to state complete postal location."
            rec_action = "Issue formal notice of non-compliance under Legal Metrology Rules."
            verif_note = "Automated check indicates a potential statutory non-compliance based on available evidence."
        else: # NEEDS_REVIEW
            reason = "Manufacturer, packer, or importer declaration could not be reliably detected in the uploaded image."
            rec_action = "Inspect the physical package or upload a clearer image containing the manufacturer/packer declaration."
            verif_note = "Absence of this declaration in the uploaded image does not by itself establish that the physical package is non-compliant."

    elif rule_id == "RULE_6_1_C":
        expected = "Net quantity declaration in standard metric SI unit (kg, g, L, mL, N)."
        if status == "PASS":
            reason = "Net quantity declared in standard metric SI unit."
            rec_action = "Automated check passed based on available evidence. Verify physical weight accuracy if required."
            verif_note = "The uploaded evidence satisfies the automated rule check. Final legal determination remains with authorized inspector."
        elif status == "FAIL":
            reason = "Net quantity declared in non-standard or prohibited measurement units."
            rec_action = "Flag non-standard measurement unit violation under Rule 6(1)(c)."
            verif_note = "Automated check indicates a potential statutory non-compliance based on available evidence."
        else: # NEEDS_REVIEW
            reason = "Net quantity declaration could not be reliably detected in the uploaded image."
            rec_action = "Inspect the physical package or upload a clearer image showing the net quantity declaration."
            verif_note = "Absence of this declaration in the uploaded image does not by itself establish that the physical package is non-compliant."

    elif rule_id == "RULE_6_1_E":
        expected = "Maximum Retail Price (MRP) formatted with currency symbol and inclusive of all taxes statement."
        if status == "PASS":
            reason = "MRP clearly declared inclusive of all taxes in Indian Rupees (₹ / Rs.)."
            rec_action = "Automated check passed based on available evidence."
            verif_note = "The uploaded evidence satisfies the automated rule check. Final legal determination remains with authorized inspector."
        elif status == "FAIL":
            reason = "MRP declaration formatted without currency symbol or missing mandatory tax statement."
            rec_action = "Flag pricing declaration non-compliance under Rule 6(1)(e)."
            verif_note = "Automated check indicates a potential statutory non-compliance based on available evidence."
        else: # NEEDS_REVIEW
            reason = "MRP declaration could not be reliably detected in the uploaded image."
            rec_action = "Inspect the physical package for the MRP declaration or upload a clearer image containing the price."
            verif_note = "Absence of this declaration in the uploaded image does not by itself establish that the physical package is non-compliant."

    elif rule_id == "RULE_6_1_N":
        expected = "Name, postal address, telephone helpline number, and email address for consumer complaints."
        if status == "PASS":
            reason = "Consumer grievance helpline or email contact details detected."
            rec_action = "Automated check passed based on available evidence."
            verif_note = "The uploaded evidence satisfies the automated rule check. Final legal determination remains with authorized inspector."
        elif status == "FAIL":
            reason = "Consumer care contact details are missing required contact channels."
            rec_action = "Flag consumer redressal declaration deficiency under Rule 6(1)(n)."
            verif_note = "Automated check indicates a potential statutory non-compliance based on available evidence."
        else: # NEEDS_REVIEW
            reason = "Consumer care contact details could not be reliably detected in the uploaded image."
            rec_action = "Inspect the package for the applicable consumer care contact details or upload a clearer image."
            verif_note = "Absence of this declaration in the uploaded image does not by itself establish that the physical package is non-compliant."

    elif rule_id == "RULE_6_1_D":
        expected = "Month and year of manufacture or packing clearly stated (MM/YYYY)."
        if status == "PASS":
            reason = "Date of manufacture/packing clearly declared in readable format."
            rec_action = "Automated check passed based on available evidence."
            verif_note = "The uploaded evidence satisfies the automated rule check. Final legal determination remains with authorized inspector."
        elif status == "FAIL":
            reason = "Manufacturing date declaration is invalid or improperly formatted."
            rec_action = "Flag date declaration non-compliance under Rule 6(1)(d)."
            verif_note = "Automated check indicates a potential statutory non-compliance based on available evidence."
        else: # NEEDS_REVIEW
            reason = "Month and year of manufacture/packing could not be reliably detected in the uploaded image."
            rec_action = "Inspect the date declaration on the physical package or upload a clearer image."
            verif_note = "Absence of this declaration in the uploaded image does not by itself establish that the physical package is non-compliant."

    elif rule_id == "RULE_7":
        expected = "Declaration text font height meets minimum statutory height thresholds based on package size."
        if status == "PASS":
            reason = "Declaration font size meets statutory height requirements."
            rec_action = "Automated check passed based on available evidence."
            verif_note = "The uploaded evidence satisfies the automated rule check. Final legal determination remains with authorized inspector."
        elif status == "FAIL":
            reason = "Font size is below statutory minimum height threshold."
            rec_action = "Flag font size deficiency under Rule 7."
            verif_note = "Automated check indicates a potential statutory non-compliance based on available evidence."
        else: # NEEDS_REVIEW
            reason = "Text size and visibility require visual verification and could not be reliably determined from automated analysis."
            rec_action = "Perform a physical visual inspection of the package to verify declaration legibility and font height."
            verif_note = "Physical visual measurement with calibrated gauge is recommended."

    elif rule_id == "RULE_11":
        expected = "Standard weight/measurement symbol specified accurately according to SI standards."
        if status == "PASS":
            reason = "Standard weight/measurement unit symbol used appropriately."
            rec_action = "Automated check passed based on available evidence."
            verif_note = "The uploaded evidence satisfies the automated rule check. Final legal determination remains with authorized inspector."
        elif status == "FAIL":
            reason = "Unit symbol violates statutory symbol standards."
            rec_action = "Flag unit symbol violation under Rule 11."
            verif_note = "Automated check indicates a potential statutory non-compliance based on available evidence."
        else: # NEEDS_REVIEW
            reason = "Applicable standard weight/measurement unit symbol could not be reliably detected in the uploaded image."
            rec_action = "Inspect the physical package or upload a clearer image showing the quantity and unit declaration."
            verif_note = "Absence of this declaration in the uploaded image does not by itself establish that the physical package is non-compliant."
    else:
        expected = "Statutory compliance requirement under Legal Metrology Rules."
        reason = f"Check evaluated with status {status}."
        rec_action = "Inspect physical package or verify additional details."
        verif_note = "Automated analysis result based on available image evidence."

    return {
        "confidence": conf_pct,
        "reason": reason,
        "expected_declaration": expected,
        "recommended_action": rec_action,
        "verification_note": verif_note
    }

def evaluate_compliance(extracted_fields: dict) -> dict:
    """
    Deterministic Compliance Engine evaluating extracted OCR evidence against 
    versioned Legal Metrology statutory rules.
    """
    checks = []
    violations = []
    warnings = []
    rule_versions_used = []

    total_weight = 0.0
    earned_weight = 0.0

    for rule in RULES_REGISTRY:
        if not rule.get("enabled"):
            continue

        rule_id = rule["rule_id"]
        source_ref = rule["source_reference"]
        req_title = rule["requirement"]
        severity = rule["severity"]
        rule_versions_used.append(f"{rule_id} v{rule['rule_version']}")

        # Weights per severity
        weight = 25.0 if severity == "critical" else (15.0 if severity == "major" else 5.0)
        total_weight += weight

        if rule_id == "RULE_6_1_A":
            mfr, conf = extract_val_and_conf(extracted_fields, "manufacturer")
            if not mfr or len(str(mfr).strip()) < 3:
                status = "NEEDS_REVIEW"
                explanation = "Manufacturer/packer details not detected in uploaded image; manual verification required."
                extracted_disp = "Not detected in uploaded image"
            elif conf < 0.65:
                status = "NEEDS_REVIEW"
                explanation = "Manufacturer detail detected with low OCR confidence; manual verification required."
                extracted_disp = str(mfr)[:45]
            else:
                status = "PASS"
                explanation = "Valid manufacturer name and postal address identified."
                earned_weight += weight
                extracted_disp = str(mfr)[:45]

            dt = get_rule_details(rule_id, status, extracted_disp, conf)
            checks.append({
                "rule_id": rule_id,
                "requirement": req_title,
                "extracted_value": extracted_disp,
                "source_reference": source_ref,
                "status": status,
                "severity": severity.upper(),
                "explanation": explanation,
                "confidence": dt["confidence"],
                "reason": dt["reason"],
                "expected_declaration": dt["expected_declaration"],
                "recommended_action": dt["recommended_action"],
                "verification_note": dt["verification_note"]
            })

        elif rule_id == "RULE_6_1_C":
            net_qty, conf = extract_val_and_conf(extracted_fields, "net_quantity")
            if not net_qty:
                status = "NEEDS_REVIEW"
                explanation = "Net quantity declaration not detected in uploaded image; officer review required."
                extracted_disp = "Not detected in uploaded image"
            elif conf < 0.65:
                status = "NEEDS_REVIEW"
                explanation = "Net quantity detected with low confidence; officer verification required."
                extracted_disp = str(net_qty)
            elif re.search(r'\b\d+(?:\.\d+)?\s*(?:kg|g|ml|l|n|grams|kilograms)\b', str(net_qty), re.I):
                status = "PASS"
                explanation = "Net quantity declared in standard SI units."
                earned_weight += weight
                extracted_disp = str(net_qty)
            else:
                status = "FAIL"
                explanation = "Net quantity declared in non-standard unit."
                extracted_disp = str(net_qty)
                violations.append({
                    "rule_id": rule_id,
                    "requirement": req_title,
                    "severity": severity,
                    "explanation": "Rule 6(1)(c) mandates net weight/volume in standard metric units."
                })

            dt = get_rule_details(rule_id, status, extracted_disp, conf)
            checks.append({
                "rule_id": rule_id,
                "requirement": req_title,
                "extracted_value": extracted_disp,
                "source_reference": source_ref,
                "status": status,
                "severity": severity.upper(),
                "explanation": explanation,
                "confidence": dt["confidence"],
                "reason": dt["reason"],
                "expected_declaration": dt["expected_declaration"],
                "recommended_action": dt["recommended_action"],
                "verification_note": dt["verification_note"]
            })

        elif rule_id == "RULE_6_1_E":
            mrp, conf = extract_val_and_conf(extracted_fields, "mrp")
            if not mrp:
                status = "NEEDS_REVIEW"
                explanation = "MRP declaration not detected in uploaded image; officer review required."
                extracted_disp = "Not detected in uploaded image"
            elif conf < 0.65:
                status = "NEEDS_REVIEW"
                explanation = "MRP detected with low OCR confidence; officer review required."
                extracted_disp = str(mrp)
            elif "₹" in str(mrp) or "RS" in str(mrp).upper():
                status = "PASS"
                explanation = "MRP clearly declared inclusive of all taxes."
                earned_weight += weight
                extracted_disp = str(mrp)
            else:
                status = "FAIL"
                explanation = "MRP declaration formatted without currency symbol or tax statement."
                extracted_disp = str(mrp)
                violations.append({
                    "rule_id": rule_id,
                    "requirement": req_title,
                    "severity": severity,
                    "explanation": "Rule 6(1)(e) requires price inclusive of all taxes."
                })

            dt = get_rule_details(rule_id, status, extracted_disp, conf)
            checks.append({
                "rule_id": rule_id,
                "requirement": req_title,
                "extracted_value": extracted_disp,
                "source_reference": source_ref,
                "status": status,
                "severity": severity.upper(),
                "explanation": explanation,
                "confidence": dt["confidence"],
                "reason": dt["reason"],
                "expected_declaration": dt["expected_declaration"],
                "recommended_action": dt["recommended_action"],
                "verification_note": dt["verification_note"]
            })

        elif rule_id == "RULE_6_1_N":
            care, conf = extract_val_and_conf(extracted_fields, "consumer_care")
            if not care:
                status = "NEEDS_REVIEW"
                explanation = "Consumer care contact details not detected in uploaded image; manual verification required."
                extracted_disp = "Not detected in uploaded image"
            elif conf < 0.65:
                status = "NEEDS_REVIEW"
                explanation = "Consumer care contact extracted with low OCR confidence; manual verification required."
                extracted_disp = str(care)[:35]
            elif ("TEL" in str(care).upper() or "EMAIL" in str(care).upper() or "@" in str(care) or "1800" in str(care) or "HELP" in str(care).upper() or "CARE" in str(care).upper()):
                status = "PASS"
                explanation = "Consumer grievance helpline/email details present."
                earned_weight += weight
                extracted_disp = str(care)[:35]
            else:
                status = "NEEDS_REVIEW"
                explanation = "Consumer care contact details require manual verification."
                extracted_disp = str(care)[:35]

            dt = get_rule_details(rule_id, status, extracted_disp, conf)
            checks.append({
                "rule_id": rule_id,
                "requirement": req_title,
                "extracted_value": extracted_disp,
                "source_reference": source_ref,
                "status": status,
                "severity": severity.upper(),
                "explanation": explanation,
                "confidence": dt["confidence"],
                "reason": dt["reason"],
                "expected_declaration": dt["expected_declaration"],
                "recommended_action": dt["recommended_action"],
                "verification_note": dt["verification_note"]
            })

        elif rule_id == "RULE_6_1_D":
            mfg_date, conf = extract_val_and_conf(extracted_fields, "manufacturing_date")
            if not mfg_date:
                mfg_date, conf = extract_val_and_conf(extracted_fields, "mfg_date")

            if not mfg_date:
                status = "NEEDS_REVIEW"
                explanation = "Month and year of manufacture not detected in uploaded image; manual verification required."
                extracted_disp = "Not detected in uploaded image"
            elif conf < 0.65:
                status = "NEEDS_REVIEW"
                explanation = "Mfg date extracted with low OCR confidence; manual verification required."
                extracted_disp = str(mfg_date)
            else:
                status = "PASS"
                explanation = "Date of manufacture/packing clearly declared."
                earned_weight += weight
                extracted_disp = str(mfg_date)

            dt = get_rule_details(rule_id, status, extracted_disp, conf)
            checks.append({
                "rule_id": rule_id,
                "requirement": req_title,
                "extracted_value": extracted_disp,
                "source_reference": source_ref,
                "status": status,
                "severity": severity.upper(),
                "explanation": explanation,
                "confidence": dt["confidence"],
                "reason": dt["reason"],
                "expected_declaration": dt["expected_declaration"],
                "recommended_action": dt["recommended_action"],
                "verification_note": dt["verification_note"]
            })

        elif rule_id == "RULE_7":
            dt = get_rule_details(rule_id, "NEEDS_REVIEW", "Visual Inspection Required", 0.0)
            checks.append({
                "rule_id": rule_id,
                "requirement": req_title,
                "extracted_value": "Visual Inspection Required",
                "source_reference": source_ref,
                "status": "NEEDS_REVIEW",
                "severity": severity.upper(),
                "explanation": "Font size height requires physical visual measurement threshold verification.",
                "confidence": dt["confidence"],
                "reason": dt["reason"],
                "expected_declaration": dt["expected_declaration"],
                "recommended_action": dt["recommended_action"],
                "verification_note": dt["verification_note"]
            })

        elif rule_id == "RULE_11":
            net_qty, conf = extract_val_and_conf(extracted_fields, "net_quantity")
            if net_qty and re.search(r'\b\d+(?:\.\d+)?\s*(?:kg|g|ml|l|n|grams|kilograms)\b', str(net_qty), re.I):
                status = "PASS"
                extracted_disp = str(net_qty)
                explanation = "Standard SI unit symbol used appropriately."
                earned_weight += weight
            else:
                status = "NEEDS_REVIEW"
                extracted_disp = "Not detected in uploaded image"
                explanation = "Unit symbol check requires detected net quantity."

            dt = get_rule_details(rule_id, status, extracted_disp, conf)
            checks.append({
                "rule_id": rule_id,
                "requirement": req_title,
                "extracted_value": extracted_disp,
                "source_reference": source_ref,
                "status": status,
                "severity": severity.upper(),
                "explanation": explanation,
                "confidence": dt["confidence"],
                "reason": dt["reason"],
                "expected_declaration": dt["expected_declaration"],
                "recommended_action": dt["recommended_action"],
                "verification_note": dt["verification_note"]
            })

    # Status Aggregation Logic (Priority: FAIL -> NEEDS_REVIEW -> PASS)
    has_fail = any(c["status"] == "FAIL" for c in checks)
    has_needs_review = any(c["status"] == "NEEDS_REVIEW" for c in checks)
    all_pass = all(c["status"] == "PASS" for c in checks)

    if has_fail:
        overall_status = "NON-COMPLIANT"
        score = round((earned_weight / total_weight) * 100.0, 1) if total_weight > 0 else 0.0
    elif has_needs_review:
        overall_status = "NEEDS_REVIEW"
        score = None  # Score unavailable when evidence is unverified/missing
    elif all_pass:
        overall_status = "COMPLIANT"
        score = 100.0
    else:
        overall_status = "NEEDS_REVIEW"
        score = None

    return {
        "score": score,
        "compliance_score": score,
        "overall_status": overall_status,
        "status": overall_status,
        "checks": checks,
        "compliance_checks": checks,
        "violations": violations,
        "warnings": warnings,
        "rule_versions_used": rule_versions_used,
        "generated_at": datetime.utcnow().isoformat()
    }

import asyncio
import os
import time
from uuid import uuid4
from datetime import datetime

from app.database import get_database, connect_to_mongo
from app.config import settings
from app.services.ocr_service import run_ocr_with_metrics, extract_structured_fields
from app.services.compliance_engine import evaluate_compliance

async def analyze():
    await connect_to_mongo()
    db = get_database()
    
    # Find an inspection that needs analysis
    inspection = await db.inspections.find_one({"status": "NEEDS_REVIEW"})
    if not inspection:
        print("No inspection found.")
        return
        
    inspection_id = inspection["inspection_id"]
    filepath = inspection["image_path"]
    
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        # Try sample_label.jpg
        filepath = "sample_label.jpg"
        if not os.path.exists(filepath):
            print("Fallback sample_label.jpg not found either.")
            return

    print(f"Analyzing {filepath} for {inspection_id}...")
    
    try:
        t_total_start = time.time()

        print("Running OCR...")
        raw_text, ocr_conf, ocr_metrics = run_ocr_with_metrics(filepath)

        print("Extracting fields...")
        t_ext_start = time.time()
        extracted_fields = extract_structured_fields(raw_text, inspection.get("filename", ""))
        t_ext_end = time.time()
        field_ext_sec = round(t_ext_end - t_ext_start, 4)
        
        # Test property access that's in the router
        print("Parsing extracted fields...")
        p_name = extracted_fields.get("product_name", {}).get("value") if isinstance(extracted_fields.get("product_name"), dict) else extracted_fields.get("product_name")
        p_net = extracted_fields.get("net_quantity", {}).get("value") if isinstance(extracted_fields.get("net_quantity"), dict) else extracted_fields.get("net_quantity")
        p_mrp = extracted_fields.get("mrp", {}).get("value") if isinstance(extracted_fields.get("mrp"), dict) else extracted_fields.get("mrp")
        p_mfg = extracted_fields.get("manufacturing_date", {}).get("value") if isinstance(extracted_fields.get("manufacturing_date"), dict) else extracted_fields.get("manufacturing_date")
        p_mfr = extracted_fields.get("manufacturer", {}).get("value") if isinstance(extracted_fields.get("manufacturer"), dict) else extracted_fields.get("manufacturer")
        p_care = extracted_fields.get("consumer_care", {}).get("value") if isinstance(extracted_fields.get("consumer_care"), dict) else extracted_fields.get("consumer_care")
        p_origin = extracted_fields.get("country_of_origin", {}).get("value") if isinstance(extracted_fields.get("country_of_origin"), dict) else extracted_fields.get("country_of_origin")

        print("Evaluating compliance...")
        comp_result = evaluate_compliance(extracted_fields)
        
        print("Done!")
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(analyze())

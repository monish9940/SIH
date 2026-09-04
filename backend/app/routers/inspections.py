from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, Response, status
from typing import List, Optional
from datetime import datetime
from uuid import uuid4
import os
import shutil
import time
import logging
from app.database import get_database
from app.config import settings
from app.services.auth_service import get_current_user
from app.services.ocr_service import run_ocr, run_ocr_with_metrics, extract_structured_fields
from app.services.compliance_engine import evaluate_compliance
from app.services.pdf_service import generate_inspection_pdf

router = APIRouter(prefix="/api/inspections", tags=["Inspections"])

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_inspection(
    file: UploadFile = File(...),
    commodity_type: str = Form("General Pre-packaged Goods"),
    inspection_profile: str = Form("Standard PCR Rules 2011"),
    user: dict = Depends(get_current_user)
):
    user_id = user["user_id"]
    db = get_database()

    # Validate file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be a valid image (JPG, PNG, WEBP).")

    # Generate unique inspection ID and save file
    insp_number = str(uuid4())[:8].upper()
    inspection_id = f"INSP-2026-{insp_number}"
    
    file_ext = os.path.splitext(file.filename)[1] or ".jpg"
    filename = f"{inspection_id}{file_ext}"
    filepath = os.path.join(settings.UPLOAD_DIR, filename)

    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    inspection_doc = {
        "inspection_id": inspection_id,
        "user_id": user_id,
        "officer_name": user.get("full_name", "Officer"),
        "image_path": filepath,
        "filename": filename,
        "commodity_type": commodity_type,
        "inspection_profile": inspection_profile,
        "product_information": {},
        "ocr_result": "",
        "ocr_confidence": 0.0,
        "compliance_checks": [],
        "compliance_score": 0.0,
        "overall_status": "NEEDS_REVIEW",
        "status": "NEEDS_REVIEW",
        "violations": [],
        "warnings": [],
        "created_at": datetime.utcnow(),
        "analyzed": False
    }

    await db.inspections.insert_one(inspection_doc)

    return {
        "inspection_id": inspection_id,
        "message": "Inspection record created successfully. Proceed to analysis."
    }

@router.post("/{inspection_id}/analyze")
async def analyze_inspection(
    inspection_id: str,
    user: dict = Depends(get_current_user)
):
    user_id = user["user_id"]
    db = get_database()

    inspection = await db.inspections.find_one({"inspection_id": inspection_id})
    if not inspection:
        raise HTTPException(status_code=404, detail="Inspection record not found.")

    # Strict Officer Ownership Check
    if inspection.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Forbidden: You are not authorized to analyze this inspection record.")

    filepath = inspection["image_path"]
    if not os.path.exists(filepath):
        raise HTTPException(status_code=400, detail="Inspection image file missing on server.")

    logger = logging.getLogger("inspections_router")
    logger.info(f"Processing inspection analysis [{inspection_id}] for image: {filepath}")

    t_total_start = time.time()

    # 1. OCR Execution with Stage Metrics
    raw_text, ocr_conf, ocr_metrics = run_ocr_with_metrics(filepath)

    # 2. Structured Field Extraction
    t_ext_start = time.time()
    extracted_fields = extract_structured_fields(raw_text, inspection.get("filename", ""))
    t_ext_end = time.time()
    field_ext_sec = round(t_ext_end - t_ext_start, 4)

    p_name = extracted_fields.get("product_name", {}).get("value") if isinstance(extracted_fields.get("product_name"), dict) else extracted_fields.get("product_name")
    p_net = extracted_fields.get("net_quantity", {}).get("value") if isinstance(extracted_fields.get("net_quantity"), dict) else extracted_fields.get("net_quantity")
    p_mrp = extracted_fields.get("mrp", {}).get("value") if isinstance(extracted_fields.get("mrp"), dict) else extracted_fields.get("mrp")
    p_mfg = extracted_fields.get("manufacturing_date", {}).get("value") if isinstance(extracted_fields.get("manufacturing_date"), dict) else extracted_fields.get("manufacturing_date")
    p_mfr = extracted_fields.get("manufacturer", {}).get("value") if isinstance(extracted_fields.get("manufacturer"), dict) else extracted_fields.get("manufacturer")
    p_care = extracted_fields.get("consumer_care", {}).get("value") if isinstance(extracted_fields.get("consumer_care"), dict) else extracted_fields.get("consumer_care")
    p_origin = extracted_fields.get("country_of_origin", {}).get("value") if isinstance(extracted_fields.get("country_of_origin"), dict) else extracted_fields.get("country_of_origin")

    # 3. Rule Engine Evaluation
    t_comp_start = time.time()
    comp_result = evaluate_compliance(extracted_fields)
    t_comp_end = time.time()
    comp_eng_sec = round(t_comp_end - t_comp_start, 4)

    # 4. MongoDB Persistence
    t_mongo_start = time.time()
    ocr_doc = {
        "ocr_id": str(uuid4()),
        "inspection_id": inspection_id,
        "user_id": user_id,
        "raw_text": raw_text,
        "ocr_confidence": ocr_conf,
        "structured_fields": extracted_fields,
        "created_at": datetime.utcnow()
    }
    await db.ocr_results.insert_one(ocr_doc)

    comp_doc = {
        "compliance_id": str(uuid4()),
        "inspection_id": inspection_id,
        "user_id": user_id,
        "score": comp_result["score"],
        "status": comp_result["overall_status"],
        "checks": comp_result["checks"],
        "violations": comp_result["violations"],
        "warnings": comp_result["warnings"],
        "rule_versions_used": comp_result["rule_versions_used"],
        "created_at": datetime.utcnow()
    }
    await db.compliance_results.insert_one(comp_doc)

    product_info = {
        "product_name": p_name or "Not detected in uploaded image",
        "commodity": inspection.get("commodity_type", "Pre-packaged Goods"),
        "net_quantity": p_net or "Not detected in uploaded image",
        "mrp": p_mrp or "Not detected in uploaded image",
        "mfg_date": p_mfg or "Not detected in uploaded image",
        "manufacturer": p_mfr or "Not detected in uploaded image",
        "consumer_care": p_care or "Not detected in uploaded image",
        "country_of_origin": p_origin or "Not detected in uploaded image"
    }

    update_fields = {
        "product_information": product_info,
        "ocr_result": raw_text,
        "ocr_confidence": ocr_conf,
        "compliance_checks": comp_result["checks"],
        "compliance_score": comp_result["score"],
        "overall_status": comp_result["overall_status"],
        "status": comp_result["overall_status"],
        "violations": comp_result["violations"],
        "warnings": comp_result["warnings"],
        "analyzed": True,
        "updated_at": datetime.utcnow()
    }

    await db.inspections.update_one({"inspection_id": inspection_id}, {"$set": update_fields})
    t_mongo_end = time.time()
    mongo_sec = round(t_mongo_end - t_mongo_start, 4)

    t_total_end = time.time()
    total_sec = round(t_total_end - t_total_start, 4)

    # Required Stage Timing Log Profile
    logger.info(f"==========================================================")
    logger.info(f"TIMING DIAGNOSTIC PROFILE FOR INSPECTION [{inspection_id}]")
    logger.info(f"Image upload/reading:      {ocr_metrics.get('image_read_sec', 0)} seconds")
    logger.info(f"OCR model loading:         {ocr_metrics.get('model_init_sec', 0)} seconds")
    logger.info(f"OCR inference:             {ocr_metrics.get('ocr_inference_sec', 0)} seconds (Passes: {ocr_metrics.get('num_passes', 1)})")
    logger.info(f"OCR text post-processing:  {ocr_metrics.get('ocr_postproc_sec', 0)} seconds")
    logger.info(f"Field extraction:          {field_ext_sec} seconds")
    logger.info(f"Compliance engine:         {comp_eng_sec} seconds")
    logger.info(f"MongoDB:                   {mongo_sec} seconds")
    logger.info(f"TOTAL:                     {total_sec} seconds")
    logger.info(f"==========================================================")

    updated_doc = await db.inspections.find_one({"inspection_id": inspection_id})
    updated_doc.pop("_id", None)
    return updated_doc

@router.get("")
async def list_inspections(
    limit: int = 50,
    status: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    user_id = user["user_id"]
    db = get_database()

    query = {"user_id": user_id}
    if status and status != "ALL":
        query["overall_status"] = status

    cursor = db.inspections.find(query).sort("created_at", -1).limit(limit)
    items = []
    async for doc in cursor:
        doc.pop("_id", None)
        items.append(doc)

    return items

@router.get("/{inspection_id}")
async def get_inspection(
    inspection_id: str,
    user: dict = Depends(get_current_user)
):
    user_id = user["user_id"]
    db = get_database()

    inspection = await db.inspections.find_one({"inspection_id": inspection_id})
    if not inspection:
        raise HTTPException(status_code=404, detail="Inspection record not found.")

    # Strict Ownership Enforcement
    if inspection.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Forbidden: You are not authorized to view this inspection record.")

    inspection.pop("_id", None)
    return inspection

from pydantic import BaseModel, Field

class CompleteReviewRequest(BaseModel):
    officer_review_notes: Optional[str] = Field(None, max_length=1000)

@router.patch("/{inspection_id}/complete-review")
async def complete_inspection_review(
    inspection_id: str,
    payload: CompleteReviewRequest = CompleteReviewRequest(),
    user: dict = Depends(get_current_user)
):
    user_id = user["user_id"]
    db = get_database()

    inspection = await db.inspections.find_one({"inspection_id": inspection_id})
    if not inspection:
        raise HTTPException(status_code=404, detail="Inspection record not found.")

    # Strict Officer Ownership Enforcement
    if inspection.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Forbidden: You are not authorized to complete review for this inspection.")

    # Check if already resolved
    if inspection.get("status") == "RESOLVED" or inspection.get("overall_status") == "RESOLVED":
        raise HTTPException(status_code=400, detail="Inspection review has already been completed.")

    notes = (payload.officer_review_notes or "").strip()
    if len(notes) > 1000:
        raise HTTPException(status_code=400, detail="Officer review notes cannot exceed 1000 characters.")

    automated_status = inspection.get("automated_status") or inspection.get("overall_status") or "NEEDS_REVIEW"

    update_fields = {
        "status": "RESOLVED",
        "overall_status": "RESOLVED",
        "automated_status": automated_status,
        "reviewed_by": user_id,
        "reviewed_by_name": user.get("full_name", "Officer"),
        "reviewed_at": datetime.utcnow(),
        "officer_review_notes": notes,
        "updated_at": datetime.utcnow()
    }

    await db.inspections.update_one({"inspection_id": inspection_id}, {"$set": update_fields})

    updated_doc = await db.inspections.find_one({"inspection_id": inspection_id})
    updated_doc.pop("_id", None)
    return updated_doc

@router.get("/{inspection_id}/pdf")
async def download_inspection_pdf(
    inspection_id: str,
    user: dict = Depends(get_current_user)
):
    user_id = user["user_id"]
    db = get_database()

    inspection = await db.inspections.find_one({"inspection_id": inspection_id})
    if not inspection:
        raise HTTPException(status_code=404, detail="Inspection record not found.")

    # Strict Ownership Enforcement
    if inspection.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Forbidden: You are not authorized to download this report.")

    pdf_bytes = generate_inspection_pdf(inspection)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=Compliance_Report_{inspection_id}.pdf"}
    )


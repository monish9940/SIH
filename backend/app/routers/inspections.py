from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, Response, status
from fastapi.responses import JSONResponse
from typing import List, Optional
from datetime import datetime
from uuid import uuid4
import os
import shutil
import time
import logging
import asyncio
from starlette.concurrency import run_in_threadpool
from app.database import get_database
from app.config import settings
from app.services.auth_service import get_current_user
from app.services.ocr_service import run_ocr, run_ocr_with_metrics, extract_structured_fields, preprocess_image_fast, get_easyocr_reader, is_ocr_ready
from app.services.compliance_engine import evaluate_compliance
from app.services.pdf_service import generate_inspection_pdf

router = APIRouter(prefix="/api/inspections", tags=["Inspections"])

# Global strong-reference set to prevent background asyncio tasks from being garbage-collected
_background_tasks: set = set()

async def run_background_analysis(inspection_id: str, user_id: str, filepath: str, filename: str, commodity_type: str):
    logger = logging.getLogger("inspections_router")
    t_start = time.time()
    logger.info(f"BACKGROUND ANALYSIS START [{inspection_id}]")
    db = get_database()
    try:
        # 1. Preprocess / Decode check
        _, _ = await run_in_threadpool(preprocess_image_fast, filepath)

        # 2. OCR Execution
        logger.info(f"OCR START [{inspection_id}] | elapsed: {time.time() - t_start:.3f}s")
        t_ocr_start = time.time()
        raw_text, ocr_conf, ocr_metrics = await run_in_threadpool(run_ocr_with_metrics, filepath)
        t_ocr_end = time.time()
        logger.info(f"OCR END [{inspection_id}] | duration: {t_ocr_end - t_ocr_start:.3f}s | elapsed: {time.time() - t_start:.3f}s")

        # 3. Structured Field Extraction
        logger.info(f"STRUCTURED EXTRACTION START [{inspection_id}] | elapsed: {time.time() - t_start:.3f}s")
        t_ext_start = time.time()
        extracted_fields = extract_structured_fields(raw_text, filename)
        t_ext_end = time.time()
        logger.info(f"STRUCTURED EXTRACTION END [{inspection_id}] | duration: {t_ext_end - t_ext_start:.3f}s | elapsed: {time.time() - t_start:.3f}s")

        p_name = extracted_fields.get("product_name", {}).get("value") if isinstance(extracted_fields.get("product_name"), dict) else extracted_fields.get("product_name")
        p_net = extracted_fields.get("net_quantity", {}).get("value") if isinstance(extracted_fields.get("net_quantity"), dict) else extracted_fields.get("net_quantity")
        p_mrp = extracted_fields.get("mrp", {}).get("value") if isinstance(extracted_fields.get("mrp"), dict) else extracted_fields.get("mrp")
        p_mfg = extracted_fields.get("manufacturing_date", {}).get("value") if isinstance(extracted_fields.get("manufacturing_date"), dict) else extracted_fields.get("manufacturing_date")
        p_mfr = extracted_fields.get("manufacturer", {}).get("value") if isinstance(extracted_fields.get("manufacturer"), dict) else extracted_fields.get("manufacturer")
        p_care = extracted_fields.get("consumer_care", {}).get("value") if isinstance(extracted_fields.get("consumer_care"), dict) else extracted_fields.get("consumer_care")
        p_origin = extracted_fields.get("country_of_origin", {}).get("value") if isinstance(extracted_fields.get("country_of_origin"), dict) else extracted_fields.get("country_of_origin")

        # 4. Compliance Engine Evaluation
        logger.info(f"COMPLIANCE START [{inspection_id}] | elapsed: {time.time() - t_start:.3f}s")
        t_comp_start = time.time()
        comp_result = evaluate_compliance(extracted_fields)
        t_comp_end = time.time()
        logger.info(f"COMPLIANCE END [{inspection_id}] | duration: {t_comp_end - t_comp_start:.3f}s | elapsed: {time.time() - t_start:.3f}s")

        # 5. MongoDB Persistence
        logger.info(f"MONGODB SAVE START [{inspection_id}] | elapsed: {time.time() - t_start:.3f}s")
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
            "commodity": commodity_type or "Pre-packaged Goods",
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
            "analysis_status": "COMPLETED",
            "analysis_completed_at": datetime.utcnow(),
            "analysis_error": None,
            "updated_at": datetime.utcnow()
        }

        await db.inspections.update_one({"inspection_id": inspection_id}, {"$set": update_fields})
        t_mongo_end = time.time()
        logger.info(f"MONGODB SAVE END [{inspection_id}] | duration: {t_mongo_end - t_mongo_start:.3f}s | elapsed: {time.time() - t_start:.3f}s")
        logger.info(f"BACKGROUND ANALYSIS COMPLETE [{inspection_id}] | TOTAL DURATION: {time.time() - t_start:.3f}s")

    except Exception as exc:
        logger.error(f"BACKGROUND ANALYSIS FAILED [{inspection_id}] | exception: {type(exc).__name__}: {exc}", exc_info=True)
        safe_error = "Unable to decode uploaded image" if "Unable to decode" in str(exc) else f"Analysis failed: {str(exc)}"
        await db.inspections.update_one(
            {"inspection_id": inspection_id},
            {"$set": {
                "analysis_status": "FAILED",
                "analysis_error": safe_error,
                "analysis_completed_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }}
        )

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
        "analyzed": False,
        "analysis_status": "PENDING"
    }

    await db.inspections.insert_one(inspection_doc)

    return {
        "inspection_id": inspection_id,
        "message": "Inspection record created successfully. Proceed to analysis."
    }

@router.post("/{inspection_id}/analyze", status_code=status.HTTP_202_ACCEPTED)
async def analyze_inspection(
    inspection_id: str,
    user: dict = Depends(get_current_user)
):
    logger = logging.getLogger("inspections_router")
    logger.info(f"START ANALYZE HTTP [{inspection_id}]")

    # Readiness guard: never initialize EasyOCR inside an HTTP request
    if not is_ocr_ready():
        logger.warning(f"OCR engine is not ready for inspection [{inspection_id}]")
        raise HTTPException(status_code=503, detail="OCR engine is not ready. Please retry shortly.")

    user_id = user["user_id"]
    db = get_database()

    inspection = await db.inspections.find_one({"inspection_id": inspection_id})
    if not inspection:
        raise HTTPException(status_code=404, detail="Inspection record not found.")

    # Strict Officer Ownership Check
    if inspection.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Forbidden: You are not authorized to analyze this inspection record.")

    filepath = inspection.get("image_path", "")
    if not filepath or not os.path.exists(filepath):
        raise HTTPException(status_code=400, detail="Inspection image file missing on server.")

    logger.info(f"VALIDATION COMPLETE [{inspection_id}]")
    logger.info(f"OCR READY [{inspection_id}]")

    # Prevent duplicate analysis jobs
    if inspection.get("analysis_status") == "PROCESSING":
        logger.info(f"ANALYSIS ALREADY IN PROGRESS [{inspection_id}]")
        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content={
                "inspection_id": inspection_id,
                "status": "PROCESSING",
                "message": "Analysis job is already in progress"
            }
        )

    now = datetime.utcnow()
    await db.inspections.update_one(
        {"inspection_id": inspection_id},
        {"$set": {
            "analysis_status": "PROCESSING",
            "analysis_started_at": now,
            "analysis_error": None,
            "updated_at": now
        }}
    )

    logger.info(f"ANALYSIS STATUS SET PROCESSING [{inspection_id}]")

    task = asyncio.create_task(
        run_background_analysis(
            inspection_id=inspection_id,
            user_id=user_id,
            filepath=filepath,
            filename=inspection.get("filename", ""),
            commodity_type=inspection.get("commodity_type", "General Pre-packaged Goods")
        )
    )
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)

    logger.info(f"BACKGROUND TASK CREATED [{inspection_id}]")
    logger.info(f"RETURNING 202 [{inspection_id}]")

    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={
            "inspection_id": inspection_id,
            "status": "PROCESSING",
            "message": "Analysis started"
        }
    )

@router.get("/{inspection_id}/analysis-status")
async def get_analysis_status(
    inspection_id: str,
    user: dict = Depends(get_current_user)
):
    user_id = user["user_id"]
    db = get_database()

    inspection = await db.inspections.find_one({"inspection_id": inspection_id})
    if not inspection:
        raise HTTPException(status_code=404, detail="Inspection record not found.")

    if inspection.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Forbidden: You are not authorized to view status for this inspection.")

    analysis_status = inspection.get("analysis_status")
    if not analysis_status:
        if inspection.get("analyzed"):
            analysis_status = "COMPLETED"
        else:
            analysis_status = "PENDING"

    if analysis_status == "COMPLETED":
        doc = dict(inspection)
        doc.pop("_id", None)
        return {
            "inspection_id": inspection_id,
            "status": "COMPLETED",
            "result": doc
        }
    elif analysis_status == "FAILED":
        return {
            "inspection_id": inspection_id,
            "status": "FAILED",
            "error": inspection.get("analysis_error", "Analysis failed due to an error.")
        }
    else:
        return {
            "inspection_id": inspection_id,
            "status": analysis_status
        }

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



from fastapi import APIRouter, Depends
from datetime import datetime, timedelta
import asyncio
from app.database import get_database
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

@router.get("/summary")
async def get_dashboard_summary(user: dict = Depends(get_current_user)):
    user_id = user["user_id"]
    db = get_database()

    total_scans_task = db.inspections.count_documents({"user_id": user_id})
    compliant_task = db.inspections.count_documents({"user_id": user_id, "overall_status": "COMPLIANT"})
    issues_resolved_task = db.inspections.count_documents({"user_id": user_id, "$or": [{"status": "RESOLVED"}, {"overall_status": "RESOLVED"}]})
    pending_task = db.inspections.count_documents({"user_id": user_id, "overall_status": "NEEDS_REVIEW", "status": {"$ne": "RESOLVED"}})

    total_scans, compliant, issues_resolved, pending = await asyncio.gather(
        total_scans_task, compliant_task, issues_resolved_task, pending_task
    )

    return {
        "total_scans": total_scans,
        "compliant": compliant,
        "issues_resolved": issues_resolved,
        "pending_issues": pending
    }

@router.get("/trends")
async def get_inspection_trends(user: dict = Depends(get_current_user)):
    user_id = user["user_id"]
    db = get_database()

    today = datetime.utcnow().date()
    days = [(today - timedelta(days=i)) for i in range(6, -1, -1)]

    tasks = []
    for day in days:
        start_dt = datetime.combine(day, datetime.min.time())
        end_dt = datetime.combine(day, datetime.max.time())
        tasks.append(
            db.inspections.count_documents({
                "user_id": user_id,
                "created_at": {"$gte": start_dt, "$lte": end_dt}
            })
        )

    counts = await asyncio.gather(*tasks)

    trend_data = [
        {"day": day.strftime("%b %d"), "count": count}
        for day, count in zip(days, counts)
    ]

    return trend_data

@router.get("/resolution-status")
async def get_resolution_status(user: dict = Depends(get_current_user)):
    user_id = user["user_id"]
    db = get_database()

    compliant_task = db.inspections.count_documents({"user_id": user_id, "overall_status": "COMPLIANT"})
    resolved_task = db.inspections.count_documents({"user_id": user_id, "$or": [{"status": "RESOLVED"}, {"overall_status": "RESOLVED"}]})
    pending_task = db.inspections.count_documents({"user_id": user_id, "overall_status": "NEEDS_REVIEW", "status": {"$ne": "RESOLVED"}})
    violations_task = db.inspections.count_documents({"user_id": user_id, "overall_status": "NON-COMPLIANT", "status": {"$ne": "RESOLVED"}})

    compliant, resolved, pending, violations = await asyncio.gather(
        compliant_task, resolved_task, pending_task, violations_task
    )

    return {
        "compliant": compliant,
        "resolved": resolved,
        "violations": violations,
        "pending": pending
    }


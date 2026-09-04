from fastapi import APIRouter, status
from pydantic import BaseModel, EmailStr
from datetime import datetime
from uuid import uuid4
from app.database import get_database

router = APIRouter(prefix="/api/contact", tags=["Contact"])

class ContactSubmission(BaseModel):
    name: str
    email: EmailStr
    phone: str
    subject: str
    message: str

@router.post("", status_code=status.HTTP_201_CREATED)
async def submit_contact_form(data: ContactSubmission):
    db = get_database()
    ticket_id = f"TICK-2026-{str(uuid4())[:6].upper()}"

    doc = {
        "ticket_id": ticket_id,
        "name": data.name,
        "email": data.email,
        "phone": data.phone,
        "subject": data.subject,
        "message": data.message,
        "status": "OPEN",
        "created_at": datetime.utcnow()
    }

    await db.contact_messages.insert_one(doc)

    return {
        "ticket_id": ticket_id,
        "message": "Support ticket created successfully. Our team will contact you within 24 hours."
    }

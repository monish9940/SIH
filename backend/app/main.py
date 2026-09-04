from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import os
import logging
import traceback

from app.config import settings
from app.database import connect_to_mongo, close_mongo_connection
from app.routers import auth, inspections, dashboard, guidelines, contact

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    yield
    await close_mongo_connection()

app = FastAPI(
    title="Compliance Checker API",
    description="Department of Legal Metrology - Packaged Commodity Compliance Verification System",
    version="1.0.0",
    lifespan=lifespan
)

# Global unhandled-exception handler — logs full traceback + returns JSON detail
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    tb = traceback.format_exc()
    logger.error(f"UNHANDLED EXCEPTION on {request.method} {request.url}\n{tb}")
    return JSONResponse(
        status_code=500,
        content={"detail": f"{type(exc).__name__}: {exc}", "traceback": tb}
    )

# CORS setup
origins = settings.CORS_ORIGINS.split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins + ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static file serving for uploads
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Include Routers
app.include_router(auth.router)
app.include_router(inspections.router)
app.include_router(dashboard.router)
app.include_router(guidelines.router)
app.include_router(contact.router)

@app.get("/")
async def root():
    return {
        "title": "Compliance Checker API",
        "department": "Department of Legal Metrology",
        "ministry": "Ministry of Consumer Affairs, Food & Public Distribution",
        "status": "OPERATIONAL"
    }

import sys
import os
# Ensure root backend directory is in sys.path when script is executed directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time
import logging
import traceback

from app.config import settings
from app.database import connect_to_mongo, close_mongo_connection
from app.routers import auth, inspections, dashboard, guidelines, contact

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")

from starlette.concurrency import run_in_threadpool

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Connecting to MongoDB Atlas...")
    await connect_to_mongo()
    logger.info("MongoDB Atlas connected successfully.")

    logger.info("ASYNC ANALYSIS VERSION ACTIVE: 2026.09.05-v4")
    logger.info("ANALYZE ARCHITECTURE: 202_ACCEPTED_POLLING")

    logger.info("EASYOCR PREWARM START")
    t0 = time.perf_counter()
    from app.services.ocr_service import get_easyocr_reader
    reader = await run_in_threadpool(get_easyocr_reader)
    duration = time.perf_counter() - t0

    if reader is None:
        logger.error("EASYOCR PREWARM FAILED")
        raise RuntimeError("EasyOCR prewarm failed during application startup.")

    logger.info(f"EASYOCR PREWARM COMPLETE | duration={duration:.2f}s")
    logger.info("EASYOCR READER READY")
    logger.info("APPLICATION STARTUP COMPLETE")
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

# CORS setup: explicitly allow production Vercel frontend, preview branches, and local dev
allowed_origins = [
    "https://sih-phi-lilac.vercel.app",
    "https://sih-hck9nitc4-monish-2dcf.vercel.app",
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
]
env_origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip() and o.strip() != "*"]
for o in env_origins:
    if o not in allowed_origins:
        allowed_origins.append(o)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin", "X-Requested-With"],
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
        "status": "OPERATIONAL",
        "version": "2026.09.05-v4",
        "architecture": "202_ACCEPTED_POLLING"
    }

@app.get("/health")
@app.get("/api/health")
async def health_check():
    from app.services.ocr_service import is_ocr_ready
    return {
        "status": "ok",
        "ocr_ready": is_ocr_ready(),
        "version": "2026.09.05-v4",
        "architecture": "202_ACCEPTED_POLLING"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)

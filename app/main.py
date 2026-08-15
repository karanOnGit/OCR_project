from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.routes import api_router
from app.core.config import get_settings
from app.core.database import init_db
from app.core.errors import (
    AppException,
    app_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    unhandled_exception_handler,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("app.main")
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure DB tables exist and upload directory is ready
    logger.info("Initializing database and upload directory...")
    init_db()
    settings.upload_path
    logger.info(f"{settings.APP_NAME} started successfully on environment: {settings.APP_ENV}")
    yield
    # Shutdown
    logger.info("Shutting down application...")


app = FastAPI(
    title=settings.APP_NAME,
    description="""
# CaptureBackend OCR API

FastAPI backend for Flutter OCR document scanning and Google Docs integration.

## Features:
* **Image Upload**: Accept document photos (JPG, PNG, WEBP) with validation.
* **OCR Processing**: Extract text using Tesseract OCR with async support.
* **Job Tracking**: Monitor status (`uploaded`, `processing`, `completed`, `failed`).
* **Google Docs**: Append extracted text directly to Google Documents via Google Docs API.
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Custom Exception Handlers
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
if not settings.DEBUG:
    app.add_exception_handler(Exception, unhandled_exception_handler)

# Register API Routers
app.include_router(api_router)


@app.get("/", tags=["Health Check"])
async def root():
    return {
        "name": settings.APP_NAME,
        "status": "healthy",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health Check"])
async def health():
    return {"status": "ok"}

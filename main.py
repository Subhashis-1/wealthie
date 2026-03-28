from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
import logging
import os
from contextlib import asynccontextmanager

from config import settings
from database import engine
from models import Base
from routers.receipts import router as receipts_router
from routers.transactions import router as transactions_router
from routers.reports import router as reports_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Creating database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create upload directory
    os.makedirs(settings.upload_dir, exist_ok=True)
    logger.info(f"Upload directory: {settings.upload_dir}")

    yield

    # Shutdown
    logger.info("Shutting down...")

app = FastAPI(
    title="Wealthie",
    description="AI-Powered Financial Management Platform",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}", exc_info=True)
    return {
        "detail": "Internal server error",
        "type": type(exc).__name__
    }

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Serve index.html at root
from fastapi.responses import FileResponse

@app.get("/")
async def read_root():
    return FileResponse("static/index.html", media_type="text/html")

# Include routers
app.include_router(receipts_router, prefix="/api/receipts", tags=["receipts"])
app.include_router(transactions_router, prefix="/api/transactions", tags=["transactions"])
app.include_router(reports_router, prefix="/api/reports", tags=["reports"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
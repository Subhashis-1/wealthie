from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import uuid
import os
from pathlib import Path
from config import settings
from database import get_db
from models import Receipt, ReceiptStatus
from schemas import UploadResponse, StatusResponse, PaginatedReceipts, ReceiptResponse
from background.jobs import process_receipt_job
from database import async_session

router = APIRouter()


@router.post("/upload", response_model=UploadResponse)
async def upload_receipt(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db)
):
    # Validate file type
    allowed_extensions = {".jpg", ".jpeg", ".png", ".webp", ".heic"}
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Invalid file type. Only image files are allowed.")

    # Validate file size
    max_size = settings.max_image_size_mb * 1024 * 1024
    file_content = await file.read()
    if len(file_content) > max_size:
        raise HTTPException(status_code=400, detail=f"File too large. Maximum size is {settings.max_image_size_mb}MB.")

    # Generate unique filename
    unique_id = str(uuid.uuid4())
    unique_filename = f"{unique_id}_{file.filename}"
    upload_path = os.path.join(settings.upload_dir, unique_filename)

    # Ensure upload directory exists
    os.makedirs(settings.upload_dir, exist_ok=True)

    # Save file
    with open(upload_path, "wb") as f:
        f.write(file_content)

    # Create receipt record
    receipt = Receipt(
        filename=file.filename,
        upload_path=upload_path,
        status=ReceiptStatus.pending
    )
    db.add(receipt)
    await db.commit()
    await db.refresh(receipt)

    # Enqueue background job
    background_tasks.add_task(process_receipt_job, receipt.id, async_session)

    return UploadResponse(
        receipt_id=receipt.id,
        status="pending",
        message="Processing started"
    )


@router.get("/{receipt_id}/status", response_model=StatusResponse)
async def get_receipt_status(receipt_id: str, db: AsyncSession = Depends(get_db)):
    try:
        receipt_uuid = uuid.UUID(receipt_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid receipt ID format")

    result = await db.execute(select(Receipt).where(Receipt.id == receipt_uuid))
    receipt = result.scalar_one_or_none()
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")

    return StatusResponse(
        status=receipt.status,
        error_message=receipt.error_message
    )


@router.get("/", response_model=PaginatedReceipts)
async def list_receipts(skip: int = 0, limit: int = 10, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Receipt).order_by(Receipt.created_at.desc()).offset(skip).limit(limit)
    )
    receipts = result.scalars().all()

    total_result = await db.execute(select(func.count(Receipt.id)))
    total = total_result.scalar()

    return PaginatedReceipts(
        receipts=[ReceiptResponse.model_validate(receipt) for receipt in receipts],
        total=total,
        skip=skip,
        limit=limit
    )
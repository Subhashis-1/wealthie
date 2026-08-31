import asyncio
import logging
import traceback
from uuid import UUID

from sqlalchemy import select, update

from config import settings
from database import async_session
from models import Receipt, ReceiptStatus, Transaction, TransactionCategory
from services.gemini_service import parse_receipt
from services.image_service import preprocess_image

logger = logging.getLogger("wealthie.jobs")
job_semaphore = asyncio.Semaphore(settings.max_concurrent_jobs)


async def process_receipt_job(receipt_id: UUID, session_factory=async_session):
    """Process one receipt with bounded concurrency and explicit state transitions."""
    async with job_semaphore:
        async with session_factory() as db:
            try:
                await db.execute(
                    update(Receipt)
                    .where(Receipt.id == receipt_id)
                    .values(status=ReceiptStatus.processing, error_message=None)
                )
                await db.commit()

                result = await db.execute(select(Receipt).where(Receipt.id == receipt_id))
                receipt = result.scalar_one_or_none()
                if receipt is None:
                    logger.warning("receipt %s disappeared before processing", receipt_id)
                    return

                with open(receipt.upload_path, "rb") as image_file:
                    image_bytes = image_file.read()

                processed_bytes = preprocess_image(image_bytes)
                parsed = await parse_receipt(processed_bytes)

                transaction = Transaction(
                    receipt_id=receipt_id,
                    merchant_name=parsed.merchant_name,
                    date=parsed.date,
                    total_amount=parsed.total_amount,
                    currency=parsed.currency,
                    category=TransactionCategory(parsed.category),
                    line_items=[item.model_dump() for item in parsed.line_items],
                    tax_amount=parsed.tax_amount,
                    payment_method=parsed.payment_method,
                    confidence_score=parsed.confidence_score,
                    raw_gemini_response=parsed.model_dump_json(),
                )
                db.add(transaction)
                receipt.status = ReceiptStatus.completed
                await db.commit()
                logger.info("receipt %s completed", receipt_id)

            except Exception as exc:
                await db.rollback()
                error_msg = f"{exc}\n{traceback.format_exc()}"
                logger.exception("receipt %s failed", receipt_id)
                await db.execute(
                    update(Receipt)
                    .where(Receipt.id == receipt_id)
                    .values(status=ReceiptStatus.failed, error_message=error_msg)
                )
                await db.commit()

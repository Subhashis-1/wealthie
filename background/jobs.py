import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
import traceback
import logging
from uuid import UUID
from config import settings
from models import Receipt, ReceiptStatus, Transaction, TransactionCategory
from services.gemini_service import parse_receipt
from services.image_service import preprocess_image
from database import async_session

logger = logging.getLogger(__name__)

# Global semaphore to limit concurrent jobs
semaphore = asyncio.Semaphore(settings.max_concurrent_jobs)

async def process_receipt_job(receipt_id: UUID, session_factory):
    async with semaphore:
        async with session_factory() as db:
            try:
                # Update status to processing
                await db.execute(
                    update(Receipt)
                    .where(Receipt.id == receipt_id)
                    .values(status=ReceiptStatus.processing)
                )
                await db.commit()

                # Get receipt
                result = await db.execute(select(Receipt).where(Receipt.id == receipt_id))
                receipt = result.scalar_one()

                # Read image file
                with open(receipt.upload_path, "rb") as f:
                    image_bytes = f.read()

                # Preprocess image
                processed_bytes = preprocess_image(image_bytes)

                # Parse with Gemini
                parsed = await parse_receipt(processed_bytes)

                # Create transaction
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
                    raw_gemini_response=str(parsed.model_dump_json())
                )
                db.add(transaction)

                # Update receipt status to completed
                await db.execute(
                    update(Receipt)
                    .where(Receipt.id == receipt_id)
                    .values(status=ReceiptStatus.completed)
                )
                await db.commit()

                logger.info(f"Successfully processed receipt {receipt_id}")

            except Exception as e:
                error_msg = f"{str(e)}\n{traceback.format_exc()}"
                logger.error(f"Failed to process receipt {receipt_id}: {error_msg}")

                # Update receipt status to failed
                async with session_factory() as db:
                    await db.execute(
                        update(Receipt)
                        .where(Receipt.id == receipt_id)
                        .values(status=ReceiptStatus.failed, error_message=error_msg)
                    )
                    await db.commit()
            finally:
                # Ensure semaphore is released
                pass
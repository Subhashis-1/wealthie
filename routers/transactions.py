from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from typing import Literal, Optional
from datetime import date
import uuid
from models import Transaction, TransactionCategory
from schemas import PaginatedTransactions, TransactionResponse, TransactionUpdate
from dependencies import get_api_key
from database import get_db

router = APIRouter()


@router.get("/", response_model=PaginatedTransactions)
async def list_transactions(
    category: Optional[TransactionCategory] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    merchant_name: Optional[str] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    sort_by: str = "created_at",
    sort_order: Literal["asc", "desc"] = "desc",
    db: AsyncSession = Depends(get_db)
):
    query = select(Transaction).where(Transaction.is_deleted == False)

    if category:
        query = query.where(Transaction.category == category)
    if date_from:
        query = query.where(Transaction.date >= date_from)
    if date_to:
        query = query.where(Transaction.date <= date_to)
    if merchant_name:
        query = query.where(Transaction.merchant_name.ilike(f"%{merchant_name}%"))
    if min_amount is not None:
        query = query.where(Transaction.total_amount >= min_amount)
    if max_amount is not None:
        query = query.where(Transaction.total_amount <= max_amount)

    # Keep ordering to transaction fields exposed by the API.
    sortable_columns = {
        "date", "merchant_name", "total_amount", "created_at",
        "category", "confidence_score",
    }
    if sort_by not in sortable_columns:
        raise HTTPException(status_code=422, detail="Unsupported sort field")
    sort_column = getattr(Transaction, sort_by)
    if sort_order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    count_query = query.with_only_columns(func.count(Transaction.id)).order_by(None).offset(None).limit(None)
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    result = await db.execute(query.offset(skip).limit(limit))
    transactions = result.scalars().all()

    return PaginatedTransactions(
        transactions=[TransactionResponse.model_validate(t) for t in transactions],
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(transaction_id: str, db: AsyncSession = Depends(get_db)):
    try:
        trans_uuid = uuid.UUID(transaction_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid transaction ID format")

    result = await db.execute(
        select(Transaction).where(
            and_(Transaction.id == trans_uuid, Transaction.is_deleted == False)
        )
    )
    transaction = result.scalar_one_or_none()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    return TransactionResponse.model_validate(transaction)


@router.put("/{transaction_id}", response_model=TransactionResponse)
async def update_transaction(
    transaction_id: str,
    update_data: TransactionUpdate,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    try:
        trans_uuid = uuid.UUID(transaction_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid transaction ID format")

    result = await db.execute(
        select(Transaction).where(
            and_(Transaction.id == trans_uuid, Transaction.is_deleted == False)
        )
    )
    transaction = result.scalar_one_or_none()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    # Update fields
    for field, value in update_data.model_dump(exclude_unset=True).items():
        setattr(transaction, field, value)

    await db.commit()
    await db.refresh(transaction)

    return TransactionResponse.model_validate(transaction)


@router.delete("/{transaction_id}")
async def delete_transaction(
    transaction_id: str,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    try:
        trans_uuid = uuid.UUID(transaction_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid transaction ID format")

    result = await db.execute(
        select(Transaction).where(
            and_(Transaction.id == trans_uuid, Transaction.is_deleted == False)
        )
    )
    transaction = result.scalar_one_or_none()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    transaction.is_deleted = True
    await db.commit()

    return {"message": "Transaction deleted successfully"}

from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, extract
from typing import Optional
from datetime import date
import csv
import json
import io
from models import Transaction
from schemas import SummaryResponse
from database import get_db

router = APIRouter()


@router.get("/summary", response_model=SummaryResponse)
async def get_summary(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(Transaction).where(Transaction.is_deleted == False)

    if date_from:
        query = query.where(Transaction.date >= date_from)
    if date_to:
        query = query.where(Transaction.date <= date_to)

    result = await db.execute(query)
    transactions = result.scalars().all()

    if not transactions:
        return SummaryResponse(
            total_spent=0.0,
            transaction_count=0,
            by_category={},
            by_month={},
            top_merchants=[],
            avg_transaction=0.0,
            date_range={"from": date_from.isoformat() if date_from else "", "to": date_to.isoformat() if date_to else ""}
        )

    total_spent = sum(t.total_amount for t in transactions)
    transaction_count = len(transactions)
    avg_transaction = total_spent / transaction_count

    # By category
    by_category = {}
    for t in transactions:
        cat = t.category.value
        by_category[cat] = by_category.get(cat, 0) + t.total_amount

    # By month
    by_month = {}
    for t in transactions:
        month_key = f"{t.date.year}-{t.date.month:02d}"
        by_month[month_key] = by_month.get(month_key, 0) + t.total_amount

    # Top merchants
    merchant_totals = {}
    merchant_counts = {}
    for t in transactions:
        merchant_totals[t.merchant_name] = merchant_totals.get(t.merchant_name, 0) + t.total_amount
        merchant_counts[t.merchant_name] = merchant_counts.get(t.merchant_name, 0) + 1

    top_merchants = [
        {"name": name, "total": total, "count": merchant_counts[name]}
        for name, total in sorted(merchant_totals.items(), key=lambda x: x[1], reverse=True)[:10]
    ]

    return SummaryResponse(
        total_spent=round(total_spent, 2),
        transaction_count=transaction_count,
        by_category={k: round(v, 2) for k, v in by_category.items()},
        by_month={k: round(v, 2) for k, v in by_month.items()},
        top_merchants=top_merchants,
        avg_transaction=round(avg_transaction, 2),
        date_range={"from": date_from.isoformat() if date_from else min(t.date for t in transactions).isoformat(), "to": date_to.isoformat() if date_to else max(t.date for t in transactions).isoformat()}
    )


@router.get("/export/csv")
async def export_csv(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(Transaction).where(Transaction.is_deleted == False)

    if date_from:
        query = query.where(Transaction.date >= date_from)
    if date_to:
        query = query.where(Transaction.date <= date_to)

    result = await db.execute(query)
    transactions = result.scalars().all()

    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["date", "merchant", "category", "amount", "currency", "payment_method", "confidence_score"])

    for t in transactions:
        writer.writerow([
            t.date.isoformat(),
            t.merchant_name,
            t.category.value,
            t.total_amount,
            t.currency,
            t.payment_method or "",
            t.confidence_score
        ])

    output.seek(0)
    response = StreamingResponse(
        io.StringIO(output.getvalue()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=transactions.csv"}
    )
    return response


@router.get("/export/json")
async def export_json(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(Transaction).where(Transaction.is_deleted == False)

    if date_from:
        query = query.where(Transaction.date >= date_from)
    if date_to:
        query = query.where(Transaction.date <= date_to)

    result = await db.execute(query)
    transactions = result.scalars().all()

    data = [
        {
            "id": str(t.id),
            "receipt_id": str(t.receipt_id),
            "merchant_name": t.merchant_name,
            "date": t.date.isoformat(),
            "total_amount": t.total_amount,
            "currency": t.currency,
            "category": t.category.value,
            "line_items": t.line_items,
            "tax_amount": t.tax_amount,
            "payment_method": t.payment_method,
            "confidence_score": t.confidence_score,
            "raw_gemini_response": t.raw_gemini_response,
            "created_at": t.created_at.isoformat()
        }
        for t in transactions
    ]

    json_str = json.dumps(data, indent=2)
    response = StreamingResponse(
        io.StringIO(json_str),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=transactions.json"}
    )
    return response
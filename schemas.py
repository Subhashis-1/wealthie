from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import date, datetime
from uuid import UUID
from models import ReceiptStatus, TransactionCategory


class ReceiptBase(BaseModel):
    filename: str
    upload_path: str
    status: ReceiptStatus
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
        "json_encoders": {datetime: lambda v: v.isoformat()},
    }


class ReceiptCreate(BaseModel):
    filename: str
    upload_path: str

    model_config = {"json_schema_extra": {"examples": [{"filename": "receipt.jpg", "upload_path": "/uploads/uuid_receipt.jpg"}]}}


class ReceiptResponse(BaseModel):
    id: UUID
    filename: str
    upload_path: str
    status: ReceiptStatus
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {"examples": [{"id": "123e4567-e89b-12d3-a456-426614174000", "filename": "receipt.jpg", "upload_path": "/uploads/uuid_receipt.jpg", "status": "pending", "created_at": "2023-01-01T00:00:00", "updated_at": "2023-01-01T00:00:00"}]},
    }


class TransactionBase(BaseModel):
    receipt_id: UUID
    merchant_name: str
    date: date
    total_amount: float
    currency: str = "USD"
    category: TransactionCategory
    line_items: List[Dict[str, Any]]
    tax_amount: Optional[float] = None
    payment_method: Optional[str] = None
    confidence_score: float
    raw_gemini_response: str
    created_at: datetime

    model_config = {
        "from_attributes": True,
        "json_encoders": {datetime: lambda v: v.isoformat()},
    }


class TransactionResponse(BaseModel):
    id: UUID
    receipt_id: UUID
    merchant_name: str
    date: date
    total_amount: float
    currency: str
    category: TransactionCategory
    line_items: List[Dict[str, Any]]
    tax_amount: Optional[float] = None
    payment_method: Optional[str] = None
    confidence_score: float
    raw_gemini_response: str
    created_at: datetime

    model_config = {
        "from_attributes": True,
        "json_encoders": {datetime: lambda v: v.isoformat()},
        "json_schema_extra": {"examples": [{"id": "123e4567-e89b-12d3-a456-426614174000", "receipt_id": "123e4567-e89b-12d3-a456-426614174000", "merchant_name": "Walmart", "date": "2023-01-01", "total_amount": 50.0, "currency": "USD", "category": "Groceries", "line_items": [{"name": "Milk", "qty": 1.0, "unit_price": 3.5}], "confidence_score": 0.95, "raw_gemini_response": "{}", "created_at": "2023-01-01T00:00:00"}]},
    }


class TransactionUpdate(BaseModel):
    category: Optional[TransactionCategory] = None
    merchant_name: Optional[str] = None
    date: Optional[date] = None
    total_amount: Optional[float] = None
    payment_method: Optional[str] = None

    model_config = {"json_schema_extra": {"examples": [{"category": "Food & Dining", "merchant_name": "Updated Merchant", "date": "2023-01-02", "total_amount": 60.0, "payment_method": "Credit Card"}]}}


class UploadResponse(BaseModel):
    receipt_id: UUID
    status: str
    message: str

    model_config = {"json_schema_extra": {"examples": [{"receipt_id": "123e4567-e89b-12d3-a456-426614174000", "status": "pending", "message": "Processing started"}]}}


class StatusResponse(BaseModel):
    status: ReceiptStatus
    error_message: Optional[str] = None

    model_config = {"json_schema_extra": {"examples": [{"status": "completed"}, {"status": "failed", "error_message": "Parsing error"}]}}


class PaginatedReceipts(BaseModel):
    receipts: List[ReceiptResponse]
    total: int
    skip: int
    limit: int

    model_config = {"json_schema_extra": {"examples": [{"receipts": [], "total": 0, "skip": 0, "limit": 10}]}}


class PaginatedTransactions(BaseModel):
    transactions: List[TransactionResponse]
    total: int
    skip: int
    limit: int

    model_config = {"json_schema_extra": {"examples": [{"transactions": [], "total": 0, "skip": 0, "limit": 10}]}}


class SummaryResponse(BaseModel):
    total_spent: float
    transaction_count: int
    by_category: Dict[str, float]
    by_month: Dict[str, float]
    top_merchants: List[Dict[str, Any]]
    avg_transaction: float
    date_range: Dict[str, str]

    model_config = {"json_schema_extra": {"examples": [{"total_spent": 1000.0, "transaction_count": 20, "by_category": {"Food & Dining": 500.0}, "by_month": {"2023-01": 500.0}, "top_merchants": [{"name": "Walmart", "total": 200.0, "count": 5}], "avg_transaction": 50.0, "date_range": {"from": "2023-01-01", "to": "2023-12-31"}}]}}


class LineItem(BaseModel):
    name: str
    qty: float
    unit_price: float

    model_config = {"json_schema_extra": {"examples": [{"name": "Apple", "qty": 2.0, "unit_price": 1.5}]}}


class ParsedReceipt(BaseModel):
    merchant_name: str
    date: str
    total_amount: float
    currency: str
    tax_amount: Optional[float] = None
    payment_method: Optional[str] = None
    category: str
    line_items: List[LineItem]
    confidence_score: float

    model_config = {"json_schema_extra": {"examples": [{"merchant_name": "Walmart", "date": "2023-01-01", "total_amount": 50.0, "currency": "USD", "category": "Groceries", "line_items": [{"name": "Milk", "qty": 1.0, "unit_price": 3.5}], "confidence_score": 0.95}]}} 
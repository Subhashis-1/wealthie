from sqlalchemy import Column, String, Float, Date, DateTime, Text, JSON, Boolean, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
import uuid
from datetime import datetime
import enum

Base = declarative_base()


class ReceiptStatus(enum.Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class TransactionCategory(enum.Enum):
    FOOD_DINING = "Food & Dining"
    GROCERIES = "Groceries"
    TRANSPORTATION = "Transportation"
    SHOPPING = "Shopping"
    ENTERTAINMENT = "Entertainment"
    HEALTHCARE = "Healthcare"
    UTILITIES = "Utilities"
    TRAVEL = "Travel"
    BUSINESS = "Business"
    OTHER = "Other"


class Receipt(Base):
    __tablename__ = "receipts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String, nullable=False)
    upload_path = Column(String, nullable=False)
    status = Column(Enum(ReceiptStatus), default=ReceiptStatus.pending)
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    receipt_id = Column(UUID(as_uuid=True), ForeignKey("receipts.id"), nullable=False)
    merchant_name = Column(String, nullable=False)
    date = Column(Date, nullable=False)
    total_amount = Column(Float, nullable=False)
    currency = Column(String, default="USD")
    category = Column(Enum(TransactionCategory), nullable=False)
    line_items = Column(JSON, nullable=False)
    tax_amount = Column(Float, nullable=True)
    payment_method = Column(String, nullable=True)
    confidence_score = Column(Float, nullable=False)
    raw_gemini_response = Column(Text, nullable=False)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
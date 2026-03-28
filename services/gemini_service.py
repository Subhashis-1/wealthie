import google.generativeai as genai
import base64
import json
from config import settings
from schemas import ParsedReceipt, LineItem
from typing import Optional

# Initialize Gemini
genai.configure(api_key=settings.gemini_api_key)
model = genai.GenerativeModel('gemini-2.0-flash')

SYSTEM_PROMPT = """You are an expert receipt parser. Analyze the receipt image and extract ALL of the following in valid JSON only. No markdown, no explanation — raw JSON only.

{
  "merchant_name": "string",
  "date": "YYYY-MM-DD",
  "total_amount": float,
  "currency": "USD",
  "tax_amount": float or null,
  "payment_method": "string or null",
  "category": "one of: Food & Dining, Groceries, Transportation, Shopping, Entertainment, Healthcare, Utilities, Travel, Business, Other",
  "line_items": [
    {"name": "string", "qty": float, "unit_price": float}
  ],
  "confidence_score": float between 0.0 and 1.0
}

If any field is not visible, use null. Never return anything except the JSON object."""

async def parse_receipt(image_bytes: bytes) -> ParsedReceipt:
    try:
        # Convert image to base64
        image_b64 = base64.b64encode(image_bytes).decode('utf-8')

        # Create content for Gemini
        response = model.generate_content([
            SYSTEM_PROMPT,
            {"mime_type": "image/jpeg", "data": image_b64}
        ])

        raw_response = response.text.strip()

        # Strip any accidental markdown fences
        if raw_response.startswith('```json'):
            raw_response = raw_response[7:]
        if raw_response.endswith('```'):
            raw_response = raw_response[:-3]
        raw_response = raw_response.strip()

        try:
            data = json.loads(raw_response)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse Gemini response as JSON: {e}. Response: {raw_response}")

        # Validate required fields
        required_fields = ["merchant_name", "date", "total_amount", "currency", "category", "line_items", "confidence_score"]
        for field in required_fields:
            if field not in data or data[field] is None:
                raise ValueError(f"Missing required field: {field}")

        # Validate category
        valid_categories = ["Food & Dining", "Groceries", "Transportation", "Shopping", "Entertainment", "Healthcare", "Utilities", "Travel", "Business", "Other"]
        if data["category"] not in valid_categories:
            data["category"] = "Other"

        # Convert line_items to proper format
        line_items = []
        for item in data["line_items"]:
            if isinstance(item, dict) and "name" in item and "qty" in item and "unit_price" in item:
                line_items.append(LineItem(
                    name=str(item["name"]),
                    qty=float(item["qty"]),
                    unit_price=float(item["unit_price"])
                ))

        return ParsedReceipt(
            merchant_name=str(data["merchant_name"]),
            date=str(data["date"]),
            total_amount=float(data["total_amount"]),
            currency=str(data["currency"]),
            tax_amount=float(data["tax_amount"]) if data.get("tax_amount") is not None else None,
            payment_method=str(data["payment_method"]) if data.get("payment_method") else None,
            category=str(data["category"]),
            line_items=line_items,
            confidence_score=float(data["confidence_score"])
        )

    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "quota" in error_msg.lower():
            raise ValueError("Gemini API quota exceeded. Please check your Google AI billing/plan or wait for quota reset. Visit https://ai.google.dev/gemini-api/docs/rate-limits for more info.")
        elif "403" in error_msg or "permission" in error_msg.lower():
            raise ValueError("Gemini API access denied. Please check your API key permissions.")
        else:
            raise ValueError(f"Gemini API error: {error_msg}")
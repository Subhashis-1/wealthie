# Wealthie - AI-Powered Financial Management Platform

Wealthie is a complete financial management platform that uses Google's Gemini Vision API to automatically extract transaction data from receipt images. Built with FastAPI, SQLAlchemy, and a modern vanilla JavaScript frontend.

## Features

- **AI Receipt Processing**: Upload receipt images and let Gemini AI extract merchant, amount, date, and categorize transactions
- **Transaction Management**: View, filter, sort, and edit transactions
- **Financial Analytics**: Dashboard with spending summaries, category breakdowns, and charts
- **Data Export**: Export transactions to CSV or JSON
- **Background Processing**: Asynchronous receipt processing with concurrency limits
- **Modern UI**: Dark-themed, responsive dashboard with drag-and-drop uploads

## Tech Stack

- **Backend**: Python 3.11+, FastAPI, Async SQLAlchemy, SQLite
- **AI**: Google Gemini Vision API
- **Image Processing**: Pillow
- **Frontend**: Vanilla HTML/CSS/JS with Chart.js
- **Background Jobs**: FastAPI BackgroundTasks + asyncio

## Setup

1. **Clone and Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Get a Gemini API Key**:
   - Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Create a new API key
   - **Important**: Free tier API keys have quota limits. For production use, consider a paid plan.
   - Copy the key

3. **Configure Environment**:
   ```bash
   cp .env.example .env
   # Edit .env and add your GEMINI_API_KEY and API_KEY
   ```

4. **Run the Application**:
   ```bash
   uvicorn main:app --reload
   ```

5. **Open in Browser**:
   - Navigate to `http://localhost:8000`
   - The frontend will load automatically

## API Endpoints

### Receipts
- `POST /api/receipts/upload` - Upload receipt image for processing
- `GET /api/receipts/{id}/status` - Check processing status
- `GET /api/receipts/` - List all receipts (paginated)

### Transactions
- `GET /api/transactions/` - List transactions with filtering
- `GET /api/transactions/{id}` - Get transaction details
- `PUT /api/transactions/{id}` - Update transaction (requires API key)
- `DELETE /api/transactions/{id}` - Soft delete transaction (requires API key)

### Reports
- `GET /api/reports/summary` - Financial summary and analytics
- `GET /api/reports/export/csv` - Export transactions as CSV
- `GET /api/reports/export/json` - Export transactions as JSON

## API Key Authentication

Write operations (PUT/DELETE on transactions) require an `X-API-Key` header with the value from your `.env` file.

## Supported Image Formats

- JPEG, PNG, WebP (recommended)
- Maximum file size: 10MB (configurable)
- Images are automatically optimized before sending to Gemini

## Categories

Transactions are automatically categorized into:
- Food & Dining
- Groceries
- Transportation
- Shopping
- Entertainment
- Healthcare
- Utilities
- Travel
- Business
- Other

## Development

The application uses:
- Async SQLAlchemy with aiosqlite for database operations
- Pydantic for data validation
- Background tasks for receipt processing
- Semaphore-based concurrency control
- Comprehensive error handling and logging

## Troubleshooting

### Receipt Processing Fails
- **Quota Exceeded**: Free Gemini API keys have rate limits. Check your usage at [Google AI Studio](https://makersuite.google.com/app/apikey)
- **Invalid API Key**: Ensure your `GEMINI_API_KEY` in `.env` is correct
- **Model Not Available**: The app uses `gemini-2.0-flash`. If issues persist, check available models

### Upload Issues
- **File Type Rejected**: Only image files (JPG, PNG, WebP) are accepted
- **File Too Large**: Maximum size is 10MB (configurable in settings)
- **Server Errors**: Check server logs for detailed error messages

### Database Issues
- **Tables Not Created**: The app creates tables automatically on startup
- **Permission Errors**: Ensure write access to the working directory

## License

This project is open source. Feel free to use and modify as needed.

---

![Wealthie Dashboard](https://via.placeholder.com/800x400/0a0a0a/00d4aa?text=Wealthie+Dashboard+Screenshot)
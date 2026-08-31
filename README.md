# Wealthie

**AI-assisted receipt ingestion and personal finance analytics built with FastAPI.**

Wealthie turns receipt images into structured transactions, stores the normalized data, and exposes APIs for transaction management and financial reporting.

> **Project status:** actively developed. The repository is a modified derivative of the open-source [ARTHA backend](https://github.com/nilayDawn/ARTHA_backend). See [`NOTICE.md`](./NOTICE.md) for attribution and licensing information.

## Architecture

```text
Receipt Image
     |
     v
Upload API -----> Receipt Record
     |
     v
Bounded Background Worker
     |
     +--> Image Preprocessing
     |
     +--> Gemini Vision Extraction
     |
     v
Validated Transaction
     |
     +--> Transaction APIs
     +--> Analytics / Reports
     +--> CSV / JSON Export
```

## Core capabilities

- **Receipt ingestion** — validates uploaded images and stores processing state.
- **AI extraction** — uses Gemini Vision to extract merchant, date, amount, tax, payment method, categories, and line items.
- **Bounded concurrency** — receipt jobs are processed asynchronously with a configurable concurrency limit.
- **Transaction management** — query, filter, update, and soft-delete financial transactions.
- **Reporting** — spending summaries and machine-readable CSV/JSON exports.
- **Image optimization** — preprocesses receipt images before external AI calls.
- **Operational visibility** — request timing headers, structured application logging, and a `/health` endpoint.

## Technology

| Layer | Technology |
|---|---|
| API | Python, FastAPI, Uvicorn |
| Persistence | SQLAlchemy 2.x, SQLite/aiosqlite |
| AI | Google Gemini Vision API |
| Image processing | Pillow |
| Validation | Pydantic / pydantic-settings |
| Frontend | HTML, CSS, JavaScript, Chart.js |
| Async processing | asyncio + FastAPI background processing |

## Local setup

### 1. Create an environment

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
```

### 2. Configure secrets

```bash
cp .env.example .env
```

Set at least:

```env
GEMINI_API_KEY=your_gemini_api_key
API_KEY=your_application_api_key
DATABASE_URL=sqlite+aiosqlite:///./wealthie.db
UPLOAD_DIR=./uploads
MAX_IMAGE_SIZE_MB=10
MAX_CONCURRENT_JOBS=5
ALLOWED_ORIGINS=http://localhost:8000
LOG_LEVEL=INFO
```

Never commit `.env` or real API credentials.

### 3. Run

```bash
uvicorn main:app --reload
```

Open `http://localhost:8000` and API documentation at `http://localhost:8000/docs`.

## API surface

### System

- `GET /health` — service health check

### Receipts

- `POST /api/receipts/upload` — upload a receipt for asynchronous processing
- `GET /api/receipts/{id}/status` — inspect processing state
- `GET /api/receipts/` — list receipts

### Transactions

- `GET /api/transactions/` — query transactions
- `GET /api/transactions/{id}` — retrieve a transaction
- `PUT /api/transactions/{id}` — update a transaction
- `DELETE /api/transactions/{id}` — soft-delete a transaction

### Reports

- `GET /api/reports/summary` — aggregate financial metrics
- `GET /api/reports/export/csv` — export transaction data
- `GET /api/reports/export/json` — export transaction data as JSON

## Engineering decisions

### Why bounded asynchronous processing?

Receipt extraction involves an external AI call, so processing it inline with the upload request would unnecessarily increase request latency. Wealthie separates ingestion from extraction and uses a semaphore to prevent unbounded concurrent API calls.

### Why preprocess images?

Receipt photos can contain unnecessary resolution and metadata. Normalizing the image before the AI request reduces payload size and makes extraction more predictable.

### Why keep processing state?

A receipt moves through explicit states (`pending`, `processing`, `completed`, or `failed`). This makes asynchronous work observable and allows the client to poll for completion without blocking the upload request.

## Development roadmap

- [ ] PostgreSQL production profile
- [ ] Redis-backed job queue
- [ ] Retry policy with exponential backoff
- [ ] Idempotency keys for receipt uploads
- [ ] Automated API and worker tests
- [ ] Containerized deployment
- [ ] Per-user authentication and data isolation
- [ ] Observability metrics for extraction latency and failure rate

## Attribution & license

Wealthie is a modified derivative of **ARTHA backend** by `nilayDawn`:

https://github.com/nilayDawn/ARTHA_backend

The upstream project is licensed under **GNU GPL v3.0**. This derivative retains the applicable GPL terms. See [`NOTICE.md`](./NOTICE.md) for the derivative-work notice.

## Disclaimer

Wealthie is a software project for financial-data organization and experimentation. It does not provide investment, tax, accounting, or other professional financial advice.

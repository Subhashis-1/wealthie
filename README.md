# Wealthie

Wealthie is a personal finance dashboard for turning receipt photos into an organized, searchable record of everyday spending. Upload a receipt, review the extracted transaction, explore category and monthly summaries, and export your records when you need them.

The app is built for local development and personal experimentation. Receipt images are sent to Google Gemini for extraction when a Gemini API key is configured. Wealthie is not a financial, tax, or accounting adviser.

## What you can do

- Upload JPG, PNG, WebP, and HEIC receipt images with drag and drop or the file picker.
- Track receipt processing through pending, processing, completed, and failed states.
- Extract merchant, purchase date, total, category, tax, payment method, line items, and confidence metadata.
- Review and edit a transaction's merchant, date, amount, and category.
- Search and filter the transaction history by merchant, category, and date range.
- Compare spending over time and across categories.
- Export transaction records as CSV or JSON.
- Keep receipt records and transaction data in SQLite for a simple local setup.

## Dashboard

The Wealthie interface is a responsive personal finance workspace with a spending snapshot, monthly and category charts, a paginated transaction table, and a receipt inbox. The interface is served by FastAPI from `static/index.html`; Chart.js renders the charts in the browser.

## How it works

```text
Receipt image
     |
     v
FastAPI upload endpoint ---> SQLite receipt record
     |                            |
     |                       Background task
     |                            |
     +----------------------> Image preparation
                                  |
                             Gemini extraction
                                  |
                        Validated transaction
                           /              \
                          v                v
                 Transaction API     Reports and exports
                          \                /
                           v              v
                        Wealthie dashboard
```

The app uses FastAPI and SQLAlchemy's async API with SQLite by default. Receipt work runs as an in-process background task, with a configured concurrency limit. This keeps the setup straightforward for a single-user local app. It is not a durable queue for multi-instance or production workloads.

## Requirements

- Python 3.10 or newer
- A Google Gemini API key for receipt extraction

## Run locally

Create and activate an environment, then install the dependencies:

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

macOS or Linux:

```bash
source .venv/bin/activate
```

Install and configure:

```bash
pip install -r requirements.txt
```

Copy `.env.example` to `.env`:

```powershell
Copy-Item .env.example .env
```

```bash
cp .env.example .env
```

Edit `.env` and provide your credentials:

```env
GEMINI_API_KEY=your_gemini_api_key
API_KEY=generate_a_private_random_key

DATABASE_URL=sqlite+aiosqlite:///./wealthie.db
UPLOAD_DIR=./uploads
MAX_IMAGE_SIZE_MB=10
MAX_CONCURRENT_JOBS=5
ALLOWED_ORIGINS=http://localhost:8000
LOG_LEVEL=INFO
```

Start the app:

```bash
uvicorn main:app --reload
```

Open [http://localhost:8000](http://localhost:8000). Interactive API documentation is available at [http://localhost:8000/docs](http://localhost:8000/docs).

The database and uploaded receipt images are runtime data. They are excluded from Git by `.gitignore`.

## API overview

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/health` | Service health |
| `POST` | `/api/receipts/upload` | Upload a receipt image for processing |
| `GET` | `/api/receipts/{id}/status` | Read processing status |
| `GET` | `/api/receipts/` | List recent receipts |
| `GET` | `/api/transactions/` | List transactions with filters and sorting |
| `GET` | `/api/transactions/{id}` | Read a transaction |
| `PUT` | `/api/transactions/{id}` | Update transaction details |
| `DELETE` | `/api/transactions/{id}` | Soft-delete a transaction |
| `GET` | `/api/reports/summary` | Spending totals and category/month breakdowns |
| `GET` | `/api/reports/export/csv` | Download transactions as CSV |
| `GET` | `/api/reports/export/json` | Download transactions as JSON |

Updating or deleting a transaction requires the `X-API-Key` header to match `API_KEY` in `.env`. Wealthie asks for this key when you edit or remove a transaction and keeps it only in the current browser tab's session storage. Do not use the development configuration as a public, multi-user deployment. The app does not currently provide user accounts or per-user data isolation.

## Configuration

| Variable | Purpose |
|---|---|
| `GEMINI_API_KEY` | Enables Gemini receipt extraction |
| `API_KEY` | Protects transaction update and delete endpoints |
| `DATABASE_URL` | SQLAlchemy database URL; defaults to local SQLite |
| `UPLOAD_DIR` | Local receipt image directory |
| `MAX_IMAGE_SIZE_MB` | Maximum accepted image size |
| `MAX_CONCURRENT_JOBS` | Maximum in-process receipt jobs running together |
| `ALLOWED_ORIGINS` | Comma-separated browser origins accepted by CORS |
| `LOG_LEVEL` | Application log level |

## Project structure

```text
Wealthie/
├── background/       Receipt processing jobs
├── routers/          Receipt, transaction, and reporting APIs
├── services/         Gemini extraction and image preparation
├── static/           Wealthie dashboard
├── config.py         Environment-backed settings
├── database.py       Async SQLAlchemy engine and sessions
├── models.py         Receipt and transaction models
├── schemas.py        API request and response schemas
└── main.py           FastAPI application and route setup
```

## Attribution and license

This repository retains its existing derivative-work relationship to [ARTHA backend](https://github.com/nilayDawn/ARTHA_backend). The applicable upstream license is GNU GPL v3.0. See [`NOTICE.md`](./NOTICE.md) for the derivative-work notice and license details.

## Responsible use

Receipt images may contain personal or payment information. Store them carefully and review your Google Gemini terms before sending receipt data to the external extraction service. Wealthie is an organizer for personal records, not a substitute for professional financial advice.

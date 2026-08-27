# Backend — AI Revenue Recovery Agent

Minimal FastAPI + SQLite foundation for the revenue recovery platform.

## Stack

- Python 3.10+
- FastAPI
- SQLAlchemy
- SQLite

## Setup

```bash
cd backend
python -m venv .venv

# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# macOS / Linux
# source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env   # Windows
# cp .env.example .env   # macOS / Linux
```

## Run the API

From the `backend/` directory (with the virtualenv active):

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open interactive docs at http://127.0.0.1:8000/docs

## Health check

```bash
curl http://127.0.0.1:8000/health
```

Expected response:

```json
{
  "status": "ok",
  "service": "AI Revenue Recovery Agent",
  "message": "API is running"
}
```

## Run tests

From the `backend/` directory:

```bash
pytest -q
```

## Database

SQLite is configured via `DATABASE_URL` in `.env`.

Tables are created automatically on application startup:

- `customers`
- `recovery_cases`
- `events`
- `actions`

## Project layout

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   └── models.py
├── tests/
│   └── test_health.py
├── .env.example
├── requirements.txt
└── README.md
```

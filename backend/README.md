# LedgerLens Backend

FastAPI backend service for LedgerLens blockchain intelligence workstation.

## Phase 1 - Case Foundation

This implementation provides the foundational case management layer:

- Case creation API
- Case retrieval API
- Case update API
- PostgreSQL database integration
- Request validation
- Error handling

## Technology Stack

- **Framework**: FastAPI 0.104+
- **Database**: PostgreSQL + SQLAlchemy 2.0 (async)
- **Validation**: Pydantic v2
- **Testing**: pytest + pytest-asyncio

## Setup

### Prerequisites

- Python 3.11+
- PostgreSQL 15+ (or Supabase instance)

### Installation

```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### Configuration

Copy `.env.example` to `.env` and configure:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/ledgerlens
SECRET_KEY=your-secret-key-here
```

### Database Migration

Apply initial schema:

```bash
psql -U user -d ledgerlens -f ../migrations/001_initial_schema.sql
```

### Run

```bash
uvicorn app.main:app --reload --port 8000
```

API will be available at:
- http://localhost:8000
- API docs: http://localhost:8000/docs
- Redoc: http://localhost:8000/redoc

## API Endpoints

### Cases

- `POST /api/v1/cases` - Create case
- `GET /api/v1/cases/{case_id}` - Get case
- `PUT /api/v1/cases/{case_id}` - Update case
- `GET /api/v1/cases` - List cases

### Health

- `GET /health` - Health check

## Testing

```bash
pytest
```

## Project Structure

```
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       └── cases.py       # Case endpoints
│   ├── db/
│   │   ├── database.py        # Database connection
│   │   └── models.py          # SQLAlchemy models
│   ├── models/
│   │   └── schemas.py         # Pydantic schemas
│   ├── services/
│   │   └── case_service.py    # Business logic
│   ├── config.py              # Configuration
│   └── main.py                # FastAPI app
├── tests/                     # Test suite
├── requirements.txt           # Dependencies
└── README.md                  # This file
```

## Phase 1 Limitations

Authentication not yet implemented - uses mock investigator ID.

Future phases will add:
- JWT authentication
- Blockchain tracing
- Graph engine
- Risk scoring
- VASP attribution
- Frontend integration

## Database Schema

See `docs/DATA_MODEL.md` for complete schema documentation.

Phase 1 tables:
- `investigators`
- `cases`

## Security Notes

- Do NOT commit `.env` file
- Use strong `SECRET_KEY` in production
- Database credentials should be stored securely
- HTTPS required in production

## Development Standards

See `docs/DEVELOPMENT_STANDARDS.md` for:
- Code formatting (black, ruff)
- Type checking (mypy)
- Testing conventions
- Error handling patterns

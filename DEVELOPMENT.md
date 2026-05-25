# AlphaMomentum MVP — Development Guide

## Quick Start

### Prerequisites
- Python 3.14+
- Node.js 18+
- npm or yarn

### Installation

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Node dependencies
cd apps/web
npm install
cd ../..
```

### Running the MVP

**Terminal 1 — FastAPI Backend (Port 8000):**
```bash
cd apps/api
python -m uvicorn app.main:app --reload
```

Backend will initialize SQLite database at `./alphamomentum.db`

**Terminal 2 — Next.js Frontend (Port 3000):**
```bash
cd apps/web
npm run dev
```

Open http://localhost:3000 in your browser

## Project Structure

```
stock-market-app/
├── apps/
│   ├── api/                 # FastAPI backend
│   │   ├── app/
│   │   │   ├── main.py      # Entry point + scheduler
│   │   │   ├── models.py    # SQLAlchemy models
│   │   │   └── config.py    # Configuration
│   │   ├── database.py      # SQLite setup
│   │   ├── routers/         # API endpoints
│   │   └── tests/
│   │
│   └── web/                 # Next.js frontend
│       ├── app/
│       ├── components/
│       ├── lib/             # API client
│       └── package.json
│
├── services/                # Shared Python logic
│   ├── indicators.py
│   ├── scoring.py
│   ├── gates.py
│   ├── provider.py
│   └── models.py
│
├── requirements.txt         # Python dependencies
└── docs/                    # Documentation
```

## API Endpoints (To Be Implemented)

- `GET /health` — Health check
- `GET /api/recommendations/today` — Today's recommendations
- `GET /api/recommendations/{symbol}` — Single recommendation details
- `GET /api/pipeline/status` — Pipeline status

## Database

SQLite database file: `./alphamomentum.db`

Tables:
- `symbols` — Tradable equities
- `daily_bars` — OHLCV data
- `indicator_values` — Technical indicators
- `recommendations` — Daily recommendations
- `pipeline_runs` — Scheduled job execution records

## Environment Variables

### Backend (apps/api/.env)
```
DATABASE_URL=sqlite:///./alphamomentum.db
MARKET_DATA_PROVIDER=mock
PIPELINE_HOUR=16
PIPELINE_MINUTE=0
```

### Frontend (apps/web/.env.local)
```
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

## Testing

```bash
# Run Python tests
pytest apps/api/tests

# Run frontend tests (when added)
cd apps/web && npm test
```

## Next Steps

1. **Implement market data ingestion** (Epic 2)
2. **Add technical indicators** (Epic 3)
3. **Create scoring engine** (Epic 4)
4. **Build recommendation engine** (Epic 5)
5. **Implement API endpoints** (Epic 7)

## Troubleshooting

### Port 8000 already in use
```bash
# Find and kill process on port 8000
lsof -i :8000 | grep -v PID | awk '{print $2}' | xargs kill -9
```

### Port 3000 already in use
```bash
# Kill Next.js process
lsof -i :3000 | grep -v PID | awk '{print $2}' | xargs kill -9
```

### Database issues
```bash
# Reset database
rm ./alphamomentum.db
# Restart FastAPI to reinitialize
```

## Educational Disclaimer

This platform provides educational trade ideas only. It does not provide personalized financial advice. Always conduct your own research and consult with a qualified financial advisor before making trading decisions.

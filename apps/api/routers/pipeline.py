"""Pipeline status endpoints."""

import json
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from apps.api.app.models import PipelineRun
from apps.api.config import MARKET_DATA_PROVIDER
from apps.api.database import get_db
from services.pipeline import load_symbol_universe, run_market_data_pipeline, validate_data_freshness
from services.provider import get_provider

router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])


@router.get("/status")
async def pipeline_status(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Return the latest market-data publish-readiness state."""
    latest_run = db.query(PipelineRun).order_by(PipelineRun.started_at.desc()).first()
    symbols = load_symbol_universe()
    freshness = validate_data_freshness(db, symbols=symbols)

    return {
        "publish_ready": freshness.publish_ready,
        "checked_at": freshness.checked_at.isoformat(),
        "symbols_checked": freshness.symbols_checked,
        "latest_required_date": freshness.latest_required_date.isoformat(),
        "reasons": freshness.reasons,
        "latest_run": _serialize_pipeline_run(latest_run),
    }


@router.post("/run")
async def run_pipeline(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Run market-data ingestion with the configured provider."""
    provider = get_provider(MARKET_DATA_PROVIDER)
    latest_run = run_market_data_pipeline(db, provider)
    freshness = validate_data_freshness(db)

    return {
        "publish_ready": freshness.publish_ready,
        "reasons": freshness.reasons,
        "latest_run": _serialize_pipeline_run(latest_run),
    }


def _serialize_pipeline_run(run: PipelineRun | None) -> dict[str, Any] | None:
    if run is None:
        return None

    error_detail: Any = run.error_message
    if run.error_message:
        try:
            error_detail = json.loads(run.error_message)
        except json.JSONDecodeError:
            error_detail = run.error_message

    return {
        "run_id": run.run_id,
        "started_at": run.started_at.isoformat(),
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        "symbols_processed": run.symbols_processed,
        "recommendations_count": run.recommendations_count,
        "status": run.status,
        "error": error_detail,
    }

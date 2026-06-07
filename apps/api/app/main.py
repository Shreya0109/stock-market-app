from fastapi import FastAPI
from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler
import logging

from apps.api.routers.health import router as health_router
from apps.api.routers.pipeline import router as pipeline_router
from apps.api.config import MARKET_DATA_PROVIDER, PIPELINE_HOUR, PIPELINE_MINUTE
from apps.api.database import SessionLocal, init_db
from services.pipeline import run_market_data_pipeline
from services.provider import get_provider

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize scheduler
scheduler = BackgroundScheduler()


def run_daily_market_data_pipeline():
    """Scheduled market data ingestion job."""
    db = SessionLocal()
    try:
        provider = get_provider(MARKET_DATA_PROVIDER)
        run_market_data_pipeline(db, provider)
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for startup and shutdown."""
    # Startup
    logger.info("Initializing database...")
    init_db()

    logger.info("Starting background scheduler...")
    scheduler.start()

    scheduler.add_job(
        run_daily_market_data_pipeline,
        "cron",
        hour=PIPELINE_HOUR,
        minute=PIPELINE_MINUTE,
        id="daily_market_data_pipeline",
        replace_existing=True,
    )

    yield

    # Shutdown
    logger.info("Stopping background scheduler...")
    scheduler.shutdown()


app = FastAPI(title="AlphaMomentum API", lifespan=lifespan)
app.include_router(health_router)
app.include_router(pipeline_router)

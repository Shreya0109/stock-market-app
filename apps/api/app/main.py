from fastapi import FastAPI
from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler
import logging

from apps.api.routers.health import router as health_router
from apps.api.database import Base, engine, init_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize scheduler
scheduler = BackgroundScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for startup and shutdown."""
    # Startup
    logger.info("Initializing database...")
    init_db()

    logger.info("Starting background scheduler...")
    scheduler.start()

    # Add your scheduled jobs here
    # scheduler.add_job(run_daily_pipeline, "cron", hour=16, minute=0, id="daily_pipeline")

    yield

    # Shutdown
    logger.info("Stopping background scheduler...")
    scheduler.shutdown()


app = FastAPI(title="AlphaMomentum API", lifespan=lifespan)
app.include_router(health_router)

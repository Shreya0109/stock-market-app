from fastapi import FastAPI

from apps.backend.routers.health import router as health_router


app = FastAPI(title="AlphaMomentum API")
app.include_router(health_router)

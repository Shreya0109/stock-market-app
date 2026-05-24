from fastapi import FastAPI

from api.routers.health import router as health_router


app = FastAPI(title="AlphaMomentum API")
app.include_router(health_router)

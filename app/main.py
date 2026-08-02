from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import settings
from app.database import engine
from app.logger import get_logger
from app.controllers.auth_controller import router as auth_router
from app.controllers.device_controller import router as device_router
from app.controllers.vinyl_controller import router as vinyl_router
from app.controllers.resource_controller import router as resource_router
from app.controllers.play_controller import router as play_router

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Database connection established")
    except Exception as e:
        logger.error("Failed to connect to database", extra={"error": str(e)})
    yield


app = FastAPI(title="Orpheus API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.get("/ping")
async def ping():
    return {"status": "pong"}


app.include_router(auth_router)
app.include_router(device_router)
app.include_router(vinyl_router)
app.include_router(resource_router)
app.include_router(play_router)

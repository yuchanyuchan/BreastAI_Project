from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .api.chat import router as chat_router
from .api.sns import router as sns_router
from .core.db import Base, engine
from .core.scheduler import start_scheduler, stop_scheduler
from .db import models as sns_models  # noqa: F401 - registers SnsDraft with Base.metadata

STATIC_DIR = Path(__file__).resolve().parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(
    title="BreastAI API",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(chat_router)
app.include_router(sns_router)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def read_root() -> dict:
    return {
        "project": "BreastAI",
        "version": "0.1.0",
        "status": "running",
    }


@app.get("/health")
def health_check() -> dict:
    return {
        "status": "healthy",
    }

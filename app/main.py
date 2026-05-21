import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db import init_db
from app.routers import chat, embedding, rag, recommendation, search, tagging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s")
log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    log.info("initializing database schema")
    await init_db()
    yield


app = FastAPI(title="Digital Notes AI Core", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in settings.cors_allowed_origins.split(",")
        if origin.strip()
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

app.include_router(embedding.router)
app.include_router(search.router)
app.include_router(rag.router)
app.include_router(chat.router)
app.include_router(tagging.router)
app.include_router(recommendation.router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}

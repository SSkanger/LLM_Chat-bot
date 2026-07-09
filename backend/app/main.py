from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import chat, conversations, export, models, prompts, search, stats, users
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import setup_logging
from app.db.init_db import init_db


settings = get_settings()
setup_logging()

app = FastAPI(title=settings.app.name, debug=settings.app.debug)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)


@app.on_event("startup")
async def startup() -> None:
    init_db()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "name": settings.app.name}


app.include_router(users.router)
app.include_router(conversations.router)
app.include_router(chat.router)
app.include_router(prompts.router)
app.include_router(models.router)
app.include_router(search.router)
app.include_router(stats.router)
app.include_router(export.router)


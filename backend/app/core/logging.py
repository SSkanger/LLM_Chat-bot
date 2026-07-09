from __future__ import annotations

import sys

from loguru import logger

from app.core.config import BACKEND_DIR, get_settings


def setup_logging() -> None:
    settings = get_settings()
    log_dir = BACKEND_DIR / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    logger.remove()
    logger.add(sys.stdout, level=settings.log_level, serialize=True)
    logger.add(log_dir / "app.log", level=settings.log_level, serialize=True, rotation="10 MB")
    logger.add(log_dir / "error.log", level="ERROR", serialize=True, rotation="10 MB")


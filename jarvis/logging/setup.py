"""Structured, privacy-conscious application logging."""
from __future__ import annotations

import json
import logging
from pathlib import Path


def configure_logging(directory: Path, debug: bool = False) -> logging.Logger:
    directory.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("jarvis")
    if logger.handlers:
        return logger
    logger.setLevel(logging.DEBUG if debug else logging.INFO)
    handler = logging.FileHandler(directory / "jarvis.log", encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    return logger


def event(logger: logging.Logger, name: str, **fields: object) -> None:
    """Log event metadata; callers must not pass raw sensitive content."""
    logger.info(json.dumps({"event": name, **fields}, ensure_ascii=False))

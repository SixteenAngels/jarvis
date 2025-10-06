from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional


def get_logger(name: str = "jarvis", logfile: Optional[str] = "/workspace/data/logs/jarvis.log") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    Path("/workspace/data/logs").mkdir(parents=True, exist_ok=True)
    if logfile:
        handler = RotatingFileHandler(logfile, maxBytes=1_000_000, backupCount=5)
        formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    stream = logging.StreamHandler()
    stream.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    logger.addHandler(stream)
    return logger

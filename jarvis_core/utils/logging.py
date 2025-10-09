from __future__ import annotations

import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:  # noqa: D401
        data = {
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            data["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(data)


def get_logger(name: str = "jarvis", logfile: Optional[str] = "/workspace/data/logs/jarvis.log", json_stdout: bool = True) -> logging.Logger:
    """Return a configured logger with rotating file and JSON stdout.

    Args:
        name: Logger name.
        logfile: Path to logfile; if None, file logging is disabled.
        json_stdout: If True, write JSON logs to stdout; else plain text.
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    Path("/workspace/data/logs").mkdir(parents=True, exist_ok=True)
    if logfile:
        handler = RotatingFileHandler(logfile, maxBytes=1_000_000, backupCount=5)
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
        logger.addHandler(handler)
    stream = logging.StreamHandler()
    stream.setFormatter(JsonFormatter() if json_stdout else logging.Formatter("%(levelname)s: %(message)s"))
    logger.addHandler(stream)
    return logger

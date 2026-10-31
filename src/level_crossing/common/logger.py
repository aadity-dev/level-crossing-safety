"""Structured logging with component context and audit tracking."""

import logging
import json
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional


class StructuredLogFormatter(logging.Formatter):
    """Formats log records as structured JSON or readable contextual text."""

    def __init__(self, as_json: bool = False):
        super().__init__()
        self.as_json = as_json

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.now(timezone.utc).isoformat()
        component = getattr(record, "component", record.name)
        extra = getattr(record, "extra_data", {})

        payload: Dict[str, Any] = {
            "timestamp": timestamp,
            "level": record.levelname,
            "component": component,
            "message": record.getMessage(),
        }
        if extra:
            payload["context"] = extra

        if self.as_json:
            return json.dumps(payload)
        
        ctx_str = f" | {json.dumps(extra)}" if extra else ""
        return f"[{timestamp}] [{record.levelname:7}] [{component:16}] {record.getMessage()}{ctx_str}"


def get_logger(component_name: str, level: int = logging.INFO, as_json: bool = False) -> logging.Logger:
    """Creates or gets a component-scoped structured logger."""
    logger = logging.getLogger(f"level_crossing.{component_name}")
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredLogFormatter(as_json=as_json))
        logger.addHandler(handler)
        logger.setLevel(level)
        logger.propagate = False
    return logger

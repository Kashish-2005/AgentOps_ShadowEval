"""
Module: logging_config.py
Project: AgentOps-ShadowEval

This module configures the logging infrastructure for the application, providing 
support for structured JSON logging in production, human-readable logging in 
development, and request-id tracing across asynchronous tasks.
"""

import logging
import sys
import uuid
from contextvars import ContextVar
from typing import Any

from pythonjsonlogger import jsonlogger
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

# ContextVar to store the request ID for the duration of an async task
request_id_var: ContextVar[str] = ContextVar("request_id", default="n/a")


class RequestIDFilter(logging.Filter):
    """
    Logging filter that injects the current request_id from ContextVar 
    into every log record.
    """
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        return True


class SafeJsonFormatter(jsonlogger.JsonFormatter):
    """
    Custom JSON formatter that safely extracts fields from the LogRecord.
    Guarantees 'level' and 'timestamp' fields without relying on rename_fields 
    mapping which can trigger KeyErrors.
    """
    def add_fields(self, log_record: dict[str, Any], record: logging.LogRecord, message_dict: dict[str, Any]) -> None:
        super().add_fields(log_record, record, message_dict)
        log_record["level"] = record.levelname
        log_record["timestamp"] = self.formatTime(record, self.datefmt)
        # Ensure redundant fields are removed if they were part of the fmt string
        log_record.pop("levelname", None)
        log_record.pop("asctime", None)


def setup_logging(level: str = "INFO", json_format: bool = False) -> None:
    """
    Configures the root logger with handlers and formatters.

    Args:
        level: The logging level (e.g., "DEBUG", "INFO").
        json_format: If True, uses JSON formatting for production environments.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear existing handlers to prevent duplication
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(RequestIDFilter())

    if json_format:
        # Production JSON formatting using the robust SafeJsonFormatter
        formatter = SafeJsonFormatter(
            "%(name)s %(message)s %(funcName)s %(lineno)d %(request_id)s"
        )
        # Suppress noisy uvicorn access logs in production unless they are warnings
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    else:
        # Development human-readable formatting
        log_format = "[%(asctime)s] %(levelname)-8s %(name)s [%(request_id)s] — %(message)s"
        formatter = logging.Formatter(log_format)

    handler.setFormatter(formatter)
    root_logger.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """
    Creates and returns a named logger instance configured with the request ID filter.

    Args:
        name: The name of the logger, typically __name__.

    Returns:
        logging.Logger: The configured logger instance.
    """
    logger = logging.getLogger(name)
    # Ensure the logger propagates to the root where the RequestIDFilter is attached
    if not any(isinstance(f, RequestIDFilter) for f in logger.filters):
        logger.addFilter(RequestIDFilter())
    return logger


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    FastAPI/Starlette middleware that generates a unique request ID for 
    each incoming request and exposes it via ContextVar and Response Headers.
    """
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Generate or extract request ID
        rid = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        
        # Set the ContextVar
        token = request_id_var.set(rid)
        
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = rid
            return response
        finally:
            # Clean up ContextVar to prevent leak in some edge cases
            request_id_var.reset(token)
import logging
import sys
import json
from datetime import datetime
from typing import Any, Dict
import traceback

from app.core.config import settings


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON
        """
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        # Add extra fields
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)
        
        # Add request context if available
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        
        return json.dumps(log_data)


class ColoredFormatter(logging.Formatter):
    """
    Colored formatter for console output in development
    """
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record with colors
        """
        log_color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{log_color}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_logging():
    """
    Setup logging configuration for the application
    """
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL))
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, settings.LOG_LEVEL))
    
    # Set formatter based on environment and format setting
    if settings.LOG_FORMAT == "json" or settings.is_production:
        formatter = JSONFormatter()
    else:
        # Use colored formatter for development
        formatter = ColoredFormatter(
            fmt='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Configure specific loggers
    
    # Reduce verbosity of some libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    
    # LangChain logging
    logging.getLogger("langchain").setLevel(logging.INFO)
    
    # SQLAlchemy logging (if using database)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    
    # Set application logger
    app_logger = logging.getLogger("app")
    app_logger.setLevel(getattr(logging, settings.LOG_LEVEL))


class LoggerAdapter(logging.LoggerAdapter):
    """
    Custom logger adapter to add context to log messages
    """
    
    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        """
        Process log message and add context
        """
        extra = kwargs.get("extra", {})
        
        # Add context from adapter
        if self.extra:
            extra.update(self.extra)
        
        kwargs["extra"] = extra
        return msg, kwargs


def get_logger(
    name: str,
    request_id: str = None,
    user_id: str = None,
    **extra_fields
) -> LoggerAdapter:
    """
    Get a logger with context
    
    Args:
        name: Logger name
        request_id: Request ID for tracing
        user_id: User ID for audit
        **extra_fields: Additional fields to include in logs
    
    Returns:
        Logger adapter with context
    """
    logger = logging.getLogger(name)
    
    context = {}
    if request_id:
        context["request_id"] = request_id
    if user_id:
        context["user_id"] = user_id
    if extra_fields:
        context["extra_fields"] = extra_fields
    
    return LoggerAdapter(logger, context)


# Utility functions for structured logging

def log_api_request(
    logger: logging.Logger,
    method: str,
    path: str,
    params: Dict[str, Any] = None,
    body: Any = None,
    headers: Dict[str, str] = None
):
    """
    Log API request details
    """
    logger.info(
        "API Request",
        extra={
            "extra_fields": {
                "api_request": {
                    "method": method,
                    "path": path,
                    "params": params,
                    "body": body if not _is_sensitive(body) else "[REDACTED]",
                    "headers": _filter_sensitive_headers(headers) if headers else None
                }
            }
        }
    )


def log_api_response(
    logger: logging.Logger,
    status_code: int,
    response_time_ms: float,
    body: Any = None
):
    """
    Log API response details
    """
    logger.info(
        "API Response",
        extra={
            "extra_fields": {
                "api_response": {
                    "status_code": status_code,
                    "response_time_ms": response_time_ms,
                    "body": body if not _is_sensitive(body) else "[REDACTED]"
                }
            }
        }
    )


def log_error(
    logger: logging.Logger,
    error: Exception,
    context: Dict[str, Any] = None
):
    """
    Log error with context
    """
    logger.error(
        f"Error occurred: {str(error)}",
        exc_info=True,
        extra={
            "extra_fields": {
                "error_context": context or {}
            }
        }
    )


def _is_sensitive(data: Any) -> bool:
    """
    Check if data contains sensitive information
    """
    if isinstance(data, dict):
        sensitive_keys = {"password", "token", "api_key", "secret", "credential"}
        return any(key.lower() in sensitive_keys for key in data.keys())
    return False


def _filter_sensitive_headers(headers: Dict[str, str]) -> Dict[str, str]:
    """
    Filter sensitive headers
    """
    sensitive_headers = {"authorization", "x-api-key", "cookie", "set-cookie"}
    return {
        k: "[REDACTED]" if k.lower() in sensitive_headers else v
        for k, v in headers.items()
    }
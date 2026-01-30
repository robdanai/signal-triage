"""
Logging Configuration for Signal Triage.

Production-grade logging with:
- Structured JSON logging
- Multiple output handlers (console, file, rotating)
- Log level configuration per module
- Request ID tracking
"""

from __future__ import annotations

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional

try:
    from pythonjsonlogger import jsonlogger
    HAS_JSON_LOGGER = True
except ImportError:
    HAS_JSON_LOGGER = False


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    json_format: bool = False,
    max_file_size_mb: int = 100,
    backup_count: int = 5
):
    """
    Configure logging for Signal Triage.
    
    Args:
        log_level: Minimum log level ("DEBUG", "INFO", "WARNING", "ERROR").
        log_file: Optional file path for log output.
        json_format: Use JSON structured logging (requires python-json-logger).
        max_file_size_mb: Maximum log file size before rotation (MB).
        backup_count: Number of backup log files to keep.
    """
    # Convert string level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    
    # Format
    if json_format and HAS_JSON_LOGGER:
        # JSON format for production
        log_format = "%(asctime)s %(name)s %(levelname)s %(message)s"
        formatter = jsonlogger.JsonFormatter(log_format)
    else:
        # Human-readable format for development
        log_format = (
            "%(asctime)s - %(name)s - %(levelname)s - "
            "%(filename)s:%(lineno)d - %(message)s"
        )
        formatter = logging.Formatter(log_format)
    
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (if log_file specified)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Rotating file handler
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_file_size_mb * 1024 * 1024,
            backupCount=backup_count
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Configure specific loggers
    
    # Set SQLAlchemy to WARNING (reduce noise)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    
    # Set uvicorn to INFO
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    
    # Set httpx/requests to WARNING
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    
    logging.info(f"Logging configured: level={log_level}, json={json_format}, file={log_file}")


class RequestIDFilter(logging.Filter):
    """
    Logging filter to add request ID to all log records.
    
    Useful for tracking logs across async operations.
    """
    
    def __init__(self, request_id: str):
        """Initialize filter with request ID."""
        super().__init__()
        self.request_id = request_id
    
    def filter(self, record):
        """Add request_id to log record."""
        record.request_id = self.request_id
        return True


def get_logger(name: str, request_id: Optional[str] = None) -> logging.Logger:
    """
    Get logger for a module with optional request ID tracking.
    
    Args:
        name: Logger name (typically __name__).
        request_id: Optional request ID for correlation.
    
    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    
    if request_id:
        logger.addFilter(RequestIDFilter(request_id))
    
    return logger

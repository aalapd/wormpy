# logger.py

import logging
import json
import os
import sys
from logging.handlers import RotatingFileHandler
from functools import wraps
from typing import Any, Callable, Dict, Optional
import asyncio

class SimpleFormatter(logging.Formatter):
    def __init__(self):
        super().__init__('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "module": record.module,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_record)

class SensitiveDataFilter(logging.Filter):
    def __init__(self, patterns):
        super().__init__()
        self.patterns = patterns

    def filter(self, record):
        message = record.getMessage()
        for pattern in self.patterns:
            message = message.replace(pattern, "*" * len(pattern))
        record.msg = message
        return True

def configure_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    max_file_size: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5,
    sensitive_patterns: Optional[list] = None,
    use_json: bool = False
):
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove all existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    formatter = JSONFormatter() if use_json else SimpleFormatter()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler (if log_file is specified)
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = RotatingFileHandler(
            log_file, maxBytes=max_file_size, backupCount=backup_count
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Sensitive data filter
    if sensitive_patterns:
        sensitive_filter = SensitiveDataFilter(sensitive_patterns)
        for handler in root_logger.handlers:
            handler.addFilter(sensitive_filter)

    # Log the configuration
    root_logger.info(f"Logging configured. Level: {log_level}, File: {log_file if log_file else 'None'}")

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)

def log_exception(logger: logging.Logger):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.exception("Exception in %s: %s", func.__name__, str(e))
                raise
        return wrapper
    return decorator

class LoggingContext:
    def __init__(self, logger: logging.Logger, level: Optional[int] = None, extra: Optional[Dict[str, Any]] = None):
        self.logger = logger
        self.level = level
        self.extra = extra
        self.old_level = None
        self.old_extra = None

    def __enter__(self):
        if self.level is not None:
            self.old_level = self.logger.level
            self.logger.setLevel(self.level)
        if self.extra is not None:
            self.old_extra = self.logger.extra
            self.logger.extra = self.extra

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.old_level is not None:
            self.logger.setLevel(self.old_level)
        if self.old_extra is not None:
            self.logger.extra = self.old_extra

def lazy_log(logger: logging.Logger, level: int, message: str, *args, **kwargs):
    if logger.isEnabledFor(level):
        logger.log(level, message, *args, **kwargs)

async def async_log_exception(logger: logging.Logger, func: Callable):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.exception("Exception in %s: %s", func.__name__, str(e))
            raise
    return wrapper

# Example usage in tests
class LogCapture:
    def __init__(self):
        self.handler = logging.handlers.MemoryHandler(capacity=1024*1024)
        self.handler.setFormatter(JSONFormatter())

    def __enter__(self):
        logging.getLogger().addHandler(self.handler)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        logging.getLogger().removeHandler(self.handler)

    def get_logs(self):
        return [json.loads(log.getMessage()) for log in self.handler.buffer]

# Initialize logging with environment-specific settings
env = os.getenv("ENVIRONMENT", "development")
log_level = os.getenv("LOG_LEVEL", "INFO")
log_file = os.getenv("LOG_FILE")
sensitive_patterns = os.getenv("SENSITIVE_PATTERNS", "").split(",")

configure_logging(
    log_level=log_level,
    log_file=log_file,
    sensitive_patterns=sensitive_patterns if sensitive_patterns[0] else None
)
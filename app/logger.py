import json
import logging
from datetime import datetime, timezone


class _FallbackJsonFormatter(logging.Formatter):
    """Stdlib-only JSON formatter used when pythonjsonlogger is not installed."""

    _SKIP = frozenset({
        "args", "created", "exc_info", "exc_text", "filename", "funcName",
        "levelname", "levelno", "lineno", "message", "module", "msecs",
        "msg", "name", "pathname", "process", "processName",
        "relativeCreated", "stack_info", "taskName", "thread", "threadName",
    })

    def format(self, record: logging.LogRecord) -> str:
        record.message = record.getMessage()
        data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.message,
        }
        data.update({k: v for k, v in record.__dict__.items() if k not in self._SKIP and not k.startswith("_")})
        if record.exc_info:
            data["exception"] = self.formatException(record.exc_info)
        return json.dumps(data)


def _build_formatter():
    try:
        from pythonjsonlogger import jsonlogger
        return jsonlogger.JsonFormatter(
            fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
    except ImportError:
        return _FallbackJsonFormatter()


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(_build_formatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

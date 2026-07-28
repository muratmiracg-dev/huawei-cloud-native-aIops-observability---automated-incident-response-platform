import logging
import sys
from contextvars import ContextVar

from pythonjsonlogger.json import JsonFormatter

request_id_context: ContextVar[str] = ContextVar("request_id", default="-")


class ContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_context.get()
        return True


def configure_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        JsonFormatter(
            "%(asctime)s %(levelname)s %(name)s %(message)s %(request_id)s",
            rename_fields={"levelname": "severity", "asctime": "timestamp"},
        )
    )
    handler.addFilter(ContextFilter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level.upper())

import logging
import sys
from datetime import datetime
from pathlib import Path


class LoggerFactory:
    """Logger com saída no console (colorida) e em arquivo txt na pasta logs/."""

    def __init__(self, log_directory: Path = Path("logs")):
        self._logger = logging.getLogger("rpa")
        self._logger.setLevel(logging.DEBUG)

        if not self._logger.handlers:
            self._logger.addHandler(_console_handler())
            self._logger.addHandler(_file_handler(log_directory))

    def info(self, message: str, **kwargs):
        self._logger.info(message, extra={"extra_data": kwargs})

    def warning(self, message: str, **kwargs):
        self._logger.warning(message, extra={"extra_data": kwargs})

    def error(self, message: str, **kwargs):
        self._logger.error(message, extra={"extra_data": kwargs})

    def exception(self, message: str, **kwargs):
        self._logger.exception(message, extra={"extra_data": kwargs})


def _console_handler() -> logging.StreamHandler:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(_Formatter(colorize=True))
    return handler


def _file_handler(directory: Path) -> logging.FileHandler:
    directory.mkdir(exist_ok=True)
    nome = datetime.now().strftime("%Y%m%d_%H%M%S") + ".txt"
    handler = logging.FileHandler(directory / nome, encoding="utf-8")
    handler.setFormatter(_Formatter(colorize=False))
    return handler


class _Formatter(logging.Formatter):
    _COLORS = {
        "DEBUG":    "\033[36m",
        "INFO":     "\033[32m",
        "WARNING":  "\033[33m",
        "ERROR":    "\033[31m",
        "CRITICAL": "\033[35m",
        "RESET":    "\033[0m",
    }

    def __init__(self, colorize: bool):
        super().__init__()
        self.colorize = colorize

    def format(self, record: logging.LogRecord) -> str:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        level = record.levelname

        if self.colorize:
            color = self._COLORS.get(level, self._COLORS["RESET"])
            reset = self._COLORS["RESET"]
            linha = f"{color}[{ts}] [{level}]{reset} {record.getMessage()}"
        else:
            linha = f"[{ts}] [{level}] {record.getMessage()}"

        extra = getattr(record, "extra_data", {})
        if extra:
            linha += f" | {extra}"

        if record.exc_info:
            linha += "\n" + self.formatException(record.exc_info)

        return linha

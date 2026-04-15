"""
Logging util taken from Turtlebott (previous closed-source project of mine.)
"""
import logging
import os
from datetime import datetime
from pathlib import Path

_shared_log_file = None
_file_handler = None


class ColorFormatter(logging.Formatter):
    """Formatter with ANSI color support for console output and fixed-width columns."""

    COLORS = {
        'DEBUG': '\033[36m',
        'INFO': '\033[32m',
        'WARNING': '\033[33m',
        'ERROR': '\033[31m',
        'CRITICAL': '\033[35m',
    }
    RESET = '\033[0m'

    TIME_WIDTH = 19
    NAME_WIDTH = 15
    LEVEL_WIDTH = 8

    def format(self, record):
        record_copy = logging.makeLogRecord(record.__dict__)

        timestamp = datetime.fromtimestamp(record_copy.created).strftime("%Y-%m-%d %H:%M:%S")
        name = f"{record_copy.name:<{self.NAME_WIDTH}}"
        levelname = f"{record_copy.levelname:<{self.LEVEL_WIDTH}}"

        color = self.COLORS.get(record_copy.levelname, self.RESET)
        levelname = f"{color}{levelname}{self.RESET}"
        name = f"\033[34m{name}\033[0m"

        return f"{timestamp} | {name} | {levelname} | {record_copy.getMessage()}"

class PlainFormatter(logging.Formatter):
    """Plain formatter without any color codes."""

    def format(self, record):
        log_format = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
        formatter = logging.Formatter(log_format, datefmt="%Y-%m-%d %H:%M:%S")
        return formatter.format(record)


def _get_log_file_path(log_dir: str) -> str:
    """
    Get the log file path with m-d-y_h-m(_#).log format.
    If a file already exists for this minute, append a number.
    """
    now = datetime.now()
    timestamp = now.strftime("%m-%d-%y_%H-%M")

    Path(log_dir).mkdir(parents=True, exist_ok=True)

    # Check if file exists
    base_log_file = os.path.join(log_dir, f"{timestamp}.log")
    if not os.path.exists(base_log_file):
        return base_log_file

    counter = 1
    while True:
        numbered_log_file = os.path.join(log_dir, f"{timestamp}_{counter}.log")
        if not os.path.exists(numbered_log_file):
            return numbered_log_file
        counter += 1


def setup_logger(name: str, log_dir: str = None, use_color: bool = True) -> logging.Logger:
    """
    Setup a logger with console and shared file handlers.
    All loggers write to the same combined log file.

    Args:
        name: Logger name (module name)
        log_dir: Directory to save logs. If None, uses {cwd}/logs
        use_color: Whether to use colored output in console

    Returns:
        Configured logger instance
    """
    global _shared_log_file, _file_handler

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    logger.handlers.clear()

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    if use_color:
        console_handler.setFormatter(ColorFormatter())
    else:
        console_handler.setFormatter(PlainFormatter())
    logger.addHandler(console_handler)

    # create shared file handler
    if _file_handler is None:
        if log_dir is None:
            log_dir = os.path.join(os.getcwd(), "logs")

        _shared_log_file = _get_log_file_path(log_dir)
        _file_handler = logging.FileHandler(_shared_log_file, encoding='utf-8')
        _file_handler.setLevel(logging.DEBUG)
        _file_handler.setFormatter(PlainFormatter())

    logger.addHandler(_file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """Get an existing logger with the given name."""
    return logging.getLogger(name)

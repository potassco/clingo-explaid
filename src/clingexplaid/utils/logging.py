import logging
from typing import Optional

# Define ANSI escape sequences for colors
LOG_COLORS = {
    "DEBUG": "\033[94m",  # Blue
    "INFO": "\033[92m",  # Green
    "WARNING": "\033[93m",  # Yellow
    "ERROR": "\033[91m",  # Red
    "CRITICAL": "\033[95m",  # Magenta
    "RESET": "\033[0m",  # Reset
}
DEFAULT_LOGGER_NAME = "default_colored_logger"


class ColoredFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord):
        log_color = LOG_COLORS.get(record.levelname, LOG_COLORS["RESET"])
        reset = LOG_COLORS["RESET"]
        record.levelname = f"{log_color}{record.levelname}{reset}"
        return super().format(record)


def setup_logger(level: int = logging.INFO, name: Optional[str] = DEFAULT_LOGGER_NAME) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(level)

    # Formatter with colored level names
    formatter = ColoredFormatter("%(asctime)s [ %(levelname)s ] %(message)s", datefmt="%H:%M:%S")
    ch.setFormatter(formatter)

    logger.addHandler(ch)

    return logger

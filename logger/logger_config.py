import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

# ANSI escape codes for colors
RESET = "\033[0m"
INFO_COLOR = "\033[92m"  # Green
WARNING_COLOR = "\033[93m"  # Yellow
ERROR_COLOR = "\033[91m"  # Red

class ColoredFormatter(logging.Formatter):
    def format(self, record):
        color = RESET
        if record.levelname == 'INFO':
            color = INFO_COLOR
        elif record.levelname == 'WARNING':
            color = WARNING_COLOR
        elif record.levelname == 'ERROR':
            color = ERROR_COLOR
        return f"{color}{super().format(record)}{RESET}"

log_dir = Path(__file__).resolve().parent / 'logs'
log_dir.mkdir(exist_ok=True)
logger = logging.getLogger('my_logger')
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setFormatter(ColoredFormatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(console_handler)

file_handler = TimedRotatingFileHandler(
    log_dir / 'my_log.log',
    when='D',
    interval=1,
    backupCount=5
)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)
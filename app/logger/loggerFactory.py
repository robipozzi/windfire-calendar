import logging
import json
from logging.handlers import TimedRotatingFileHandler

class LoggerFactory:
    default_level: int
    logger: logging.Logger

    def __init__(self, default_level=logging.DEBUG):
        self.default_level = default_level
    
    def get_logger(self, logger_name):
        """Ensure logging is configured and return a logger."""
        self.logger = logging.getLogger(logger_name)
        file_handler = TimedRotatingFileHandler(
            "windfire-calendar.log", when="midnight", interval=1 / 86400, backupCount=7
        )
        stream_handler = logging.StreamHandler()
        #file_handler.setFormatter(JsonFormatter())
        file_handler.setFormatter(ColorFormatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s"))
        stream_handler.setFormatter(ColorFormatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s"))
        self.logger.handlers = [file_handler]
        self.logger.setLevel(logging.DEBUG)
        return self.logger
        
class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "module": record.module,
            "funcName": record.funcName,
            "lineno": record.lineno,
            "message": record.getMessage(),
        }
        return json.dumps(log_record)        

class ColorFormatter(logging.Formatter):
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[41m', # Red background
    }
    RESET = '\033[0m'

    def format(self, record):
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)
    
##############################################
##### Initialize Logger Factory instance #####
##############################################
logger_factory = LoggerFactory()
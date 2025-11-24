import logging
import json
from logging.handlers import TimedRotatingFileHandler
from config.settings import settings

class LoggerFactory:
    level: int
    logger: logging.Logger

    def __init__(self, level=logging.NOTSET):
        print(f"DEFAULT LOG FILE: {settings.get('DEFAULT_LOG_FILE')}")
        print(f"DEFAULT LOG BACKUP COUNT: {settings.get('DEFAULT_LOG_BACKUP_COUNT')}")
        print(f"DEFAULT LOG ROTATION WHEN: {settings.get('DEFAULT_LOG_ROTATION_WHEN')}")
        print(f"DEFAULT LOG ROTATION INTERVAL: {settings.get('DEFAULT_LOG_ROTATION_INTERVAL')}")

        # If DEFAULT_LOG_LEVEL is set in settings, map it to a logging level constant
        # DEBUG = 10, INFO = 20, WARNING = 30, ERROR = 40, CRITICAL = 50
        default_level = settings.get('DEFAULT_LOG_LEVEL')
        if default_level is not None:
            try:
                if isinstance(default_level, int):
                    level = default_level
                else:
                    level_str = str(default_level).strip().upper()
                    # support numeric strings
                    if level_str.isdigit():
                        level = int(level_str)
                    else:
                        level = {
                            "NOTSET": logging.NOTSET,
                            "DEBUG": logging.DEBUG,
                            "INFO": logging.INFO,
                            "WARNING": logging.WARNING,                            
                            "ERROR": logging.ERROR,
                            "CRITICAL": logging.CRITICAL,

                        }.get(level_str, level)
            except Exception:
                print(f"Invalid DEFAULT_LOG_LEVEL '{default_level}', using {level}")

        print(f"level: {level}")
        self.level = level
    
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
        # ****** Check whether LOG_LEVEL environment variable is set ******
        self.logger.setLevel(self.level)
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
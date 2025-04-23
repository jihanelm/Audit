import logging.config
from logging.handlers import TimedRotatingFileHandler
from zoneinfo import ZoneInfo
from datetime import datetime
import os


class MoroccoTimedRotatingFileHandler(TimedRotatingFileHandler):
    def computeRollover(self, currentTime):
        # Redéfinir le moment de rotation avec l'heure du Maroc
        tz = ZoneInfo("Africa/Casablanca")
        dt = datetime.fromtimestamp(currentTime, tz)
        return super().computeRollover(dt.timestamp())

if not os.path.exists("logs"):
    os.makedirs("logs")

LOG_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
        },
    },
    "handlers": {
        "file": {
            "()": MoroccoTimedRotatingFileHandler,
            "filename": "logs/app.log",
            "when": "midnight",              # rotation tous les jours à minuit
            "interval": 1,                   # chaque 1 jour
            "encoding": "utf-8",
            "formatter": "default",
        },
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default"
        }
    },
    "root": {
        "level": "INFO",
        "handlers": ["file", "console"]
    }
}

def setup_logger():
    logging.config.dictConfig(LOG_CONFIG)
    logger = logging.getLogger(__name__)
    return logger

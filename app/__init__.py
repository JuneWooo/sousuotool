import sys
from loguru import logger
from app.config.config import settings

logger.remove()
logger.add(settings.LOG_DIR, level=settings.LOG_LEVEL)
logger.add(sys.stdout, level="DEBUG")

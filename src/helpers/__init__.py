from loguru import logger

logger.add(
    "info.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {module}:{function}:{line} - {message}",
    level="INFO",
)

logger.info("Logging started.")

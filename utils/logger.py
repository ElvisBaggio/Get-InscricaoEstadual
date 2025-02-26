import os
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from utils.config import settings

# Create logs directory if it doesn't exist
logs_dir = Path("logs")
logs_dir.mkdir(exist_ok=True)

def setup_logger(name: str, log_file: str, level=logging.INFO) -> logging.Logger:
    """
    Set up a logger instance with both file and console handlers
    
    Args:
        name: Logger name (typically service name)
        log_file: Path to log file
        level: Logging level
        
    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Prevent adding handlers multiple times
    if not logger.handlers:
        # File handler with rotation (10MB max size, keep 5 backup files)
        file_handler = RotatingFileHandler(
            os.path.join(logs_dir, log_file),
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(logging.Formatter(settings.LOG_FORMAT, settings.DATETIME_FORMAT))
        logger.addHandler(file_handler)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(settings.LOG_FORMAT, settings.DATETIME_FORMAT))
        logger.addHandler(console_handler)
    
    return logger

# Create loggers for different components
captcha_logger = setup_logger('captcha_service', 'captcha.log', logging.DEBUG)
selenium_logger = setup_logger('selenium_service', 'selenium.log', logging.DEBUG)
api_logger = setup_logger('api', 'api.log', logging.INFO)
app_logger = setup_logger('app', 'app.log', logging.INFO)

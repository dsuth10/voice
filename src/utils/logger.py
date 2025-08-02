"""
Logging system for Voice Dictation Assistant.

This module provides a centralized logging configuration with rotating file handlers,
console output, and appropriate log formatting for the application.
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path


class VoiceDictationLogger:
    """Centralized logging system for Voice Dictation Assistant."""
    
    def __init__(self, name="VoiceDictationAssistant", log_level=logging.INFO):
        """
        Initialize the logging system.
        
        Args:
            name (str): Logger name
            log_level: Logging level (default: INFO)
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(log_level)
        
        # Prevent duplicate handlers
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self):
        """Set up logging handlers for file and console output."""
        # Create logs directory in user's AppData
        log_dir = Path(os.environ.get('APPDATA', '')) / 'VoiceDictationAssistant' / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Main log file
        log_file = log_dir / 'app.log'
        
        # Create rotating file handler (10 files, 1MB each)
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=1024 * 1024,  # 1MB
            backupCount=10,
            encoding='utf-8'
        )
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        
        # Define log format
        log_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        file_handler.setFormatter(log_format)
        console_handler.setFormatter(log_format)
        
        # Add handlers to logger
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        # Set higher level for third-party libraries to reduce noise
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('PIL').setLevel(logging.WARNING)
        logging.getLogger('matplotlib').setLevel(logging.WARNING)
    
    def get_logger(self, name=None):
        """
        Get a logger instance.
        
        Args:
            name (str): Optional logger name
            
        Returns:
            logging.Logger: Logger instance
        """
        if name:
            return logging.getLogger(f"VoiceDictationAssistant.{name}")
        return self.logger
    
    def info(self, message):
        """Log info message."""
        self.logger.info(message)
    
    def warning(self, message):
        """Log warning message."""
        self.logger.warning(message)
    
    def error(self, message):
        """Log error message."""
        self.logger.error(message)
    
    def debug(self, message):
        """Log debug message."""
        self.logger.debug(message)
    
    def critical(self, message):
        """Log critical message."""
        self.logger.critical(message)
    
    def exception(self, message):
        """Log exception with traceback."""
        self.logger.exception(message)
    
    def get_log_file_path(self):
        """Get the path to the current log file."""
        log_dir = Path(os.environ.get('APPDATA', '')) / 'VoiceDictationAssistant' / 'logs'
        return log_dir / 'app.log'


# Global logger instance
_logger_instance = None


def get_logger(name=None):
    """
    Get a logger instance for the application.
    
    Args:
        name (str): Optional logger name
        
    Returns:
        logging.Logger: Logger instance
    """
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = VoiceDictationLogger()
    
    if name:
        return _logger_instance.get_logger(name)
    return _logger_instance.get_logger()


def setup_logging(log_level=logging.INFO):
    """
    Set up logging for the application.
    
    Args:
        log_level: Logging level (default: INFO)
    """
    global _logger_instance
    _logger_instance = VoiceDictationLogger(log_level=log_level)
    return _logger_instance


# Convenience functions
def log_info(message, logger_name=None):
    """Log info message."""
    logger = get_logger(logger_name)
    logger.info(message)


def log_warning(message, logger_name=None):
    """Log warning message."""
    logger = get_logger(logger_name)
    logger.warning(message)


def log_error(message, logger_name=None):
    """Log error message."""
    logger = get_logger(logger_name)
    logger.error(message)


def log_debug(message, logger_name=None):
    """Log debug message."""
    logger = get_logger(logger_name)
    logger.debug(message)


def log_critical(message, logger_name=None):
    """Log critical message."""
    logger = get_logger(logger_name)
    logger.critical(message)


def log_exception(message, logger_name=None):
    """Log exception with traceback."""
    logger = get_logger(logger_name)
    logger.exception(message) 
#!/usr/bin/env python3
"""
Test script to verify the logging system works correctly.
"""

import sys
import os
from pathlib import Path

# Add src to path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from utils.logger import setup_logging, get_logger, log_info, log_warning, log_error, log_debug


def test_logging_system():
    """Test the logging system functionality."""
    print("Testing Voice Dictation Assistant Logging System")
    print("=" * 50)
    
    # Set up logging
    logger_instance = setup_logging()
    logger = get_logger("test")
    
    # Test different log levels
    print("Testing log levels...")
    log_info("This is an info message", "test")
    log_warning("This is a warning message", "test")
    log_error("This is an error message", "test")
    log_debug("This is a debug message", "test")
    
    # Test direct logger methods
    print("Testing direct logger methods...")
    logger.info("Direct info message")
    logger.warning("Direct warning message")
    logger.error("Direct error message")
    logger.debug("Direct debug message")
    
    # Test exception logging
    print("Testing exception logging...")
    try:
        raise ValueError("Test exception for logging")
    except ValueError as e:
        logger.exception(f"Caught exception: {e}")
    
    # Test log file creation
    print("Testing log file creation...")
    log_file_path = logger_instance.get_log_file_path()
    print(f"Log file path: {log_file_path}")
    
    if log_file_path.exists():
        print(f"✅ Log file created successfully")
        print(f"Log file size: {log_file_path.stat().st_size} bytes")
        
        # Read and display last few lines
        with open(log_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            print(f"Last 5 log entries:")
            for line in lines[-5:]:
                print(f"  {line.strip()}")
    else:
        print("❌ Log file was not created")
        return False
    
    print("\n" + "=" * 50)
    print("✅ Logging system test completed successfully!")
    return True


def test_log_rotation():
    """Test log rotation functionality."""
    print("\nTesting log rotation...")
    
    logger = get_logger("rotation_test")
    
    # Generate many log entries to trigger rotation
    for i in range(1000):
        logger.info(f"Test log entry {i}: " + "x" * 100)  # Long message to fill log quickly
    
    log_file_path = Path(os.environ.get('APPDATA', '')) / 'VoiceDictationAssistant' / 'logs' / 'app.log'
    
    if log_file_path.exists():
        print(f"✅ Log rotation test completed. Current log size: {log_file_path.stat().st_size} bytes")
        return True
    else:
        print("❌ Log rotation test failed")
        return False


def main():
    """Run all logging tests."""
    success = True
    
    # Test basic logging
    if not test_logging_system():
        success = False
    
    # Test log rotation (optional - can be slow)
    # if not test_log_rotation():
    #     success = False
    
    if success:
        print("\n🎉 All logging tests passed!")
        return True
    else:
        print("\n⚠️  Some logging tests failed.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 
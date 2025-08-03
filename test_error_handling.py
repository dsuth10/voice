#!/usr/bin/env python3
"""
Test script for the Enhanced Error Handling and Logging System

This script tests the comprehensive error handling functionality including:
- Error categorization
- User-friendly error messages
- Contextual logging
- Recovery strategies
- Global exception handling
"""

import sys
import time
import logging
import threading
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.error_handler import ErrorHandler, ErrorNotifier, ErrorCategory, ErrorSeverity
from src.core.feedback_system import UserFeedbackSystem, FeedbackType
from src.utils.logger import setup_logging


def setup_test_environment():
    """Setup test environment."""
    # Setup logging
    setup_logging(logging.DEBUG)
    
    # Setup feedback system
    feedback_system = UserFeedbackSystem(FeedbackType.BOTH)
    
    # Setup error handler
    error_handler = ErrorHandler()
    
    # Setup error notifier
    error_notifier = ErrorNotifier(feedback_system)
    
    return error_handler, error_notifier, feedback_system


def test_error_categorization(error_handler):
    """Test error categorization functionality."""
    print("Testing error categorization...")
    
    # Test different types of errors
    test_errors = [
        ("No microphone detected", "audio"),
        ("API key authentication failed", "configuration"),
        ("Network timeout", "network"),
        ("Permission denied", "permission"),
        ("Memory allocation failed", "resource"),
        ("Speech recognition failed", "transcription"),
        ("Text enhancement error", "ai_enhancement"),
        ("Clipboard access denied", "text_insertion"),
        ("Hotkey already registered", "hotkey"),
        ("Unknown error occurred", "unknown")
    ]
    
    for error_message, expected_category in test_errors:
        exception = Exception(error_message)
        error_info = error_handler._create_error_info(exception, None, None)
        category = error_handler._classify_error(exception)
        
        print(f"  {error_message[:30]:<30} -> {category.value}")
        
        if category.value == expected_category:
            print(f"    ✅ Correctly categorized as {category.value}")
        else:
            print(f"    ❌ Expected {expected_category}, got {category.value}")


def test_user_friendly_messages(error_notifier):
    """Test user-friendly error message generation."""
    print("\nTesting user-friendly error messages...")
    
    from src.core.error_handler import ErrorInfo
    from datetime import datetime
    
    # Test different error scenarios
    test_scenarios = [
        ("No microphone detected", "audio"),
        ("API key authentication failed", "transcription"),
        ("Rate limit exceeded", "ai_enhancement"),
        ("Network timeout", "network"),
        ("Access denied", "permission"),
        ("Insufficient memory", "resource"),
        ("Clipboard in use", "text_insertion"),
        ("Hotkey conflict", "hotkey"),
        ("Configuration file not found", "configuration")
    ]
    
    for error_message, category_name in test_scenarios:
        category = ErrorCategory(category_name)
        error_info = ErrorInfo(
            timestamp=datetime.now(),
            error_type=Exception,
            error_message=error_message,
            severity=ErrorSeverity.MEDIUM,
            category=category
        )
        
        user_message = error_notifier._create_error_message(error_info)
        print(f"  {error_message[:30]:<30} -> {user_message}")


def test_contextual_logging(error_handler):
    """Test contextual logging functionality."""
    print("\nTesting contextual logging...")
    
    # Create a test error
    exception = Exception("Test error for logging")
    error_info = error_handler._create_error_info(exception, None, None)
    
    # Test logging with context
    error_handler._log_error_with_context(error_info)
    
    print("  ✅ Contextual logging test completed")


def test_recovery_strategies(error_handler):
    """Test recovery strategies."""
    print("\nTesting recovery strategies...")
    
    # Test audio recovery
    audio_error = Exception("Audio device not found")
    audio_error_info = error_handler._create_error_info(audio_error, None, None)
    
    print(f"  Audio error category: {audio_error_info.category.value}")
    print(f"  Audio error severity: {audio_error_info.severity.value}")
    
    # Test recovery attempt
    recovery_success = error_handler._attempt_recovery(audio_error_info)
    print(f"  Recovery attempt result: {'Success' if recovery_success else 'Failed'}")


def test_global_exception_handling():
    """Test global exception handling."""
    print("\nTesting global exception handling...")
    
    def trigger_exception():
        """Function that raises an exception."""
        raise ValueError("Test exception for global handling")
    
    def trigger_thread_exception():
        """Function that raises an exception in a thread."""
        raise RuntimeError("Test thread exception")
    
    # Test main thread exception
    try:
        trigger_exception()
    except Exception as e:
        print(f"  ✅ Main thread exception caught: {e}")
    
    # Test thread exception
    thread = threading.Thread(target=trigger_thread_exception)
    thread.start()
    thread.join()
    print("  ✅ Thread exception handling test completed")


def test_error_statistics(error_handler):
    """Test error statistics functionality."""
    print("\nTesting error statistics...")
    
    # Generate some test errors
    test_errors = [
        Exception("Test error 1"),
        Exception("Test error 2"),
        Exception("Test error 3")
    ]
    
    for error in test_errors:
        error_handler.handle_error(error)
    
    # Get statistics
    stats = error_handler.get_error_statistics()
    print(f"  Total errors: {stats['total_errors']}")
    print(f"  Recovery successes: {stats['recovery_successes']}")
    print(f"  Recovery failures: {stats['recovery_failures']}")
    print(f"  Recovery rate: {stats['recovery_rate']:.1f}%")
    print(f"  Recent errors: {stats['recent_errors']}")


def test_log_file_creation():
    """Test log file creation and rotation."""
    print("\nTesting log file creation...")
    
    from src.utils.logger import get_logger
    
    logger = get_logger("test_logger")
    
    # Generate some log entries
    logger.info("Test info message")
    logger.warning("Test warning message")
    logger.error("Test error message")
    
    # Check if log file exists
    log_file = Path.home() / "AppData" / "Roaming" / "VoiceDictationAssistant" / "logs" / "app.log"
    if log_file.exists():
        print(f"  ✅ Log file created: {log_file}")
        print(f"  Log file size: {log_file.stat().st_size} bytes")
    else:
        print(f"  ❌ Log file not found: {log_file}")


def main():
    """Main test function."""
    print("=== Enhanced Error Handling and Logging System Test ===")
    
    try:
        # Setup test environment
        error_handler, error_notifier, feedback_system = setup_test_environment()
        
        # Run tests
        test_error_categorization(error_handler)
        test_user_friendly_messages(error_notifier)
        test_contextual_logging(error_handler)
        test_recovery_strategies(error_handler)
        test_global_exception_handling()
        test_error_statistics(error_handler)
        test_log_file_creation()
        
        print("\n=== Test Summary ===")
        print("Enhanced error handling and logging system tests completed.")
        print("Check the logs above for detailed information.")
        
        # Cleanup
        error_handler.shutdown()
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 
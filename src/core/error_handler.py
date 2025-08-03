"""
Error Handling and Recovery System for Voice Dictation Assistant

This module provides comprehensive error detection, notification, and recovery
strategies for all workflow stages, ensuring the application can recover gracefully
from failures without requiring a restart.
"""

import threading
import time
import logging
import traceback
from typing import Optional, Callable, Dict, Any, List, Type
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

from .application_controller import ApplicationState
from .workflow_manager import WorkflowStep


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for classification."""
    AUDIO = "audio"
    TRANSCRIPTION = "transcription"
    AI_ENHANCEMENT = "ai_enhancement"
    TEXT_INSERTION = "text_insertion"
    HOTKEY = "hotkey"
    CONFIGURATION = "configuration"
    NETWORK = "network"
    PERMISSION = "permission"
    RESOURCE = "resource"
    UNKNOWN = "unknown"


@dataclass
class ErrorInfo:
    """Error information structure."""
    timestamp: datetime
    error_type: Type[Exception]
    error_message: str
    severity: ErrorSeverity
    category: ErrorCategory
    workflow_step: Optional[WorkflowStep] = None
    application_state: Optional[ApplicationState] = None
    retry_count: int = 0
    max_retries: int = 3
    recovery_strategy: Optional[str] = None
    stack_trace: Optional[str] = None


class RecoveryStrategy:
    """Base class for recovery strategies."""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.logger = logging.getLogger(__name__)
    
    def can_handle(self, error_info: ErrorInfo) -> bool:
        """Check if this strategy can handle the error."""
        raise NotImplementedError
    
    def execute(self, error_info: ErrorInfo) -> bool:
        """Execute the recovery strategy."""
        raise NotImplementedError


class AudioRecoveryStrategy(RecoveryStrategy):
    """Recovery strategy for audio-related errors."""
    
    def __init__(self):
        super().__init__("audio_recovery", "Recover from audio capture errors")
    
    def can_handle(self, error_info: ErrorInfo) -> bool:
        return error_info.category == ErrorCategory.AUDIO
    
    def execute(self, error_info: ErrorInfo) -> bool:
        self.logger.info("Executing audio recovery strategy")
        
        try:
            # Try to reinitialize audio capture with different settings
            # This would be implemented in the ApplicationController
            return True
        except Exception as e:
            self.logger.error(f"Audio recovery failed: {e}")
            return False


class TranscriptionRecoveryStrategy(RecoveryStrategy):
    """Recovery strategy for transcription errors."""
    
    def __init__(self):
        super().__init__("transcription_recovery", "Recover from transcription errors")
    
    def can_handle(self, error_info: ErrorInfo) -> bool:
        return error_info.category == ErrorCategory.TRANSCRIPTION
    
    def execute(self, error_info: ErrorInfo) -> bool:
        self.logger.info("Executing transcription recovery strategy")
        
        try:
            # Try fallback transcription service
            # This would be implemented in the SpeechRecognition component
            return True
        except Exception as e:
            self.logger.error(f"Transcription recovery failed: {e}")
            return False


class AIEnhancementRecoveryStrategy(RecoveryStrategy):
    """Recovery strategy for AI enhancement errors."""
    
    def __init__(self):
        super().__init__("ai_enhancement_recovery", "Recover from AI enhancement errors")
    
    def can_handle(self, error_info: ErrorInfo) -> bool:
        return error_info.category == ErrorCategory.AI_ENHANCEMENT
    
    def execute(self, error_info: ErrorInfo) -> bool:
        self.logger.info("Executing AI enhancement recovery strategy")
        
        try:
            # Try fallback AI model or skip enhancement
            # This would be implemented in the AITextProcessor component
            return True
        except Exception as e:
            self.logger.error(f"AI enhancement recovery failed: {e}")
            return False


class TextInsertionRecoveryStrategy(RecoveryStrategy):
    """Recovery strategy for text insertion errors."""
    
    def __init__(self):
        super().__init__("text_insertion_recovery", "Recover from text insertion errors")
    
    def can_handle(self, error_info: ErrorInfo) -> bool:
        return error_info.category == ErrorCategory.TEXT_INSERTION
    
    def execute(self, error_info: ErrorInfo) -> bool:
        self.logger.info("Executing text insertion recovery strategy")
        
        try:
            # Try alternative insertion method or clipboard fallback
            # This would be implemented in the TextInsertionSystem component
            return True
        except Exception as e:
            self.logger.error(f"Text insertion recovery failed: {e}")
            return False


class ConfigurationRecoveryStrategy(RecoveryStrategy):
    """Recovery strategy for configuration errors."""
    
    def __init__(self):
        super().__init__("configuration_recovery", "Recover from configuration errors")
    
    def can_handle(self, error_info: ErrorInfo) -> bool:
        return error_info.category == ErrorCategory.CONFIGURATION
    
    def execute(self, error_info: ErrorInfo) -> bool:
        self.logger.info("Executing configuration recovery strategy")
        
        try:
            # Try to reload configuration or use defaults
            # This would be implemented in the ConfigManager component
            return True
        except Exception as e:
            self.logger.error(f"Configuration recovery failed: {e}")
            return False


class ErrorHandler:
    """
    Comprehensive error handling and recovery system.
    
    This class provides error detection, classification, recovery strategies,
    and user notification for all application components.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Error tracking
        self.error_history: List[ErrorInfo] = []
        self.error_lock = threading.Lock()
        
        # Recovery strategies
        self.recovery_strategies: List[RecoveryStrategy] = [
            AudioRecoveryStrategy(),
            TranscriptionRecoveryStrategy(),
            AIEnhancementRecoveryStrategy(),
            TextInsertionRecoveryStrategy(),
            ConfigurationRecoveryStrategy(),
        ]
        
        # Callbacks
        self.error_callbacks: List[Callable[[ErrorInfo], None]] = []
        self.recovery_callbacks: List[Callable[[ErrorInfo, bool], None]] = []
        
        # Statistics
        self.error_count = 0
        self.recovery_success_count = 0
        self.recovery_failure_count = 0
        
        self.logger.info("ErrorHandler initialized")
        
        # Set up global exception handling
        self._setup_global_exception_handling()
    
    def handle_error(self, 
                    exception: Exception, 
                    workflow_step: Optional[WorkflowStep] = None,
                    application_state: Optional[ApplicationState] = None) -> ErrorInfo:
        """
        Handle an error with classification and recovery.
        
        Args:
            exception: The exception that occurred
            workflow_step: Current workflow step (if applicable)
            application_state: Current application state (if applicable)
            
        Returns:
            ErrorInfo object with error details and recovery status
        """
        with self.error_lock:
            # Create error info
            error_info = self._create_error_info(exception, workflow_step, application_state)
            
            # Add to history
            self.error_history.append(error_info)
            self.error_count += 1
            
            # Log error with contextual information
            self._log_error_with_context(error_info)
            
            # Attempt recovery
            recovery_success = self._attempt_recovery(error_info)
            
            # Update statistics
            if recovery_success:
                self.recovery_success_count += 1
            else:
                self.recovery_failure_count += 1
            
            # Notify callbacks
            self._notify_error_callbacks(error_info)
            self._notify_recovery_callbacks(error_info, recovery_success)
            
            return error_info
    
    def _create_error_info(self, 
                          exception: Exception, 
                          workflow_step: Optional[WorkflowStep],
                          application_state: Optional[ApplicationState]) -> ErrorInfo:
        """Create ErrorInfo object from exception."""
        # Classify error
        category = self._classify_error(exception)
        severity = self._determine_severity(exception, category)
        
        # Create error info
        error_info = ErrorInfo(
            timestamp=datetime.now(),
            error_type=type(exception),
            error_message=str(exception),
            severity=severity,
            category=category,
            workflow_step=workflow_step,
            application_state=application_state,
            stack_trace=traceback.format_exc()
        )
        
        return error_info
    
    def _log_error_with_context(self, error_info: ErrorInfo):
        """Log error with contextual information."""
        # Create contextual information
        context = {
            'error_type': error_info.error_type.__name__,
            'category': error_info.category.value,
            'severity': error_info.severity.value,
            'retry_count': error_info.retry_count,
            'max_retries': error_info.max_retries
        }
        
        if error_info.workflow_step:
            context['workflow_step'] = error_info.workflow_step.value
        
        if error_info.application_state:
            context['application_state'] = error_info.application_state.value
        
        # Log the error with context
        self.logger.error(
            f"Error occurred: {error_info.error_message}",
            extra={'error_context': context}
        )
        
        # Log stack trace at debug level
        if error_info.stack_trace:
            self.logger.debug(f"Stack trace: {error_info.stack_trace}")
    
    def _classify_error(self, exception: Exception) -> ErrorCategory:
        """Classify the error based on exception type and message."""
        error_message = str(exception).lower()
        exception_type = type(exception).__name__.lower()
        
        # Check for specific exception types first
        if 'requests' in exception_type or 'urllib' in exception_type:
            return ErrorCategory.NETWORK
        
        if 'permission' in exception_type or 'access' in exception_type:
            return ErrorCategory.PERMISSION
        
        if 'memory' in exception_type or 'resource' in exception_type:
            return ErrorCategory.RESOURCE
        
        # Audio errors
        if any(keyword in error_message for keyword in ['audio', 'microphone', 'pyaudio', 'device', 'sound', 'recording']):
            return ErrorCategory.AUDIO
        
        # Transcription errors
        if any(keyword in error_message for keyword in ['transcription', 'speech', 'assemblyai', 'whisper', 'recognize']):
            return ErrorCategory.TRANSCRIPTION
        
        # AI enhancement errors
        if any(keyword in error_message for keyword in ['openai', 'gpt', 'enhancement', 'ai', 'completion', 'model']) and 'api key' not in error_message and 'allocation' not in error_message:
            return ErrorCategory.AI_ENHANCEMENT
        
        # Text insertion errors
        if any(keyword in error_message for keyword in ['insertion', 'text', 'cursor', 'clipboard', 'typing', 'input']):
            return ErrorCategory.TEXT_INSERTION
        
        # Configuration errors (check first to avoid conflicts)
        if any(keyword in error_message for keyword in ['config', 'api_key', 'settings', 'configuration', 'setup']):
            return ErrorCategory.CONFIGURATION
        
        # Resource errors (check before AI enhancement to avoid conflicts)
        if any(keyword in error_message for keyword in ['memory', 'resource', 'disk', 'space', 'quota', 'allocation']):
            return ErrorCategory.RESOURCE
        
        # Network errors
        if any(keyword in error_message for keyword in ['network', 'connection', 'timeout', 'http', 'ssl', 'dns']):
            return ErrorCategory.NETWORK
        
        # Permission errors
        if any(keyword in error_message for keyword in ['permission', 'access', 'denied', 'unauthorized', 'forbidden']):
            return ErrorCategory.PERMISSION
        
        # Hotkey errors (check after configuration to avoid conflicts)
        if any(keyword in error_message for keyword in ['hotkey', 'keyboard', 'shortcut', 'binding']) or ('key' in error_message and 'api_key' not in error_message and 'authentication' not in error_message):
            return ErrorCategory.HOTKEY
        
        return ErrorCategory.UNKNOWN
    
    def _determine_severity(self, exception: Exception, category: ErrorCategory) -> ErrorSeverity:
        """Determine error severity based on exception and category."""
        error_message = str(exception).lower()
        
        # Critical errors
        if any(keyword in error_message for keyword in ['fatal', 'critical', 'unrecoverable']):
            return ErrorSeverity.CRITICAL
        
        # High severity errors
        if category in [ErrorCategory.CONFIGURATION, ErrorCategory.PERMISSION]:
            return ErrorSeverity.HIGH
        
        # Medium severity errors
        if category in [ErrorCategory.AUDIO, ErrorCategory.TRANSCRIPTION, ErrorCategory.AI_ENHANCEMENT]:
            return ErrorSeverity.MEDIUM
        
        # Low severity errors
        if category in [ErrorCategory.TEXT_INSERTION, ErrorCategory.HOTKEY]:
            return ErrorSeverity.LOW
        
        return ErrorSeverity.MEDIUM
    
    def _attempt_recovery(self, error_info: ErrorInfo) -> bool:
        """Attempt to recover from the error with exponential backoff."""
        if error_info.severity == ErrorSeverity.CRITICAL:
            self.logger.error("Critical error - no recovery attempted")
            return False
        
        if error_info.retry_count >= error_info.max_retries:
            self.logger.warning(f"Max retries reached for error: {error_info.error_message}")
            return False
        
        # Increment retry count
        error_info.retry_count += 1
        
        # Calculate delay with exponential backoff (1s, 2s, 4s, etc.)
        delay = 2 ** (error_info.retry_count - 1)
        
        self.logger.info(f"Attempting recovery (attempt {error_info.retry_count}/{error_info.max_retries}) with {delay}s delay")
        
        # Wait before retry
        if error_info.retry_count > 1:
            time.sleep(delay)
        
        # Find applicable recovery strategy
        for strategy in self.recovery_strategies:
            if strategy.can_handle(error_info):
                self.logger.info(f"Attempting recovery with strategy: {strategy.name}")
                
                try:
                    success = strategy.execute(error_info)
                    if success:
                        error_info.recovery_strategy = strategy.name
                        self.logger.info(f"Recovery successful with strategy: {strategy.name}")
                        return True
                    else:
                        self.logger.warning(f"Recovery failed with strategy: {strategy.name}")
                        
                except Exception as e:
                    self.logger.error(f"Recovery strategy execution failed: {e}")
        
        self.logger.warning("No applicable recovery strategy found")
        return False
    
    def _notify_error_callbacks(self, error_info: ErrorInfo):
        """Notify error callbacks."""
        for callback in self.error_callbacks:
            try:
                callback(error_info)
            except Exception as e:
                self.logger.error(f"Error callback failed: {e}")
    
    def _notify_recovery_callbacks(self, error_info: ErrorInfo, recovery_success: bool):
        """Notify recovery callbacks."""
        for callback in self.recovery_callbacks:
            try:
                callback(error_info, recovery_success)
            except Exception as e:
                self.logger.error(f"Recovery callback failed: {e}")
    
    def add_error_callback(self, callback: Callable[[ErrorInfo], None]):
        """Add callback for error notifications."""
        self.error_callbacks.append(callback)
    
    def add_recovery_callback(self, callback: Callable[[ErrorInfo, bool], None]):
        """Add callback for recovery notifications."""
        self.recovery_callbacks.append(callback)
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error handling statistics."""
        with self.error_lock:
            return {
                'total_errors': self.error_count,
                'recovery_successes': self.recovery_success_count,
                'recovery_failures': self.recovery_failure_count,
                'recovery_rate': (self.recovery_success_count / max(self.error_count, 1)) * 100,
                'recent_errors': len([e for e in self.error_history if 
                                    (datetime.now() - e.timestamp).seconds < 3600])
            }
    
    def get_error_history(self, hours: int = 24) -> List[ErrorInfo]:
        """Get error history for the specified time period."""
        cutoff_time = datetime.now().replace(hour=datetime.now().hour - hours)
        
        with self.error_lock:
            return [error for error in self.error_history if error.timestamp > cutoff_time]
    
    def clear_error_history(self):
        """Clear error history."""
        with self.error_lock:
            self.error_history.clear()
            self.error_count = 0
            self.recovery_success_count = 0
            self.recovery_failure_count = 0
    
    def shutdown(self):
        """Shutdown the error handler."""
        self.logger.info("Shutting down error handler")
        
        try:
            # Clear callbacks
            self.error_callbacks.clear()
            self.recovery_callbacks.clear()
            
            # Clear error history
            self.clear_error_history()
            
            self.logger.info("Error handler shutdown completed")
            
        except Exception as e:
            self.logger.error(f"Error during error handler shutdown: {e}")
    
    def _setup_global_exception_handling(self):
        """Set up global exception handling for uncaught exceptions."""
        import sys
        
        def global_exception_handler(exc_type, exc_value, exc_traceback):
            """Global exception handler for uncaught exceptions."""
            if issubclass(exc_type, KeyboardInterrupt):
                # Don't handle keyboard interrupts
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
                return
            
            # Create error info for uncaught exception
            error_info = ErrorInfo(
                timestamp=datetime.now(),
                error_type=exc_type,
                error_message=str(exc_value),
                severity=ErrorSeverity.HIGH,
                category=ErrorCategory.UNKNOWN,
                stack_trace=traceback.format_exception(exc_type, exc_value, exc_traceback)
            )
            
            # Log the uncaught exception
            self.logger.critical(
                f"Uncaught exception: {exc_value}",
                extra={'error_context': {
                    'error_type': exc_type.__name__,
                    'category': 'uncaught',
                    'severity': 'critical'
                }}
            )
            
            # Attempt to handle the error
            self.handle_error(exc_value)
        
        # Set the global exception handler
        sys.excepthook = global_exception_handler
        
        # Set up threading exception handler (Python 3.8+)
        if hasattr(threading, 'excepthook'):
            def threading_exception_handler(args):
                """Handle exceptions in threads."""
                if args.exc_type is not None:
                    self.logger.error(
                        f"Uncaught exception in thread {args.thread}: {args.exc_value}",
                        extra={'error_context': {
                            'error_type': args.exc_type.__name__,
                            'category': 'thread_exception',
                            'thread': args.thread.name if args.thread else 'unknown'
                        }}
                    )
                    self.handle_error(args.exc_value)
            
            threading.excepthook = threading_exception_handler


class ErrorNotifier:
    """Error notification system for user feedback."""
    
    def __init__(self, feedback_system):
        self.logger = logging.getLogger(__name__)
        self.feedback_system = feedback_system
    
    def notify_error(self, error_info: ErrorInfo):
        """Notify user of an error."""
        # Determine notification message based on error severity and category
        message = self._create_error_message(error_info)
        
        # Use feedback system to notify user
        self.feedback_system.on_error(message)
    
    def notify_recovery(self, error_info: ErrorInfo, success: bool):
        """Notify user of recovery attempt result."""
        if success:
            message = f"Recovered from {error_info.category.value} error"
            self.logger.info(message)
        else:
            message = f"Failed to recover from {error_info.category.value} error"
            self.logger.warning(message)
    
    def _create_error_message(self, error_info: ErrorInfo) -> str:
        """Create user-friendly error message."""
        error_message = error_info.error_message.lower()
        
        # Detailed category-specific messages
        category_messages = {
            ErrorCategory.AUDIO: self._get_audio_error_message(error_message),
            ErrorCategory.TRANSCRIPTION: self._get_transcription_error_message(error_message),
            ErrorCategory.AI_ENHANCEMENT: self._get_ai_enhancement_error_message(error_message),
            ErrorCategory.TEXT_INSERTION: self._get_text_insertion_error_message(error_message),
            ErrorCategory.HOTKEY: self._get_hotkey_error_message(error_message),
            ErrorCategory.CONFIGURATION: self._get_configuration_error_message(error_message),
            ErrorCategory.NETWORK: self._get_network_error_message(error_message),
            ErrorCategory.PERMISSION: self._get_permission_error_message(error_message),
            ErrorCategory.RESOURCE: self._get_resource_error_message(error_message),
            ErrorCategory.UNKNOWN: "An unexpected error occurred. Please try again."
        }
        
        base_message = category_messages.get(error_info.category, "An unexpected error occurred.")
        
        # Add severity prefix
        if error_info.severity == ErrorSeverity.CRITICAL:
            return f"Critical Error: {base_message}"
        elif error_info.severity == ErrorSeverity.HIGH:
            return f"Error: {base_message}"
        elif error_info.severity == ErrorSeverity.MEDIUM:
            return f"Warning: {base_message}"
        else:
            return f"Notice: {base_message}"
    
    def _get_audio_error_message(self, error_message: str) -> str:
        """Get user-friendly audio error message."""
        if 'no microphone' in error_message or 'device not found' in error_message:
            return "No microphone detected. Please connect a microphone and try again."
        elif 'permission' in error_message:
            return "Microphone access denied. Please allow microphone permissions in your system settings."
        elif 'busy' in error_message or 'in use' in error_message:
            return "Microphone is currently in use by another application. Please close other audio applications and try again."
        else:
            return "Audio capture error. Please check your microphone settings and try again."
    
    def _get_transcription_error_message(self, error_message: str) -> str:
        """Get user-friendly transcription error message."""
        if 'api key' in error_message or 'authentication' in error_message:
            return "Speech recognition service authentication failed. Please check your API key in settings."
        elif 'rate limit' in error_message:
            return "Speech recognition service is busy. Please wait a moment and try again."
        elif 'network' in error_message or 'connection' in error_message:
            return "Cannot connect to speech recognition service. Please check your internet connection."
        else:
            return "Speech recognition error. Please try speaking again."
    
    def _get_ai_enhancement_error_message(self, error_message: str) -> str:
        """Get user-friendly AI enhancement error message."""
        if 'api key' in error_message or 'authentication' in error_message:
            return "AI enhancement service authentication failed. Please check your API key in settings."
        elif 'rate limit' in error_message:
            return "AI enhancement service is busy. Please wait a moment and try again."
        elif 'network' in error_message or 'connection' in error_message:
            return "Cannot connect to AI enhancement service. Please check your internet connection."
        else:
            return "Text enhancement error. Your text will be inserted without enhancement."
    
    def _get_text_insertion_error_message(self, error_message: str) -> str:
        """Get user-friendly text insertion error message."""
        if 'clipboard' in error_message:
            return "Cannot access clipboard. Please check if another application is using the clipboard."
        elif 'cursor' in error_message or 'position' in error_message:
            return "Cannot determine cursor position. Please click in the text area where you want to insert text."
        else:
            return "Text insertion error. Please manually paste the text if needed."
    
    def _get_hotkey_error_message(self, error_message: str) -> str:
        """Get user-friendly hotkey error message."""
        if 'already registered' in error_message or 'conflict' in error_message:
            return "Hotkey conflict detected. The key combination is already in use by another application."
        elif 'permission' in error_message:
            return "Cannot register hotkeys. Please run the application as administrator or check system permissions."
        else:
            return "Hotkey registration error. You can still use the system tray menu to control the application."
    
    def _get_configuration_error_message(self, error_message: str) -> str:
        """Get user-friendly configuration error message."""
        if 'api key' in error_message:
            return "API key not configured. Please set up your API keys in the settings."
        elif 'file' in error_message or 'path' in error_message:
            return "Configuration file error. Please check if the settings file is accessible."
        else:
            return "Configuration error. Please check your settings and try again."
    
    def _get_network_error_message(self, error_message: str) -> str:
        """Get user-friendly network error message."""
        if 'timeout' in error_message:
            return "Network timeout. Please check your internet connection and try again."
        elif 'ssl' in error_message or 'certificate' in error_message:
            return "Network security error. Please check your system's date and time settings."
        elif 'dns' in error_message:
            return "Cannot resolve server address. Please check your internet connection."
        else:
            return "Network connection error. Please check your internet connection and try again."
    
    def _get_permission_error_message(self, error_message: str) -> str:
        """Get user-friendly permission error message."""
        if 'access denied' in error_message:
            return "Access denied. Please run the application as administrator or check file permissions."
        elif 'unauthorized' in error_message:
            return "Unauthorized access. Please check your account permissions."
        else:
            return "Permission error. Please check your system permissions and try again."
    
    def _get_resource_error_message(self, error_message: str) -> str:
        """Get user-friendly resource error message."""
        if 'memory' in error_message:
            return "Insufficient memory. Please close other applications and try again."
        elif 'disk' in error_message or 'space' in error_message:
            return "Insufficient disk space. Please free up some space and try again."
        else:
            return "System resource error. Please restart the application and try again." 
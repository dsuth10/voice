"""
Error Recovery and Undo Support Module

This module provides robust error handling and recovery mechanisms
for text insertion failures and undo functionality.
"""

import logging
import time
import traceback
from typing import Optional, Dict, Any, List, Callable
from .text_insertion import TextInserter
from .cursor_detection import CursorDetector

logger = logging.getLogger(__name__)


class ErrorRecoveryManager:
    """Manages error recovery and undo functionality for text insertion."""
    
    def __init__(self):
        self.text_inserter = TextInserter()
        self.cursor_detector = CursorDetector()
        self.error_history = []
        self.recovery_strategies = self._initialize_recovery_strategies()
        self.max_error_history = 50
        self.undo_stack = []
        self.max_undo_stack = 20
        
    def _initialize_recovery_strategies(self) -> Dict[str, Callable]:
        """Initialize recovery strategies for different error types."""
        return {
            'clipboard_error': self._handle_clipboard_error,
            'typing_error': self._handle_typing_error,
            'window_error': self._handle_window_error,
            'permission_error': self._handle_permission_error,
            'timeout_error': self._handle_timeout_error,
            'unknown_error': self._handle_unknown_error
        }
    
    def insert_text_with_recovery(self, text: str, use_clipboard: bool = True,
                                 app_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Insert text with comprehensive error recovery.
        
        Args:
            text: Text to insert
            use_clipboard: Whether to use clipboard method
            app_name: Target application name
            
        Returns:
            Dictionary with insertion results and recovery info
        """
        result = {
            'success': False,
            'method_used': None,
            'error_type': None,
            'error_message': None,
            'recovery_attempted': False,
            'recovery_successful': False,
            'undo_available': False
        }
        
        try:
            # Attempt primary insertion
            success = self.text_inserter.insert_text(text, use_clipboard, app_name)
            
            if success:
                result['success'] = True
                result['method_used'] = 'clipboard' if use_clipboard else 'direct'
                result['undo_available'] = True
                
                # Add to undo stack
                self._add_to_undo_stack(text, app_name)
                
                logger.info(f"Text insertion successful using {result['method_used']} method")
                return result
            
            # Primary method failed, try recovery
            result['recovery_attempted'] = True
            recovery_success = self._attempt_recovery(text, use_clipboard, app_name)
            
            if recovery_success:
                result['success'] = True
                result['method_used'] = 'recovery'
                result['recovery_successful'] = True
                result['undo_available'] = True
                
                # Add to undo stack
                self._add_to_undo_stack(text, app_name)
                
                logger.info("Text insertion successful after recovery")
            else:
                result['error_type'] = 'recovery_failed'
                result['error_message'] = "All insertion methods failed"
                logger.error("All insertion methods failed")
            
        except Exception as e:
            error_type = self._classify_error(e)
            result['error_type'] = error_type
            result['error_message'] = str(e)
            result['recovery_attempted'] = True
            
            # Attempt recovery for the specific error
            recovery_success = self._attempt_error_recovery(text, error_type, e)
            
            if recovery_success:
                result['success'] = True
                result['method_used'] = 'error_recovery'
                result['recovery_successful'] = True
                result['undo_available'] = True
                
                # Add to undo stack
                self._add_to_undo_stack(text, app_name)
                
                logger.info(f"Text insertion successful after {error_type} recovery")
            else:
                logger.error(f"Error recovery failed for {error_type}: {e}")
        
        # Log error for analysis
        self._log_error(result)
        
        return result
    
    def _attempt_recovery(self, text: str, original_method: bool, app_name: Optional[str]) -> bool:
        """
        Attempt recovery when primary insertion method fails.
        
        Args:
            text: Text to insert
            original_method: The original method that failed
            app_name: Target application name
            
        Returns:
            True if recovery was successful
        """
        try:
            # Try alternative method
            alternative_method = not original_method
            success = self.text_inserter.insert_text(text, alternative_method, app_name)
            
            if success:
                logger.info(f"Recovery successful using {'clipboard' if alternative_method else 'direct'} method")
                return True
            
            # Try with different timing
            time.sleep(0.5)  # Wait longer
            success = self.text_inserter.insert_text(text, original_method, app_name)
            
            if success:
                logger.info("Recovery successful with adjusted timing")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Recovery attempt failed: {e}")
            return False
    
    def _attempt_error_recovery(self, text: str, error_type: str, error: Exception) -> bool:
        """
        Attempt recovery for specific error types.
        
        Args:
            text: Text to insert
            error_type: Type of error encountered
            error: The exception that occurred
            
        Returns:
            True if recovery was successful
        """
        strategy = self.recovery_strategies.get(error_type, self.recovery_strategies['unknown_error'])
        return strategy(text, error)
    
    def _handle_clipboard_error(self, text: str, error: Exception) -> bool:
        """Handle clipboard-related errors."""
        try:
            logger.info("Attempting clipboard error recovery")
            
            # Try direct typing instead
            success = self.text_inserter.insert_text(text, use_clipboard=False)
            
            if success:
                logger.info("Clipboard error recovery successful using direct typing")
                return True
            
            # Try with clipboard reset
            import pyperclip
            pyperclip.copy('')  # Clear clipboard
            time.sleep(0.1)
            
            success = self.text_inserter.insert_text(text, use_clipboard=True)
            return success
            
        except Exception as e:
            logger.error(f"Clipboard error recovery failed: {e}")
            return False
    
    def _handle_typing_error(self, text: str, error: Exception) -> bool:
        """Handle typing-related errors."""
        try:
            logger.info("Attempting typing error recovery")
            
            # Try clipboard method instead
            success = self.text_inserter.insert_text(text, use_clipboard=True)
            
            if success:
                logger.info("Typing error recovery successful using clipboard")
                return True
            
            # Try with slower typing
            import pyautogui
            original_pause = pyautogui.PAUSE
            pyautogui.PAUSE = 0.2  # Slower typing
            
            try:
                success = self.text_inserter.insert_text(text, use_clipboard=False)
                return success
            finally:
                pyautogui.PAUSE = original_pause
            
        except Exception as e:
            logger.error(f"Typing error recovery failed: {e}")
            return False
    
    def _handle_window_error(self, text: str, error: Exception) -> bool:
        """Handle window-related errors."""
        try:
            logger.info("Attempting window error recovery")
            
            # Check if window is still active
            active_window = self.cursor_detector.get_active_window()
            if not active_window:
                logger.warning("No active window detected")
                return False
            
            # Try to focus the window
            active_window.activate()
            time.sleep(0.2)
            
            # Attempt insertion
            success = self.text_inserter.insert_text(text, use_clipboard=True)
            return success
            
        except Exception as e:
            logger.error(f"Window error recovery failed: {e}")
            return False
    
    def _handle_permission_error(self, text: str, error: Exception) -> bool:
        """Handle permission-related errors."""
        try:
            logger.info("Attempting permission error recovery")
            
            # Try with different method
            success = self.text_inserter.insert_text(text, use_clipboard=False)
            
            if success:
                logger.info("Permission error recovery successful")
                return True
            
            # Try with elevated permissions (if possible)
            logger.warning("Permission error recovery failed - may need elevated permissions")
            return False
            
        except Exception as e:
            logger.error(f"Permission error recovery failed: {e}")
            return False
    
    def _handle_timeout_error(self, text: str, error: Exception) -> bool:
        """Handle timeout-related errors."""
        try:
            logger.info("Attempting timeout error recovery")
            
            # Try with longer delays
            import pyautogui
            original_pause = pyautogui.PAUSE
            pyautogui.PAUSE = 0.3  # Longer delays
            
            try:
                success = self.text_inserter.insert_text(text, use_clipboard=True)
                return success
            finally:
                pyautogui.PAUSE = original_pause
            
        except Exception as e:
            logger.error(f"Timeout error recovery failed: {e}")
            return False
    
    def _handle_unknown_error(self, text: str, error: Exception) -> bool:
        """Handle unknown errors."""
        try:
            logger.info("Attempting unknown error recovery")
            
            # Try both methods with delays
            time.sleep(0.5)
            
            # Try clipboard first
            success = self.text_inserter.insert_text(text, use_clipboard=True)
            if success:
                return True
            
            # Try direct typing
            time.sleep(0.5)
            success = self.text_inserter.insert_text(text, use_clipboard=False)
            return success
            
        except Exception as e:
            logger.error(f"Unknown error recovery failed: {e}")
            return False
    
    def _classify_error(self, error: Exception) -> str:
        """Classify the type of error for appropriate recovery."""
        error_str = str(error).lower()
        
        if 'clipboard' in error_str or 'permission' in error_str:
            return 'clipboard_error'
        elif 'typing' in error_str or 'keyboard' in error_str:
            return 'typing_error'
        elif 'window' in error_str or 'focus' in error_str:
            return 'window_error'
        elif 'permission' in error_str or 'access' in error_str:
            return 'permission_error'
        elif 'timeout' in error_str or 'timed' in error_str:
            return 'timeout_error'
        else:
            return 'unknown_error'
    
    def _add_to_undo_stack(self, text: str, app_name: Optional[str]):
        """Add insertion to undo stack."""
        undo_item = {
            'text': text,
            'app_name': app_name,
            'timestamp': time.time(),
            'method': 'recovery'
        }
        
        self.undo_stack.append(undo_item)
        
        # Keep stack size manageable
        if len(self.undo_stack) > self.max_undo_stack:
            self.undo_stack.pop(0)
    
    def undo_last_insertion(self) -> Dict[str, Any]:
        """
        Undo the last text insertion with error handling.
        
        Returns:
            Dictionary with undo results
        """
        result = {
            'success': False,
            'error_message': None,
            'undo_item': None
        }
        
        try:
            # Use the text inserter's undo functionality
            success = self.text_inserter.undo_last_insertion()
            
            if success:
                result['success'] = True
                if self.undo_stack:
                    result['undo_item'] = self.undo_stack.pop()
                logger.info("Undo successful")
            else:
                result['error_message'] = "No insertion to undo"
                logger.warning("No insertion to undo")
            
        except Exception as e:
            result['error_message'] = str(e)
            logger.error(f"Undo failed: {e}")
        
        return result
    
    def _log_error(self, result: Dict[str, Any]):
        """Log error for analysis and improvement."""
        error_entry = {
            'timestamp': time.time(),
            'error_type': result.get('error_type'),
            'error_message': result.get('error_message'),
            'recovery_attempted': result.get('recovery_attempted', False),
            'recovery_successful': result.get('recovery_successful', False)
        }
        
        self.error_history.append(error_entry)
        
        # Keep history size manageable
        if len(self.error_history) > self.max_error_history:
            self.error_history.pop(0)
        
        logger.debug(f"Error logged: {error_entry}")
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about errors and recovery attempts.
        
        Returns:
            Dictionary with error statistics
        """
        if not self.error_history:
            return {
                'total_errors': 0,
                'recovery_success_rate': 0.0,
                'most_common_error': None,
                'recent_errors': []
            }
        
        total_errors = len(self.error_history)
        successful_recoveries = sum(1 for e in self.error_history if e.get('recovery_successful', False))
        recovery_rate = successful_recoveries / total_errors if total_errors > 0 else 0.0
        
        # Find most common error type
        error_types = [e.get('error_type') for e in self.error_history if e.get('error_type')]
        most_common = max(set(error_types), key=error_types.count) if error_types else None
        
        return {
            'total_errors': total_errors,
            'recovery_success_rate': recovery_rate,
            'most_common_error': most_common,
            'recent_errors': self.error_history[-5:]  # Last 5 errors
        }
    
    def clear_error_history(self):
        """Clear error history."""
        self.error_history.clear()
        logger.debug("Error history cleared")
    
    def get_undo_stack_info(self) -> Dict[str, Any]:
        """
        Get information about the undo stack.
        
        Returns:
            Dictionary with undo stack information
        """
        return {
            'stack_size': len(self.undo_stack),
            'max_size': self.max_undo_stack,
            'recent_items': self.undo_stack[-3:] if self.undo_stack else []
        } 
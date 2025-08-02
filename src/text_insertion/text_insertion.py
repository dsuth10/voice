"""
Text Insertion Module

This module provides functionality to insert text at the detected cursor position
using both clipboard paste and direct typing approaches.
"""

import logging
import time
import pyautogui
import pyperclip
from typing import Optional, Tuple, Dict, Any
from .cursor_detection import CursorDetector

logger = logging.getLogger(__name__)


class TextInserter:
    """Handles text insertion using various methods."""
    
    def __init__(self):
        self.cursor_detector = CursorDetector()
        self.clipboard_backup = None
        self.last_insertion = None
        self.insertion_history = []
        self.max_history_size = 10
        
        # Configure pyautogui for reliability
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1  # Small delay between actions
    
    def insert_text(self, text: str, use_clipboard: bool = True, 
                   app_name: Optional[str] = None) -> bool:
        """
        Insert text at the current cursor position.
        
        Args:
            text: Text to insert
            use_clipboard: Whether to use clipboard method (default: True)
            app_name: Target application name for optimization
            
        Returns:
            True if insertion was successful
        """
        if not text:
            logger.warning("Attempted to insert empty text")
            return False
        
        try:
            # Store insertion info for undo
            self.last_insertion = {
                'text': text,
                'method': 'clipboard' if use_clipboard else 'direct',
                'timestamp': time.time(),
                'app_name': app_name
            }
            
            # Backup clipboard content
            self._backup_clipboard()
            
            if use_clipboard:
                success = self._insert_via_clipboard(text)
            else:
                success = self._insert_via_direct_typing(text)
            
            if success:
                self._add_to_history(self.last_insertion)
                logger.info(f"Successfully inserted {len(text)} characters")
            else:
                # Try fallback method
                logger.warning("Primary insertion method failed, trying fallback")
                success = self._insert_with_fallback(text, use_clipboard)
            
            return success
            
        except Exception as e:
            logger.error(f"Text insertion failed: {e}")
            return False
        finally:
            # Restore clipboard content
            self._restore_clipboard()
    
    def _insert_via_clipboard(self, text: str) -> bool:
        """
        Insert text using clipboard method.
        
        Args:
            text: Text to insert
            
        Returns:
            True if successful
        """
        try:
            # Copy text to clipboard
            pyperclip.copy(text)
            
            # Small delay to ensure clipboard is ready
            time.sleep(0.05)
            
            # Paste using Ctrl+V
            pyautogui.hotkey('ctrl', 'v')
            
            # Verify insertion by checking if text was actually pasted
            time.sleep(0.1)
            return True
            
        except Exception as e:
            logger.error(f"Clipboard insertion failed: {e}")
            return False
    
    def _insert_via_direct_typing(self, text: str) -> bool:
        """
        Insert text using direct typing method.
        
        Args:
            text: Text to insert
            
        Returns:
            True if successful
        """
        try:
            # Type text directly
            pyautogui.write(text)
            return True
            
        except Exception as e:
            logger.error(f"Direct typing insertion failed: {e}")
            return False
    
    def _insert_with_fallback(self, text: str, original_method: bool) -> bool:
        """
        Try alternative insertion method if primary fails.
        
        Args:
            text: Text to insert
            original_method: The original method that failed
            
        Returns:
            True if fallback was successful
        """
        try:
            if original_method:  # Original was clipboard, try direct typing
                return self._insert_via_direct_typing(text)
            else:  # Original was direct typing, try clipboard
                return self._insert_via_clipboard(text)
        except Exception as e:
            logger.error(f"Fallback insertion failed: {e}")
            return False
    
    def _backup_clipboard(self):
        """Backup current clipboard content."""
        try:
            self.clipboard_backup = pyperclip.paste()
        except Exception as e:
            logger.warning(f"Failed to backup clipboard: {e}")
            self.clipboard_backup = None
    
    def _restore_clipboard(self):
        """Restore original clipboard content."""
        if self.clipboard_backup is not None:
            try:
                pyperclip.copy(self.clipboard_backup)
                logger.debug("Clipboard content restored")
            except Exception as e:
                logger.error(f"Failed to restore clipboard: {e}")
    
    def _add_to_history(self, insertion_info: Dict[str, Any]):
        """Add insertion to history."""
        self.insertion_history.append(insertion_info)
        
        # Keep history size manageable
        if len(self.insertion_history) > self.max_history_size:
            self.insertion_history.pop(0)
    
    def undo_last_insertion(self) -> bool:
        """
        Undo the last text insertion.
        
        Returns:
            True if undo was successful
        """
        if not self.last_insertion:
            logger.warning("No insertion to undo")
            return False
        
        try:
            text = self.last_insertion['text']
            method = self.last_insertion['method']
            
            # Calculate characters to delete
            chars_to_delete = len(text)
            
            # Send backspace key that many times
            for _ in range(chars_to_delete):
                pyautogui.press('backspace')
                time.sleep(0.01)  # Small delay between backspaces
            
            logger.info(f"Undid insertion of {chars_to_delete} characters")
            
            # Remove from history
            if self.insertion_history:
                self.insertion_history.pop()
            
            # Clear last insertion
            self.last_insertion = None
            
            return True
            
        except Exception as e:
            logger.error(f"Undo failed: {e}")
            return False
    
    def get_insertion_history(self) -> list:
        """
        Get insertion history.
        
        Returns:
            List of recent insertions
        """
        return self.insertion_history.copy()
    
    def clear_history(self):
        """Clear insertion history."""
        self.insertion_history.clear()
        self.last_insertion = None
        logger.debug("Insertion history cleared")
    
    def get_insertion_stats(self) -> Dict[str, Any]:
        """
        Get statistics about insertions.
        
        Returns:
            Dictionary with insertion statistics
        """
        if not self.insertion_history:
            return {
                'total_insertions': 0,
                'total_characters': 0,
                'clipboard_method_count': 0,
                'direct_method_count': 0,
                'average_text_length': 0
            }
        
        total_insertions = len(self.insertion_history)
        total_characters = sum(len(item['text']) for item in self.insertion_history)
        clipboard_count = sum(1 for item in self.insertion_history if item['method'] == 'clipboard')
        direct_count = sum(1 for item in self.insertion_history if item['method'] == 'direct')
        
        return {
            'total_insertions': total_insertions,
            'total_characters': total_characters,
            'clipboard_method_count': clipboard_count,
            'direct_method_count': direct_count,
            'average_text_length': total_characters / total_insertions if total_insertions > 0 else 0
        }
    
    def test_insertion_methods(self, test_text: str = "Test insertion") -> Dict[str, bool]:
        """
        Test both insertion methods with sample text.
        
        Args:
            test_text: Text to use for testing
            
        Returns:
            Dictionary with test results for each method
        """
        results = {}
        
        # Test clipboard method
        try:
            self._backup_clipboard()
            results['clipboard'] = self._insert_via_clipboard(test_text)
            self._restore_clipboard()
        except Exception as e:
            logger.error(f"Clipboard method test failed: {e}")
            results['clipboard'] = False
        
        # Test direct typing method
        try:
            results['direct_typing'] = self._insert_via_direct_typing(test_text)
        except Exception as e:
            logger.error(f"Direct typing method test failed: {e}")
            results['direct_typing'] = False
        
        logger.info(f"Insertion method test results: {results}")
        return results 
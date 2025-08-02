"""
Special Handling and Fallback Module

This module provides fallback mechanisms and special handling for applications
with non-standard text input methods or unusual behaviors.
"""

import logging
import time
import pyautogui
import pyperclip
from typing import Optional, Dict, Any, List, Callable
from .cursor_detection import CursorDetector
from .text_insertion import TextInserter
from .formatting import TextFormatter

logger = logging.getLogger(__name__)


class SpecialHandlingManager:
    """Manages special handling for unusual applications and fallback mechanisms."""
    
    def __init__(self):
        self.cursor_detector = CursorDetector()
        self.text_inserter = TextInserter()
        self.text_formatter = TextFormatter()
        self.special_apps = self._initialize_special_applications()
        self.fallback_strategies = self._initialize_fallback_strategies()
        self.unsupported_apps = set()
        
    def _initialize_special_applications(self) -> Dict[str, Dict[str, Any]]:
        """Initialize special handling for specific applications."""
        return {
            'Secure Applications': {
                'Citrix': {
                    'description': 'Virtual desktop environment',
                    'handling': 'direct_typing_only',
                    'delays': 0.2,
                    'retry_count': 3
                },
                'VMware Horizon': {
                    'description': 'Virtual desktop environment',
                    'handling': 'direct_typing_only',
                    'delays': 0.2,
                    'retry_count': 3
                },
                'Remote Desktop': {
                    'description': 'Windows Remote Desktop',
                    'handling': 'direct_typing_only',
                    'delays': 0.15,
                    'retry_count': 2
                }
            },
            'Development Tools': {
                'Visual Studio': {
                    'description': 'IDE with complex input handling',
                    'handling': 'clipboard_preferred',
                    'delays': 0.1,
                    'retry_count': 2
                },
                'IntelliJ IDEA': {
                    'description': 'Java IDE with smart completion',
                    'handling': 'clipboard_preferred',
                    'delays': 0.1,
                    'retry_count': 2
                },
                'Eclipse': {
                    'description': 'Java IDE',
                    'handling': 'clipboard_preferred',
                    'delays': 0.1,
                    'retry_count': 2
                }
            },
            'Terminal Applications': {
                'Command Prompt': {
                    'description': 'Windows command line',
                    'handling': 'direct_typing_only',
                    'delays': 0.05,
                    'retry_count': 1
                },
                'PowerShell': {
                    'description': 'Windows PowerShell',
                    'handling': 'direct_typing_only',
                    'delays': 0.05,
                    'retry_count': 1
                },
                'Windows Terminal': {
                    'description': 'Modern terminal application',
                    'handling': 'direct_typing_only',
                    'delays': 0.05,
                    'retry_count': 1
                }
            },
            'Gaming Applications': {
                'Steam': {
                    'description': 'Gaming platform',
                    'handling': 'clipboard_preferred',
                    'delays': 0.1,
                    'retry_count': 2
                },
                'Discord': {
                    'description': 'Gaming chat application',
                    'handling': 'clipboard_preferred',
                    'delays': 0.1,
                    'retry_count': 2
                }
            },
            'Web Applications': {
                'Web-based Editors': {
                    'description': 'Online text editors',
                    'handling': 'clipboard_preferred',
                    'delays': 0.1,
                    'retry_count': 2
                },
                'Cloud IDEs': {
                    'description': 'Cloud-based development environments',
                    'handling': 'clipboard_preferred',
                    'delays': 0.1,
                    'retry_count': 2
                }
            }
        }
    
    def _initialize_fallback_strategies(self) -> Dict[str, Callable]:
        """Initialize fallback strategies for different scenarios."""
        return {
            'character_by_character': self._insert_character_by_character,
            'word_by_word': self._insert_word_by_word,
            'line_by_line': self._insert_line_by_line,
            'simulated_typing': self._simulated_typing,
            'clipboard_reset': self._clipboard_reset_strategy,
            'window_refocus': self._window_refocus_strategy
        }
    
    def insert_text_with_special_handling(self, text: str, app_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Insert text with special handling for unusual applications.
        
        Args:
            text: Text to insert
            app_name: Target application name
            
        Returns:
            Dictionary with insertion results
        """
        result = {
            'success': False,
            'method_used': None,
            'special_handling': False,
            'fallback_used': False,
            'error_message': None
        }
        
        # Detect application if not provided
        if app_name is None:
            window_info = self.cursor_detector.get_window_info()
            app_name = window_info.get('app_name', 'Unknown')
        
        # Check if application requires special handling
        special_config = self._get_special_config(app_name)
        
        if special_config:
            result['special_handling'] = True
            success = self._handle_special_application(text, app_name, special_config)
            
            if success:
                result['success'] = True
                result['method_used'] = special_config.get('handling', 'special')
                logger.info(f"Special handling successful for {app_name}")
                return result
        
        # Try standard insertion first
        success = self.text_inserter.insert_text(text, use_clipboard=True, app_name=app_name)
        
        if success:
            result['success'] = True
            result['method_used'] = 'standard'
            return result
        
        # Standard method failed, try fallback strategies
        result['fallback_used'] = True
        fallback_success = self._try_fallback_strategies(text, app_name)
        
        if fallback_success:
            result['success'] = True
            result['method_used'] = 'fallback'
            logger.info(f"Fallback strategy successful for {app_name}")
        else:
            result['error_message'] = "All insertion methods failed"
            logger.error(f"All insertion methods failed for {app_name}")
        
        return result
    
    def _get_special_config(self, app_name: str) -> Optional[Dict[str, Any]]:
        """Get special configuration for an application."""
        for category, apps in self.special_apps.items():
            for app, config in apps.items():
                if app.lower() in app_name.lower() or app_name.lower() in app.lower():
                    return config
        return None
    
    def _handle_special_application(self, text: str, app_name: str, config: Dict[str, Any]) -> bool:
        """
        Handle insertion for applications requiring special handling.
        
        Args:
            text: Text to insert
            app_name: Application name
            config: Special configuration
            
        Returns:
            True if successful
        """
        handling = config.get('handling', 'direct_typing_only')
        delays = config.get('delays', 0.1)
        retry_count = config.get('retry_count', 2)
        
        # Apply delays
        original_pause = pyautogui.PAUSE
        pyautogui.PAUSE = delays
        
        try:
            for attempt in range(retry_count + 1):
                success = False
                
                if handling == 'direct_typing_only':
                    success = self.text_inserter.insert_text(text, use_clipboard=False, app_name=app_name)
                elif handling == 'clipboard_preferred':
                    success = self.text_inserter.insert_text(text, use_clipboard=True, app_name=app_name)
                    if not success:
                        success = self.text_inserter.insert_text(text, use_clipboard=False, app_name=app_name)
                
                if success:
                    return True
                
                if attempt < retry_count:
                    time.sleep(0.5)  # Wait before retry
            
            return False
            
        finally:
            pyautogui.PAUSE = original_pause
    
    def _try_fallback_strategies(self, text: str, app_name: str) -> bool:
        """
        Try various fallback strategies for text insertion.
        
        Args:
            text: Text to insert
            app_name: Application name
            
        Returns:
            True if any strategy was successful
        """
        strategies = [
            'character_by_character',
            'word_by_word',
            'line_by_line',
            'simulated_typing',
            'clipboard_reset',
            'window_refocus'
        ]
        
        for strategy in strategies:
            try:
                strategy_func = self.fallback_strategies.get(strategy)
                if strategy_func:
                    success = strategy_func(text, app_name)
                    if success:
                        logger.info(f"Fallback strategy '{strategy}' successful")
                        return True
            except Exception as e:
                logger.error(f"Fallback strategy '{strategy}' failed: {e}")
        
        return False
    
    def _insert_character_by_character(self, text: str, app_name: str) -> bool:
        """Insert text character by character."""
        try:
            for char in text:
                pyautogui.write(char)
                time.sleep(0.01)  # Small delay between characters
            return True
        except Exception as e:
            logger.error(f"Character-by-character insertion failed: {e}")
            return False
    
    def _insert_word_by_word(self, text: str, app_name: str) -> bool:
        """Insert text word by word."""
        try:
            words = text.split()
            for word in words:
                pyautogui.write(word + ' ')
                time.sleep(0.05)  # Small delay between words
            return True
        except Exception as e:
            logger.error(f"Word-by-word insertion failed: {e}")
            return False
    
    def _insert_line_by_line(self, text: str, app_name: str) -> bool:
        """Insert text line by line."""
        try:
            lines = text.split('\n')
            for line in lines:
                pyautogui.write(line)
                pyautogui.press('enter')
                time.sleep(0.1)  # Delay between lines
            return True
        except Exception as e:
            logger.error(f"Line-by-line insertion failed: {e}")
            return False
    
    def _simulated_typing(self, text: str, app_name: str) -> bool:
        """Simulate human-like typing with variable delays."""
        try:
            import random
            
            for char in text:
                pyautogui.write(char)
                # Random delay to simulate human typing
                time.sleep(random.uniform(0.01, 0.03))
            return True
        except Exception as e:
            logger.error(f"Simulated typing failed: {e}")
            return False
    
    def _clipboard_reset_strategy(self, text: str, app_name: str) -> bool:
        """Reset clipboard and try insertion again."""
        try:
            # Clear clipboard
            pyperclip.copy('')
            time.sleep(0.1)
            
            # Try insertion again
            success = self.text_inserter.insert_text(text, use_clipboard=True, app_name=app_name)
            return success
        except Exception as e:
            logger.error(f"Clipboard reset strategy failed: {e}")
            return False
    
    def _window_refocus_strategy(self, text: str, app_name: str) -> bool:
        """Refocus window and try insertion again."""
        try:
            # Get active window and refocus
            active_window = self.cursor_detector.get_active_window()
            if active_window:
                active_window.activate()
                time.sleep(0.2)
                
                # Try insertion again
                success = self.text_inserter.insert_text(text, use_clipboard=True, app_name=app_name)
                return success
            
            return False
        except Exception as e:
            logger.error(f"Window refocus strategy failed: {e}")
            return False
    
    def add_special_application(self, app_name: str, config: Dict[str, Any]):
        """
        Add a new application to special handling.
        
        Args:
            app_name: Name of the application
            config: Special configuration
        """
        # Add to a default category
        if 'Special Applications' not in self.special_apps:
            self.special_apps['Special Applications'] = {}
        
        self.special_apps['Special Applications'][app_name] = config
        logger.info(f"Added special handling for {app_name}")
    
    def remove_special_application(self, app_name: str):
        """
        Remove an application from special handling.
        
        Args:
            app_name: Name of the application to remove
        """
        for category, apps in self.special_apps.items():
            if app_name in apps:
                del apps[app_name]
                logger.info(f"Removed special handling for {app_name}")
                break
    
    def mark_application_unsupported(self, app_name: str):
        """
        Mark an application as unsupported.
        
        Args:
            app_name: Name of the application
        """
        self.unsupported_apps.add(app_name)
        logger.warning(f"Marked {app_name} as unsupported")
    
    def is_application_unsupported(self, app_name: str) -> bool:
        """
        Check if an application is marked as unsupported.
        
        Args:
            app_name: Name of the application
            
        Returns:
            True if application is unsupported
        """
        return app_name in self.unsupported_apps
    
    def get_special_applications(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all special applications and their configurations.
        
        Returns:
            Dictionary of special applications
        """
        return self.special_apps.copy()
    
    def get_unsupported_applications(self) -> List[str]:
        """
        Get list of unsupported applications.
        
        Returns:
            List of unsupported application names
        """
        return list(self.unsupported_apps)
    
    def test_application_compatibility(self, app_name: str, test_text: str = "Test") -> Dict[str, Any]:
        """
        Test compatibility of an application with text insertion.
        
        Args:
            app_name: Name of the application to test
            test_text: Text to use for testing
            
        Returns:
            Dictionary with test results
        """
        result = {
            'app_name': app_name,
            'standard_method': False,
            'special_handling': False,
            'fallback_methods': [],
            'recommended_method': None,
            'compatibility_score': 0
        }
        
        # Test standard method
        try:
            success = self.text_inserter.insert_text(test_text, use_clipboard=True, app_name=app_name)
            result['standard_method'] = success
        except Exception as e:
            logger.error(f"Standard method test failed for {app_name}: {e}")
        
        # Test special handling
        special_config = self._get_special_config(app_name)
        if special_config:
            result['special_handling'] = True
            try:
                success = self._handle_special_application(test_text, app_name, special_config)
                if success:
                    result['recommended_method'] = 'special_handling'
            except Exception as e:
                logger.error(f"Special handling test failed for {app_name}: {e}")
        
        # Test fallback methods
        for strategy_name in self.fallback_strategies.keys():
            try:
                strategy_func = self.fallback_strategies.get(strategy_name)
                if strategy_func:
                    success = strategy_func(test_text, app_name)
                    if success:
                        result['fallback_methods'].append(strategy_name)
            except Exception as e:
                logger.error(f"Fallback method '{strategy_name}' test failed for {app_name}: {e}")
        
        # Calculate compatibility score
        score = 0
        if result['standard_method']:
            score += 50
        if result['special_handling']:
            score += 30
        if result['fallback_methods']:
            score += len(result['fallback_methods']) * 10
        
        result['compatibility_score'] = min(score, 100)
        
        # Set recommended method
        if not result['recommended_method']:
            if result['standard_method']:
                result['recommended_method'] = 'standard'
            elif result['fallback_methods']:
                result['recommended_method'] = result['fallback_methods'][0]
            else:
                result['recommended_method'] = 'unsupported'
        
        return result 
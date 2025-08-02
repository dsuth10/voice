"""
Text Insertion System

This module provides the main TextInsertionSystem class that integrates all
components for comprehensive text insertion functionality.
"""

import logging
from typing import Optional, Dict, Any, List
from .cursor_detection import CursorDetector
from .text_insertion import TextInserter
from .formatting import TextFormatter
from .error_recovery import ErrorRecoveryManager
from .special_handling import SpecialHandlingManager

logger = logging.getLogger(__name__)


class TextInsertionSystem:
    """Main text insertion system that integrates all components."""
    
    def __init__(self):
        self.cursor_detector = CursorDetector()
        self.text_inserter = TextInserter()
        self.text_formatter = TextFormatter()
        self.error_recovery = ErrorRecoveryManager()
        self.special_handling = SpecialHandlingManager()
        
        # Configuration
        self.enable_formatting = True
        self.enable_error_recovery = True
        self.enable_special_handling = True
        self.default_method = 'clipboard'  # 'clipboard' or 'direct'
        
        logger.info("Text Insertion System initialized")
    
    def insert_text(self, text: str, app_name: Optional[str] = None,
                   use_formatting: bool = True, use_recovery: bool = True) -> Dict[str, Any]:
        """
        Insert text with full system integration.
        
        Args:
            text: Text to insert
            app_name: Target application name (auto-detected if None)
            use_formatting: Whether to apply application-specific formatting
            use_recovery: Whether to use error recovery mechanisms
            
        Returns:
            Dictionary with comprehensive insertion results
        """
        result = {
            'success': False,
            'method_used': None,
            'app_detected': None,
            'formatting_applied': False,
            'recovery_used': False,
            'special_handling': False,
            'error_message': None,
            'performance_metrics': {}
        }
        
        try:
            # Step 1: Detect application and cursor position
            window_info = self.cursor_detector.get_window_info()
            app_name = app_name or window_info.get('app_name', 'Unknown')
            result['app_detected'] = app_name
            
            logger.info(f"Inserting text into {app_name}")
            
            # Step 2: Apply formatting if enabled
            if use_formatting and self.enable_formatting:
                original_text = text
                text = self.text_formatter.format_text_for_application(text, app_name)
                result['formatting_applied'] = text != original_text
                
                if result['formatting_applied']:
                    logger.debug(f"Formatting applied for {app_name}")
            
            # Step 3: Check if application is unsupported
            if self.special_handling.is_application_unsupported(app_name):
                result['error_message'] = f"Application {app_name} is marked as unsupported"
                logger.warning(f"Attempted insertion into unsupported application: {app_name}")
                return result
            
            # Step 4: Insert text using appropriate method
            if use_recovery and self.enable_error_recovery:
                # Use error recovery manager
                recovery_result = self.error_recovery.insert_text_with_recovery(
                    text, self.default_method == 'clipboard', app_name
                )
                
                result.update(recovery_result)
                result['recovery_used'] = True
                
            elif self.enable_special_handling:
                # Use special handling manager
                special_result = self.special_handling.insert_text_with_special_handling(text, app_name)
                
                result.update(special_result)
                result['special_handling'] = special_result.get('special_handling', False)
                
            else:
                # Use basic text inserter
                success = self.text_inserter.insert_text(
                    text, self.default_method == 'clipboard', app_name
                )
                
                result['success'] = success
                result['method_used'] = self.default_method
            
            # Step 5: Log performance metrics
            result['performance_metrics'] = self._get_performance_metrics()
            
            if result['success']:
                logger.info(f"Text insertion successful using {result['method_used']} method")
            else:
                logger.error(f"Text insertion failed: {result.get('error_message', 'Unknown error')}")
            
        except Exception as e:
            result['error_message'] = str(e)
            logger.error(f"Text insertion system error: {e}")
        
        return result
    
    def undo_last_insertion(self) -> Dict[str, Any]:
        """
        Undo the last text insertion.
        
        Returns:
            Dictionary with undo results
        """
        return self.error_recovery.undo_last_insertion()
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get comprehensive system status and statistics.
        
        Returns:
            Dictionary with system status
        """
        # Get statistics from all components
        insertion_stats = self.text_inserter.get_insertion_stats()
        error_stats = self.error_recovery.get_error_statistics()
        undo_info = self.error_recovery.get_undo_stack_info()
        
        # Get supported applications
        supported_apps = self.cursor_detector.get_supported_applications()
        formatting_apps = self.text_formatter.get_supported_applications()
        special_apps = self.special_handling.get_special_applications()
        unsupported_apps = self.special_handling.get_unsupported_applications()
        
        return {
            'system_components': {
                'cursor_detection': 'active',
                'text_insertion': 'active',
                'formatting': 'active' if self.enable_formatting else 'disabled',
                'error_recovery': 'active' if self.enable_error_recovery else 'disabled',
                'special_handling': 'active' if self.enable_special_handling else 'disabled'
            },
            'insertion_statistics': insertion_stats,
            'error_statistics': error_stats,
            'undo_stack_info': undo_info,
            'application_support': {
                'supported_applications': len(supported_apps),
                'formatting_applications': len(formatting_apps),
                'special_applications': len(special_apps),
                'unsupported_applications': len(unsupported_apps)
            },
            'configuration': {
                'enable_formatting': self.enable_formatting,
                'enable_error_recovery': self.enable_error_recovery,
                'enable_special_handling': self.enable_special_handling,
                'default_method': self.default_method
            }
        }
    
    def test_application_compatibility(self, app_name: str) -> Dict[str, Any]:
        """
        Test compatibility of an application with the text insertion system.
        
        Args:
            app_name: Name of the application to test
            
        Returns:
            Dictionary with comprehensive test results
        """
        test_results = {
            'app_name': app_name,
            'cursor_detection': False,
            'text_insertion': False,
            'formatting': False,
            'error_recovery': False,
            'special_handling': False,
            'overall_compatibility': 0
        }
        
        try:
            # Test cursor detection
            window_info = self.cursor_detector.get_window_info()
            test_results['cursor_detection'] = bool(window_info)
            
            # Test text insertion
            test_text = "Test insertion"
            insertion_result = self.text_inserter.insert_text(test_text, use_clipboard=True, app_name=app_name)
            test_results['text_insertion'] = insertion_result
            
            # Test formatting
            formatted_text = self.text_formatter.format_text_for_application(test_text, app_name)
            test_results['formatting'] = formatted_text != test_text
            
            # Test error recovery
            recovery_result = self.error_recovery.insert_text_with_recovery(test_text, True, app_name)
            test_results['error_recovery'] = recovery_result.get('success', False)
            
            # Test special handling
            special_result = self.special_handling.test_application_compatibility(app_name, test_text)
            test_results['special_handling'] = special_result.get('compatibility_score', 0) > 0
            
            # Calculate overall compatibility
            components = ['cursor_detection', 'text_insertion', 'formatting', 'error_recovery', 'special_handling']
            score = sum(test_results[comp] for comp in components) / len(components) * 100
            test_results['overall_compatibility'] = score
            
        except Exception as e:
            logger.error(f"Application compatibility test failed for {app_name}: {e}")
            test_results['error'] = str(e)
        
        return test_results
    
    def configure_system(self, **kwargs):
        """
        Configure the text insertion system.
        
        Args:
            **kwargs: Configuration options
                - enable_formatting: Enable/disable text formatting
                - enable_error_recovery: Enable/disable error recovery
                - enable_special_handling: Enable/disable special handling
                - default_method: Set default insertion method ('clipboard' or 'direct')
        """
        if 'enable_formatting' in kwargs:
            self.enable_formatting = kwargs['enable_formatting']
            logger.info(f"Formatting {'enabled' if self.enable_formatting else 'disabled'}")
        
        if 'enable_error_recovery' in kwargs:
            self.enable_error_recovery = kwargs['enable_error_recovery']
            logger.info(f"Error recovery {'enabled' if self.enable_error_recovery else 'disabled'}")
        
        if 'enable_special_handling' in kwargs:
            self.enable_special_handling = kwargs['enable_special_handling']
            logger.info(f"Special handling {'enabled' if self.enable_special_handling else 'disabled'}")
        
        if 'default_method' in kwargs:
            method = kwargs['default_method']
            if method in ['clipboard', 'direct']:
                self.default_method = method
                logger.info(f"Default method set to {self.default_method}")
            else:
                logger.warning(f"Invalid default method: {method}")
    
    def add_special_application(self, app_name: str, config: Dict[str, Any]):
        """
        Add a new application to special handling.
        
        Args:
            app_name: Name of the application
            config: Special configuration
        """
        self.special_handling.add_special_application(app_name, config)
    
    def mark_application_unsupported(self, app_name: str):
        """
        Mark an application as unsupported.
        
        Args:
            app_name: Name of the application
        """
        self.special_handling.mark_application_unsupported(app_name)
    
    def get_supported_applications(self) -> Dict[str, List[str]]:
        """
        Get all supported applications by category.
        
        Returns:
            Dictionary mapping categories to application lists
        """
        return {
            'Standard Applications': list(self.cursor_detector.get_supported_applications().keys()),
            'Formatting Applications': self.text_formatter.get_supported_applications(),
            'Special Applications': list(self.special_handling.get_special_applications().keys()),
            'Unsupported Applications': self.special_handling.get_unsupported_applications()
        }
    
    def _get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for the system."""
        # This would typically include timing information
        # For now, return basic metrics
        return {
            'insertion_count': self.text_inserter.get_insertion_stats().get('total_insertions', 0),
            'error_count': self.error_recovery.get_error_statistics().get('total_errors', 0),
            'recovery_success_rate': self.error_recovery.get_error_statistics().get('recovery_success_rate', 0.0)
        }
    
    def clear_history(self):
        """Clear all history and statistics."""
        self.text_inserter.clear_history()
        self.error_recovery.clear_error_history()
        logger.info("System history cleared")
    
    def reset_system(self):
        """Reset the system to initial state."""
        self.clear_history()
        self.configure_system(
            enable_formatting=True,
            enable_error_recovery=True,
            enable_special_handling=True,
            default_method='clipboard'
        )
        logger.info("Text insertion system reset to initial state") 
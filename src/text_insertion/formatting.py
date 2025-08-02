"""
Application-Specific Formatting Module

This module provides functionality to detect the active application and apply
context-appropriate text formatting before insertion.
"""

import logging
import re
from typing import Optional, Dict, Any, List
from .cursor_detection import CursorDetector

logger = logging.getLogger(__name__)


class TextFormatter:
    """Handles application-specific text formatting."""
    
    def __init__(self):
        self.cursor_detector = CursorDetector()
        self.formatting_rules = self._initialize_formatting_rules()
        self.special_characters = {
            'smart_quotes': {'"': '"', '"': '"', "'": ''', "'": '''},
            'em_dash': {'--': '—'},
            'en_dash': {' - ': ' – '},
            'ellipsis': {'...': '…'},
            'copyright': {'(c)': '©'},
            'registered': {'(r)': '®'},
            'trademark': {'(tm)': '™'}
        }
    
    def _initialize_formatting_rules(self) -> Dict[str, Dict[str, Any]]:
        """Initialize formatting rules for different applications."""
        return {
            'Microsoft Word': {
                'preserve_formatting': True,
                'smart_quotes': True,
                'smart_dashes': True,
                'ellipsis': True,
                'symbols': True,
                'paragraph_breaks': True,
                'line_breaks': True,
                'max_length': 10000
            },
            'Microsoft Excel': {
                'preserve_formatting': False,
                'smart_quotes': False,
                'smart_dashes': False,
                'ellipsis': False,
                'symbols': False,
                'paragraph_breaks': False,
                'line_breaks': True,
                'max_length': 32000
            },
            'Microsoft PowerPoint': {
                'preserve_formatting': True,
                'smart_quotes': True,
                'smart_dashes': True,
                'ellipsis': True,
                'symbols': True,
                'paragraph_breaks': True,
                'line_breaks': True,
                'max_length': 5000
            },
            'Notepad': {
                'preserve_formatting': False,
                'smart_quotes': False,
                'smart_dashes': False,
                'ellipsis': False,
                'symbols': False,
                'paragraph_breaks': True,
                'line_breaks': True,
                'max_length': 100000
            },
            'Visual Studio Code': {
                'preserve_formatting': False,
                'smart_quotes': False,
                'smart_dashes': False,
                'ellipsis': False,
                'symbols': False,
                'paragraph_breaks': True,
                'line_breaks': True,
                'max_length': 100000
            },
            'Google Chrome': {
                'preserve_formatting': False,
                'smart_quotes': False,
                'smart_dashes': False,
                'ellipsis': False,
                'symbols': False,
                'paragraph_breaks': True,
                'line_breaks': True,
                'max_length': 100000
            },
            'Mozilla Firefox': {
                'preserve_formatting': False,
                'smart_quotes': False,
                'smart_dashes': False,
                'ellipsis': False,
                'symbols': False,
                'paragraph_breaks': True,
                'line_breaks': True,
                'max_length': 100000
            },
            'Microsoft Edge': {
                'preserve_formatting': False,
                'smart_quotes': False,
                'smart_dashes': False,
                'ellipsis': False,
                'symbols': False,
                'paragraph_breaks': True,
                'line_breaks': True,
                'max_length': 100000
            },
            'Outlook': {
                'preserve_formatting': True,
                'smart_quotes': True,
                'smart_dashes': True,
                'ellipsis': True,
                'symbols': True,
                'paragraph_breaks': True,
                'line_breaks': True,
                'max_length': 5000
            },
            'Teams': {
                'preserve_formatting': False,
                'smart_quotes': False,
                'smart_dashes': False,
                'ellipsis': False,
                'symbols': False,
                'paragraph_breaks': True,
                'line_breaks': True,
                'max_length': 1000
            },
            'Slack': {
                'preserve_formatting': False,
                'smart_quotes': False,
                'smart_dashes': False,
                'ellipsis': False,
                'symbols': False,
                'paragraph_breaks': True,
                'line_breaks': True,
                'max_length': 1000
            }
        }
    
    def format_text_for_application(self, text: str, app_name: Optional[str] = None) -> str:
        """
        Format text based on the target application.
        
        Args:
            text: Text to format
            app_name: Target application name. If None, detects automatically.
            
        Returns:
            Formatted text
        """
        if not text:
            return text
        
        # Detect application if not provided
        if app_name is None:
            window_info = self.cursor_detector.get_window_info()
            app_name = window_info.get('app_name', 'Unknown')
        
        # Get formatting rules for the application
        rules = self.formatting_rules.get(app_name, self.formatting_rules.get('Notepad', {}))
        
        logger.debug(f"Formatting text for {app_name} with rules: {rules}")
        
        # Apply formatting based on rules
        formatted_text = text
        
        if rules.get('smart_quotes', False):
            formatted_text = self._apply_smart_quotes(formatted_text)
        
        if rules.get('smart_dashes', False):
            formatted_text = self._apply_smart_dashes(formatted_text)
        
        if rules.get('ellipsis', False):
            formatted_text = self._apply_ellipsis(formatted_text)
        
        if rules.get('symbols', False):
            formatted_text = self._apply_symbols(formatted_text)
        
        # Handle paragraph and line breaks
        formatted_text = self._handle_breaks(formatted_text, rules)
        
        # Check length limits
        max_length = rules.get('max_length', 100000)
        if len(formatted_text) > max_length:
            logger.warning(f"Text truncated from {len(formatted_text)} to {max_length} characters for {app_name}")
            formatted_text = formatted_text[:max_length]
        
        return formatted_text
    
    def _apply_smart_quotes(self, text: str) -> str:
        """Apply smart quotes formatting."""
        # Replace straight quotes with curly quotes
        text = re.sub(r'\b"([^"]*)"\b', r'"\1"', text)  # Double quotes
        text = re.sub(r"\b'([^']*)'\b", r"'\1'", text)  # Single quotes
        
        return text
    
    def _apply_smart_dashes(self, text: str) -> str:
        """Apply smart dashes formatting."""
        # Replace double hyphens with em dash
        text = re.sub(r'--', '—', text)
        
        # Replace single hyphen with en dash in number ranges
        text = re.sub(r'(\d+)-(\d+)', r'\1–\2', text)
        
        return text
    
    def _apply_ellipsis(self, text: str) -> str:
        """Apply ellipsis formatting."""
        # Replace three dots with ellipsis
        text = re.sub(r'\.{3,}', '…', text)
        
        return text
    
    def _apply_symbols(self, text: str) -> str:
        """Apply symbol replacements."""
        # Copyright
        text = re.sub(r'\b\(c\)\b', '©', text, flags=re.IGNORECASE)
        
        # Registered trademark
        text = re.sub(r'\b\(r\)\b', '®', text, flags=re.IGNORECASE)
        
        # Trademark
        text = re.sub(r'\b\(tm\)\b', '™', text, flags=re.IGNORECASE)
        
        return text
    
    def _handle_breaks(self, text: str, rules: Dict[str, Any]) -> str:
        """Handle paragraph and line breaks based on application rules."""
        if not rules.get('paragraph_breaks', True):
            # Remove paragraph breaks
            text = text.replace('\n\n', ' ')
            text = text.replace('\r\n\r\n', ' ')
        
        if not rules.get('line_breaks', True):
            # Remove line breaks
            text = text.replace('\n', ' ')
            text = text.replace('\r\n', ' ')
        
        return text
    
    def get_application_rules(self, app_name: str) -> Dict[str, Any]:
        """
        Get formatting rules for a specific application.
        
        Args:
            app_name: Name of the application
            
        Returns:
            Dictionary of formatting rules
        """
        return self.formatting_rules.get(app_name, {})
    
    def add_application_rules(self, app_name: str, rules: Dict[str, Any]):
        """
        Add or update formatting rules for an application.
        
        Args:
            app_name: Name of the application
            rules: Dictionary of formatting rules
        """
        self.formatting_rules[app_name] = rules
        logger.info(f"Added formatting rules for {app_name}")
    
    def remove_application_rules(self, app_name: str):
        """
        Remove formatting rules for an application.
        
        Args:
            app_name: Name of the application to remove
        """
        if app_name in self.formatting_rules:
            del self.formatting_rules[app_name]
            logger.info(f"Removed formatting rules for {app_name}")
    
    def get_supported_applications(self) -> List[str]:
        """
        Get list of applications with formatting rules.
        
        Returns:
            List of supported application names
        """
        return list(self.formatting_rules.keys())
    
    def validate_text_for_application(self, text: str, app_name: str) -> Dict[str, Any]:
        """
        Validate text for a specific application.
        
        Args:
            text: Text to validate
            app_name: Target application name
            
        Returns:
            Dictionary with validation results
        """
        rules = self.get_application_rules(app_name)
        max_length = rules.get('max_length', 100000)
        
        validation = {
            'is_valid': True,
            'length': len(text),
            'max_length': max_length,
            'within_limits': len(text) <= max_length,
            'has_special_characters': bool(re.search(r'[^\x00-\x7F]', text)),
            'has_formatting': bool(re.search(r'[<>]', text)),  # Basic HTML/formatting detection
            'line_count': text.count('\n') + 1,
            'word_count': len(text.split())
        }
        
        if not validation['within_limits']:
            validation['is_valid'] = False
            validation['truncated_length'] = max_length
        
        return validation
    
    def get_formatting_preview(self, text: str, app_name: str) -> Dict[str, str]:
        """
        Get a preview of how text will be formatted for an application.
        
        Args:
            text: Original text
            app_name: Target application name
            
        Returns:
            Dictionary with original and formatted text
        """
        formatted = self.format_text_for_application(text, app_name)
        
        return {
            'original': text,
            'formatted': formatted,
            'changes_made': text != formatted,
            'length_difference': len(formatted) - len(text)
        } 
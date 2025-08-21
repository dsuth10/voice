"""
Application Context Awareness Implementation

This module provides functionality to detect the active application and adapt
text formatting and behavior based on the application context.
"""

import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

# ``pygetwindow`` is an optional dependency that is not available on all
# platforms (for example the execution environment used for these tests).
# Importing it unconditionally would raise a ``ModuleNotFoundError`` and make
# the whole context module unusable.  The tests only need the ability to import
# the module and, in some cases, gracefully handle the absence of window
# information.  To keep the public API the same we attempt to import
# ``pygetwindow`` but fall back to ``None`` when it isn't installed.
try:  # pragma: no cover - behaviour exercised indirectly in tests
    import pygetwindow as gw  # type: ignore
except Exception:  # pragma: no cover - triggered when dependency is missing
    gw = None  # type: ignore

logger = logging.getLogger(__name__)


@dataclass
class WindowInfo:
    """Information about a detected window."""
    title: str
    class_name: str
    is_active: bool
    is_minimized: bool
    is_maximized: bool


class ApplicationContext:
    """
    Detects the active application and provides context-specific formatting rules.
    
    This class uses pygetwindow to detect the currently active application
    and provides context-specific formatting templates and AI prompts.
    """
    
    def __init__(self):
        """Initialize the ApplicationContext with default patterns and templates."""
        # Define known application patterns for context detection
        self.app_patterns = {
            'email': ['outlook', 'thunderbird', 'gmail', 'mail', 'thunderbird', 'apple mail'],
            'document': ['word', 'writer', 'docs', 'pages', 'notepad', 'textedit', 'libreoffice'],
            'code': ['code', 'visual studio', 'intellij', 'pycharm', 'eclipse', 'sublime', 'atom', 'vim', 'emacs'],
            'browser': ['chrome', 'firefox', 'edge', 'safari', 'opera', 'brave'],
            'chat': ['teams', 'slack', 'discord', 'whatsapp', 'telegram', 'signal'],
            'presentation': ['powerpoint', 'keynote', 'impress', 'slides'],
            'spreadsheet': ['excel', 'calc', 'numbers', 'sheets'],
            'design': ['photoshop', 'illustrator', 'figma', 'sketch', 'canva'],
            'terminal': ['cmd', 'powershell', 'terminal', 'iterm', 'conemu', 'hyper']
        }
        
        # Define context-specific formatting templates
        self.formatting_templates = {
            'email': {
                'formal': True,
                'paragraphs': True,
                'greeting': True,
                'signature': False,
                'line_breaks': True,
                'capitalization': 'sentence'
            },
            'document': {
                'formal': True,
                'paragraphs': True,
                'academic': False,
                'line_breaks': True,
                'capitalization': 'sentence'
            },
            'code': {
                'comment_style': True,
                'technical': True,
                'concise': True,
                'line_breaks': False,
                'capitalization': 'lowercase'
            },
            'chat': {
                'formal': False,
                'concise': True,
                'conversational': True,
                'line_breaks': True,
                'capitalization': 'mixed'
            },
            'presentation': {
                'formal': True,
                'concise': True,
                'bullet_points': True,
                'line_breaks': True,
                'capitalization': 'title'
            },
            'spreadsheet': {
                'formal': True,
                'concise': True,
                'technical': True,
                'line_breaks': False,
                'capitalization': 'sentence'
            },
            'design': {
                'formal': False,
                'concise': True,
                'creative': True,
                'line_breaks': True,
                'capitalization': 'mixed'
            },
            'terminal': {
                'technical': True,
                'concise': True,
                'command_style': True,
                'line_breaks': False,
                'capitalization': 'lowercase'
            },
            'general': {
                'formal': False,
                'paragraphs': True,
                'line_breaks': True,
                'capitalization': 'sentence'
            }
        }
        
        # User-defined context rules (can be customized)
        self.user_rules = {}
        
        # Learning data for improving detection
        self.learning_data = {
            'corrections': [],
            'frequency': {}
        }
    
    def detect_active_window(self) -> Optional[WindowInfo]:
        """
        Detect the currently active window using pygetwindow.

        Returns:
            WindowInfo object with window details, or None if detection fails
        """
        # ``pygetwindow`` may not be available (e.g. on headless CI systems).
        # In that case we simply return ``None`` which callers already handle by
        # falling back to a generic context.  This mirrors the behaviour when
        # the library is present but no active window can be determined.
        if gw is None:  # pragma: no cover - depends on platform
            logger.warning("pygetwindow is not available; cannot detect window")
            return None

        try:
            active_window = gw.getActiveWindow()
            if not active_window:
                logger.warning("No active window detected")
                return None

            # Get window properties
            window_info = WindowInfo(
                title=active_window.title,
                class_name=getattr(active_window, '_hWnd', 'unknown'),
                is_active=active_window.isActive,
                is_minimized=active_window.isMinimized,
                is_maximized=active_window.isMaximized
            )

            logger.debug(f"Detected active window: {window_info.title}")
            return window_info

        except Exception as e:  # pragma: no cover - defensive programming
            logger.error(f"Error detecting active window: {e}")
            return None
    
    def detect_context(self, window_info: Optional[WindowInfo] = None) -> str:
        """
        Determine the application context based on window information.
        
        Args:
            window_info: WindowInfo object, or None to detect automatically
            
        Returns:
            Context type string (email, document, code, etc.)
        """
        if not window_info:
            window_info = self.detect_active_window()
        
        if not window_info:
            return 'unknown'
        
        window_title = window_info.title.lower()
        
        # Check user-defined rules first
        for pattern, context in self.user_rules.items():
            if pattern.lower() in window_title:
                logger.debug(f"User rule matched: {pattern} -> {context}")
                return context
        
        # Check predefined patterns
        for context_type, patterns in self.app_patterns.items():
            if any(pattern in window_title for pattern in patterns):
                logger.debug(f"Pattern matched: {context_type} for window '{window_info.title}'")
                return context_type
        
        # Check for specific application indicators
        if any(indicator in window_title for indicator in ['- microsoft word', '- word']):
            return 'document'
        elif any(indicator in window_title for indicator in ['- microsoft outlook', '- outlook']):
            return 'email'
        elif any(indicator in window_title for indicator in ['- chrome', '- firefox', '- edge']):
            return 'browser'
        elif any(indicator in window_title for indicator in ['visual studio code', 'code.exe']):
            return 'code'
        
        logger.debug(f"No specific context detected for window: {window_info.title}")
        return 'general'
    
    def get_formatting_template(self, context_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Get the formatting template for a specific context.
        
        Args:
            context_type: Context type string, or None to detect automatically
            
        Returns:
            Dictionary containing formatting rules for the context
        """
        if not context_type:
            context_type = self.detect_context()
        
        template = self.formatting_templates.get(context_type, {})
        if not template:
            template = self.formatting_templates.get('general', {})
        
        logger.debug(f"Using formatting template for context: {context_type}")
        return template.copy()
    
    def get_ai_prompt_for_context(self, context_type: Optional[str] = None) -> str:
        """
        Get an AI prompt tailored for the specific context.
        
        Args:
            context_type: Context type string, or None to detect automatically
            
        Returns:
            Context-specific AI prompt string
        """
        if not context_type:
            context_type = self.detect_context()
        
        prompts = {
            'email': "Format this as a professional email. Use proper email etiquette, clear subject lines, and appropriate greetings/closings.",
            'document': "Format this as a well-structured document paragraph. Use proper grammar, clear sentences, and logical flow.",
            'code': "Format this as a clear code comment or documentation. Use technical language appropriately and be concise.",
            'chat': "Format this as a conversational message. Keep it natural, clear, and appropriate for the platform.",
            'presentation': "Format this as presentation content. Use bullet points where appropriate and keep it concise.",
            'spreadsheet': "Format this as spreadsheet content. Use clear, concise language suitable for data entry.",
            'design': "Format this as design-related content. Use creative but clear language appropriate for design work.",
            'terminal': "Format this as terminal/command line content. Use technical language and command syntax where appropriate.",
            'browser': "Format this as web content. Use clear, readable language suitable for web forms or content.",
            'general': "Format this text appropriately for the current context. Ensure clarity and proper grammar."
        }
        
        prompt = prompts.get(context_type, prompts['general'])
        logger.debug(f"Using AI prompt for context: {context_type}")
        return prompt
    
    def add_user_rule(self, pattern: str, context: str) -> None:
        """
        Add a user-defined rule for context detection.
        
        Args:
            pattern: Window title pattern to match
            context: Context type to assign when pattern matches
        """
        self.user_rules[pattern] = context
        logger.info(f"Added user rule: {pattern} -> {context}")
    
    def remove_user_rule(self, pattern: str) -> bool:
        """
        Remove a user-defined rule.
        
        Args:
            pattern: Pattern to remove
            
        Returns:
            True if rule was removed, False if not found
        """
        if pattern in self.user_rules:
            del self.user_rules[pattern]
            logger.info(f"Removed user rule: {pattern}")
            return True
        return False
    
    def get_context_info(self) -> Dict[str, Any]:
        """
        Get comprehensive information about the current context.
        
        Returns:
            Dictionary with context information
        """
        window_info = self.detect_active_window()
        context_type = self.detect_context(window_info)
        formatting_template = self.get_formatting_template(context_type)
        ai_prompt = self.get_ai_prompt_for_context(context_type)
        
        return {
            'context_type': context_type,
            'window_info': window_info,
            'formatting_template': formatting_template,
            'ai_prompt': ai_prompt,
            'user_rules_count': len(self.user_rules)
        } 
"""
Application Context Awareness Module

This module provides functionality to detect the active application and adapt
text formatting and behavior based on the application context.
"""

from .application_context import ApplicationContext
from .text_formatter import ContextTextFormatter
from .ai_enhancement_adapter import AIEnhancementAdapter
from .user_rules_manager import UserRulesManager

__all__ = ['ApplicationContext', 'ContextTextFormatter', 'AIEnhancementAdapter', 'UserRulesManager'] 
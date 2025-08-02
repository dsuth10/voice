"""
Text Insertion Module

This module provides comprehensive text insertion functionality for Windows applications.
It includes cursor detection, text insertion, formatting, error recovery, and special handling.
"""

from .cursor_detection import CursorDetector
from .text_insertion import TextInserter
from .formatting import TextFormatter
from .error_recovery import ErrorRecoveryManager
from .special_handling import SpecialHandlingManager
from .text_insertion_system import TextInsertionSystem

__all__ = [
    'CursorDetector',
    'TextInserter', 
    'TextFormatter',
    'ErrorRecoveryManager',
    'SpecialHandlingManager',
    'TextInsertionSystem'
]

# Version information
__version__ = '1.0.0'
__author__ = 'Voice Dictation Assistant Team'
__description__ = 'Comprehensive text insertion system for Windows applications' 
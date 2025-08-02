"""
Core Application Architecture Module

This module contains the main application controller and supporting components
for the Voice Dictation Assistant.
"""

from .application_controller import ApplicationController
from .workflow_manager import WorkflowManager
from .feedback_system import UserFeedbackSystem
from .error_handler import ErrorHandler
from .performance_monitor import PerformanceMonitor

__all__ = [
    'ApplicationController',
    'WorkflowManager', 
    'UserFeedbackSystem',
    'ErrorHandler',
    'PerformanceMonitor'
] 
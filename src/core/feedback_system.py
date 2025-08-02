"""
User Feedback System for Voice Dictation Assistant

This module provides comprehensive user feedback including visual indicators,
audio cues, and system tray notifications for all application states.
"""

import threading
import time
import logging
from typing import Optional, Callable, Dict, Any, List
from dataclasses import dataclass
from enum import Enum
import winsound
import ctypes
from ctypes import wintypes

from .application_controller import ApplicationState
from .workflow_manager import WorkflowStep


class FeedbackType(Enum):
    """Feedback type enumeration."""
    VISUAL = "visual"
    AUDIO = "audio"
    BOTH = "both"


class FeedbackLevel(Enum):
    """Feedback level enumeration."""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class AudioFeedback:
    """Audio feedback configuration."""
    frequency: int
    duration: int
    volume: int = 50


class VisualFeedback:
    """Visual feedback indicators."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.is_active = False
        self.flash_thread = None
        self.stop_flash = threading.Event()
    
    def show_recording_indicator(self):
        """Show recording indicator (e.g., flashing red)."""
        self.logger.info("Showing recording indicator")
        self._start_flash_effect("recording")
    
    def show_processing_indicator(self):
        """Show processing indicator (e.g., spinning or pulsing)."""
        self.logger.info("Showing processing indicator")
        self._start_flash_effect("processing")
    
    def show_error_indicator(self):
        """Show error indicator (e.g., solid red)."""
        self.logger.info("Showing error indicator")
        self._start_flash_effect("error")
    
    def show_success_indicator(self):
        """Show success indicator (e.g., green flash)."""
        self.logger.info("Showing success indicator")
        self._start_flash_effect("success")
    
    def hide_all_indicators(self):
        """Hide all visual indicators."""
        self.logger.info("Hiding all indicators")
        self._stop_flash_effect()
    
    def _start_flash_effect(self, effect_type: str):
        """Start a flashing effect for visual feedback."""
        self._stop_flash_effect()
        
        self.is_active = True
        self.stop_flash.clear()
        
        if effect_type == "recording":
            self.flash_thread = threading.Thread(target=self._flash_red, daemon=True)
        elif effect_type == "processing":
            self.flash_thread = threading.Thread(target=self._flash_yellow, daemon=True)
        elif effect_type == "error":
            self.flash_thread = threading.Thread(target=self._flash_error, daemon=True)
        elif effect_type == "success":
            self.flash_thread = threading.Thread(target=self._flash_success, daemon=True)
        
        self.flash_thread.start()
    
    def _stop_flash_effect(self):
        """Stop the current flashing effect."""
        if self.flash_thread and self.flash_thread.is_alive():
            self.stop_flash.set()
            self.flash_thread.join(timeout=1.0)
        
        self.is_active = False
    
    def _flash_red(self):
        """Flash red for recording state."""
        while not self.stop_flash.is_set():
            # Flash red (this would integrate with system tray or UI)
            time.sleep(0.5)
    
    def _flash_yellow(self):
        """Flash yellow for processing state."""
        while not self.stop_flash.is_set():
            # Flash yellow (this would integrate with system tray or UI)
            time.sleep(0.3)
    
    def _flash_error(self):
        """Flash error indicator."""
        for _ in range(3):  # Flash 3 times
            if self.stop_flash.is_set():
                break
            # Flash error color
            time.sleep(0.2)
    
    def _flash_success(self):
        """Flash success indicator."""
        for _ in range(2):  # Flash 2 times
            if self.stop_flash.is_set():
                break
            # Flash success color
            time.sleep(0.1)


class AudioFeedbackSystem:
    """Audio feedback system using Windows API."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.audio_enabled = True
        
        # Audio feedback configurations
        self.audio_feedback = {
            'recording_start': AudioFeedback(800, 100),  # Medium tone
            'recording_stop': AudioFeedback(600, 100),   # Lower tone
            'processing': AudioFeedback(1000, 50),        # High tone
            'success': AudioFeedback(1200, 200),          # High success tone
            'error': AudioFeedback(400, 300),             # Low error tone
            'warning': AudioFeedback(600, 150),           # Warning tone
        }
    
    def play_recording_start(self):
        """Play audio for recording start."""
        self._play_audio('recording_start')
    
    def play_recording_stop(self):
        """Play audio for recording stop."""
        self._play_audio('recording_stop')
    
    def play_processing(self):
        """Play audio for processing state."""
        self._play_audio('processing')
    
    def play_success(self):
        """Play audio for success."""
        self._play_audio('success')
    
    def play_error(self):
        """Play audio for error."""
        self._play_audio('error')
    
    def play_warning(self):
        """Play audio for warning."""
        self._play_audio('warning')
    
    def _play_audio(self, feedback_type: str):
        """Play audio feedback using Windows API."""
        if not self.audio_enabled:
            return
        
        try:
            feedback = self.audio_feedback.get(feedback_type)
            if feedback:
                winsound.Beep(feedback.frequency, feedback.duration)
                self.logger.debug(f"Played audio feedback: {feedback_type}")
        except Exception as e:
            self.logger.error(f"Failed to play audio feedback: {e}")
    
    def set_audio_enabled(self, enabled: bool):
        """Enable or disable audio feedback."""
        self.audio_enabled = enabled
        self.logger.info(f"Audio feedback {'enabled' if enabled else 'disabled'}")


class SystemTrayFeedback:
    """System tray feedback integration."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.tray_icon = None
        self.icon_states = {
            'idle': 'icon_idle.ico',
            'recording': 'icon_recording.ico',
            'processing': 'icon_processing.ico',
            'error': 'icon_error.ico'
        }
    
    def update_tray_icon(self, state: str):
        """Update system tray icon based on application state."""
        self.logger.info(f"Updating tray icon to: {state}")
        # This would integrate with pystray or similar library
        # For now, we'll just log the state change
    
    def show_notification(self, title: str, message: str, duration: int = 3000):
        """Show a system tray notification."""
        self.logger.info(f"Tray notification: {title} - {message}")
        # This would integrate with system tray notification API
        # For now, we'll just log the notification


class UserFeedbackSystem:
    """
    Comprehensive user feedback system.
    
    This class provides visual, audio, and system tray feedback for all
    application states and workflow steps.
    """
    
    def __init__(self, feedback_type: FeedbackType = FeedbackType.BOTH):
        """
        Initialize the feedback system.
        
        Args:
            feedback_type: Type of feedback to provide
        """
        self.logger = logging.getLogger(__name__)
        
        # Feedback components
        self.visual_feedback = VisualFeedback()
        self.audio_feedback = AudioFeedbackSystem()
        self.tray_feedback = SystemTrayFeedback()
        
        # Configuration
        self.feedback_type = feedback_type
        self.feedback_level = FeedbackLevel.MEDIUM
        
        # State tracking
        self.current_state = None
        self.current_workflow_step = None
        
        # Callbacks
        self.state_callbacks: List[Callable[[str], None]] = []
        self.workflow_callbacks: List[Callable[[str], None]] = []
        
        self.logger.info("UserFeedbackSystem initialized")
    
    def on_application_state_change(self, new_state: ApplicationState):
        """Handle application state changes."""
        if self.current_state != new_state:
            old_state = self.current_state
            self.current_state = new_state
            
            self.logger.info(f"Application state changed: {old_state} -> {new_state}")
            
            # Provide appropriate feedback
            if new_state == ApplicationState.RECORDING:
                self._feedback_recording_start()
            elif new_state == ApplicationState.PROCESSING:
                self._feedback_processing_start()
            elif new_state == ApplicationState.IDLE:
                self._feedback_idle()
            elif new_state == ApplicationState.ERROR:
                self._feedback_error()
            
            # Update system tray
            self.tray_feedback.update_tray_icon(new_state.value)
            
            # Notify callbacks
            for callback in self.state_callbacks:
                try:
                    callback(new_state.value)
                except Exception as e:
                    self.logger.error(f"State callback error: {e}")
    
    def on_workflow_step_change(self, new_step: WorkflowStep):
        """Handle workflow step changes."""
        if self.current_workflow_step != new_step:
            old_step = self.current_workflow_step
            self.current_workflow_step = new_step
            
            self.logger.info(f"Workflow step changed: {old_step} -> {new_step}")
            
            # Provide step-specific feedback
            if new_step == WorkflowStep.RECORDING:
                self._feedback_recording_start()
            elif new_step == WorkflowStep.TRANSCRIBING:
                self._feedback_transcribing_start()
            elif new_step == WorkflowStep.ENHANCING:
                self._feedback_enhancing_start()
            elif new_step == WorkflowStep.INSERTING:
                self._feedback_inserting_start()
            elif new_step == WorkflowStep.COMPLETED:
                self._feedback_workflow_completed()
            elif new_step == WorkflowStep.ERROR:
                self._feedback_workflow_error()
            
            # Notify callbacks
            for callback in self.workflow_callbacks:
                try:
                    callback(new_step.value)
                except Exception as e:
                    self.logger.error(f"Workflow callback error: {e}")
    
    def on_error(self, error_message: str):
        """Handle error notifications."""
        self.logger.error(f"Error feedback: {error_message}")
        
        # Audio feedback
        if self.feedback_type in [FeedbackType.AUDIO, FeedbackType.BOTH]:
            self.audio_feedback.play_error()
        
        # Visual feedback
        if self.feedback_type in [FeedbackType.VISUAL, FeedbackType.BOTH]:
            self.visual_feedback.show_error_indicator()
        
        # System tray notification
        self.tray_feedback.show_notification(
            "Voice Dictation Assistant - Error",
            error_message,
            duration=5000
        )
    
    def _feedback_recording_start(self):
        """Provide feedback for recording start."""
        self.logger.info("Providing recording start feedback")
        
        if self.feedback_type in [FeedbackType.AUDIO, FeedbackType.BOTH]:
            self.audio_feedback.play_recording_start()
        
        if self.feedback_type in [FeedbackType.VISUAL, FeedbackType.BOTH]:
            self.visual_feedback.show_recording_indicator()
    
    def _feedback_processing_start(self):
        """Provide feedback for processing start."""
        self.logger.info("Providing processing start feedback")
        
        if self.feedback_type in [FeedbackType.AUDIO, FeedbackType.BOTH]:
            self.audio_feedback.play_processing()
        
        if self.feedback_type in [FeedbackType.VISUAL, FeedbackType.BOTH]:
            self.visual_feedback.show_processing_indicator()
    
    def _feedback_transcribing_start(self):
        """Provide feedback for transcription start."""
        self.logger.info("Providing transcription start feedback")
        # Could add specific feedback for transcription step
    
    def _feedback_enhancing_start(self):
        """Provide feedback for text enhancement start."""
        self.logger.info("Providing enhancement start feedback")
        # Could add specific feedback for enhancement step
    
    def _feedback_inserting_start(self):
        """Provide feedback for text insertion start."""
        self.logger.info("Providing insertion start feedback")
        # Could add specific feedback for insertion step
    
    def _feedback_workflow_completed(self):
        """Provide feedback for workflow completion."""
        self.logger.info("Providing workflow completion feedback")
        
        if self.feedback_type in [FeedbackType.AUDIO, FeedbackType.BOTH]:
            self.audio_feedback.play_success()
        
        if self.feedback_type in [FeedbackType.VISUAL, FeedbackType.BOTH]:
            self.visual_feedback.show_success_indicator()
        
        # Hide indicators after a short delay
        threading.Timer(2.0, self.visual_feedback.hide_all_indicators).start()
    
    def _feedback_workflow_error(self):
        """Provide feedback for workflow error."""
        self.logger.info("Providing workflow error feedback")
        
        if self.feedback_type in [FeedbackType.AUDIO, FeedbackType.BOTH]:
            self.audio_feedback.play_error()
        
        if self.feedback_type in [FeedbackType.VISUAL, FeedbackType.BOTH]:
            self.visual_feedback.show_error_indicator()
    
    def _feedback_idle(self):
        """Provide feedback for idle state."""
        self.logger.info("Providing idle feedback")
        
        if self.feedback_type in [FeedbackType.AUDIO, FeedbackType.BOTH]:
            self.audio_feedback.play_recording_stop()
        
        if self.feedback_type in [FeedbackType.VISUAL, FeedbackType.BOTH]:
            self.visual_feedback.hide_all_indicators()
    
    def _feedback_error(self):
        """Provide feedback for error state."""
        self.logger.info("Providing error feedback")
        
        if self.feedback_type in [FeedbackType.AUDIO, FeedbackType.BOTH]:
            self.audio_feedback.play_error()
        
        if self.feedback_type in [FeedbackType.VISUAL, FeedbackType.BOTH]:
            self.visual_feedback.show_error_indicator()
    
    def set_feedback_type(self, feedback_type: FeedbackType):
        """Set the type of feedback to provide."""
        self.feedback_type = feedback_type
        self.logger.info(f"Feedback type set to: {feedback_type}")
    
    def set_feedback_level(self, level: FeedbackLevel):
        """Set the feedback level."""
        self.feedback_level = level
        self.logger.info(f"Feedback level set to: {level}")
    
    def add_state_callback(self, callback: Callable[[str], None]):
        """Add callback for state changes."""
        self.state_callbacks.append(callback)
    
    def add_workflow_callback(self, callback: Callable[[str], None]):
        """Add callback for workflow step changes."""
        self.workflow_callbacks.append(callback)
    
    def shutdown(self):
        """Shutdown the feedback system."""
        self.logger.info("Shutting down feedback system")
        
        try:
            # Stop visual feedback
            self.visual_feedback.hide_all_indicators()
            
            # Disable audio feedback
            self.audio_feedback.set_audio_enabled(False)
            
            self.logger.info("Feedback system shutdown completed")
            
        except Exception as e:
            self.logger.error(f"Error during feedback system shutdown: {e}") 
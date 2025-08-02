"""
Visual and Audio Feedback System for Hotkeys

This module provides visual and audio feedback for hotkey activation,
recording states, and error conditions in the Voice Dictation Assistant.
"""

import logging
import threading
import time
import winsound
from typing import Optional, Callable
from enum import Enum
from dataclasses import dataclass


class FeedbackType(Enum):
    """Enumeration for feedback types."""
    VISUAL = "visual"
    AUDIO = "audio"
    BOTH = "both"


class FeedbackLevel(Enum):
    """Enumeration for feedback levels."""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class FeedbackConfig:
    """Configuration for feedback behavior."""
    visual_feedback: bool = True
    audio_feedback: bool = True
    feedback_level: FeedbackLevel = FeedbackLevel.MEDIUM
    system_tray_callback: Optional[Callable] = None
    audio_device_callback: Optional[Callable] = None


class HotkeyFeedbackSystem:
    """
    Provides visual and audio feedback for hotkey events and recording states.
    
    Supports system tray icon changes, audio cues, and other feedback mechanisms
    to inform users about the current state of the voice dictation system.
    """
    
    def __init__(self, config: FeedbackConfig = None):
        """
        Initialize the feedback system.
        
        Args:
            config: Configuration for feedback behavior
        """
        self.config = config or FeedbackConfig()
        self.logger = logging.getLogger(__name__)
        
        # Audio feedback settings
        self.audio_frequencies = {
            'recording_start': 800,  # Hz
            'recording_stop': 600,   # Hz
            'error': 400,            # Hz
            'warning': 1000,         # Hz
            'success': 1200          # Hz
        }
        
        self.audio_durations = {
            'recording_start': 200,  # ms
            'recording_stop': 150,   # ms
            'error': 500,            # ms
            'warning': 300,          # ms
            'success': 250           # ms
        }
        
        # Visual feedback states
        self.current_visual_state = "idle"
        self.visual_states = {
            'idle': {'icon': 'default', 'color': 'gray'},
            'recording': {'icon': 'recording', 'color': 'red'},
            'processing': {'icon': 'processing', 'color': 'yellow'},
            'error': {'icon': 'error', 'color': 'red'},
            'warning': {'icon': 'warning', 'color': 'orange'},
            'success': {'icon': 'success', 'color': 'green'}
        }
    
    def provide_feedback(self, event_type: str, feedback_type: FeedbackType = FeedbackType.BOTH):
        """
        Provide feedback for a specific event.
        
        Args:
            event_type: Type of event (recording_start, recording_stop, error, etc.)
            feedback_type: Type of feedback to provide
        """
        try:
            if feedback_type in [FeedbackType.VISUAL, FeedbackType.BOTH]:
                self._provide_visual_feedback(event_type)
            
            if feedback_type in [FeedbackType.AUDIO, FeedbackType.BOTH]:
                self._provide_audio_feedback(event_type)
            
            self.logger.debug(f"Provided {feedback_type.value} feedback for event: {event_type}")
            
        except Exception as e:
            self.logger.error(f"Failed to provide feedback for {event_type}: {e}")
    
    def _provide_visual_feedback(self, event_type: str):
        """
        Provide visual feedback for an event.
        
        Args:
            event_type: Type of event
        """
        if not self.config.visual_feedback:
            return
        
        # Map event types to visual states
        state_mapping = {
            'recording_start': 'recording',
            'recording_stop': 'processing',
            'processing_complete': 'success',
            'error': 'error',
            'warning': 'warning',
            'hotkey_activated': 'recording',
            'hotkey_deactivated': 'idle'
        }
        
        new_state = state_mapping.get(event_type, 'idle')
        self._update_visual_state(new_state)
    
    def _provide_audio_feedback(self, event_type: str):
        """
        Provide audio feedback for an event.
        
        Args:
            event_type: Type of event
        """
        if not self.config.audio_feedback:
            return
        
        # Check if audio frequency is defined for this event
        if event_type not in self.audio_frequencies:
            self.logger.warning(f"No audio frequency defined for event: {event_type}")
            return
        
        # Get audio parameters
        frequency = self.audio_frequencies[event_type]
        duration = self.audio_durations[event_type]
        
        # Play audio feedback in a separate thread to avoid blocking
        audio_thread = threading.Thread(
            target=self._play_audio,
            args=(frequency, duration),
            daemon=True
        )
        audio_thread.start()
    
    def _play_audio(self, frequency: int, duration: int):
        """
        Play audio feedback using Windows API.
        
        Args:
            frequency: Frequency in Hz
            duration: Duration in milliseconds
        """
        try:
            # Use Windows API to play a beep
            winsound.Beep(frequency, duration)
        except Exception as e:
            self.logger.error(f"Failed to play audio feedback: {e}")
            
            # Fallback: try to use the audio device callback if available
            if self.config.audio_device_callback:
                try:
                    self.config.audio_device_callback(frequency, duration)
                except Exception as callback_error:
                    self.logger.error(f"Audio callback also failed: {callback_error}")
    
    def _update_visual_state(self, new_state: str):
        """
        Update the visual state and notify the system tray.
        
        Args:
            new_state: New visual state
        """
        if new_state == self.current_visual_state:
            return
        
        self.current_visual_state = new_state
        
        # Get state configuration
        state_config = self.visual_states.get(new_state, self.visual_states['idle'])
        
        # Notify system tray if callback is available
        if self.config.system_tray_callback:
            try:
                self.config.system_tray_callback(new_state, state_config)
            except Exception as e:
                self.logger.error(f"Failed to update system tray: {e}")
        
        self.logger.debug(f"Updated visual state to: {new_state}")
    
    def set_system_tray_callback(self, callback: Callable):
        """
        Set the callback for system tray updates.
        
        Args:
            callback: Function to call for system tray updates
        """
        self.config.system_tray_callback = callback
    
    def set_audio_device_callback(self, callback: Callable):
        """
        Set the callback for custom audio device output.
        
        Args:
            callback: Function to call for audio output
        """
        self.config.audio_device_callback = callback
    
    def update_feedback_config(self, config: FeedbackConfig):
        """
        Update the feedback configuration.
        
        Args:
            config: New feedback configuration
        """
        self.config = config
        self.logger.info("Updated feedback configuration")
    
    def get_current_visual_state(self) -> str:
        """
        Get the current visual state.
        
        Returns:
            str: Current visual state
        """
        return self.current_visual_state
    
    def get_visual_state_config(self, state: str) -> dict:
        """
        Get configuration for a visual state.
        
        Args:
            state: Visual state name
            
        Returns:
            dict: State configuration
        """
        return self.visual_states.get(state, self.visual_states['idle'])
    
    def add_custom_audio_event(self, event_type: str, frequency: int, duration: int):
        """
        Add a custom audio event with specific frequency and duration.
        
        Args:
            event_type: Name of the event
            frequency: Frequency in Hz
            duration: Duration in milliseconds
        """
        self.audio_frequencies[event_type] = frequency
        self.audio_durations[event_type] = duration
        self.logger.info(f"Added custom audio event: {event_type} ({frequency}Hz, {duration}ms)")
    
    def add_custom_visual_state(self, state_name: str, icon: str, color: str):
        """
        Add a custom visual state.
        
        Args:
            state_name: Name of the state
            icon: Icon identifier
            color: Color identifier
        """
        self.visual_states[state_name] = {'icon': icon, 'color': color}
        self.logger.info(f"Added custom visual state: {state_name}")
    
    def test_audio_feedback(self, event_type: str = 'success'):
        """
        Test audio feedback for a specific event type.
        
        Args:
            event_type: Event type to test
        """
        self.logger.info(f"Testing audio feedback for: {event_type}")
        self._provide_audio_feedback(event_type)
    
    def test_visual_feedback(self, state: str = 'recording'):
        """
        Test visual feedback for a specific state.
        
        Args:
            state: State to test
        """
        self.logger.info(f"Testing visual feedback for state: {state}")
        self._update_visual_state(state)
    
    def cleanup(self):
        """Clean up the feedback system."""
        # Reset to idle state
        self._update_visual_state('idle')
        self.logger.info("Feedback system cleanup completed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup() 
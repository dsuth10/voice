"""
Push-to-Talk Hotkey Event Handling

This module provides specialized handling for push-to-talk functionality,
managing keydown and keyup events for voice recording activation.
"""

import logging
import threading
import time
from typing import Callable, Optional, Dict
from enum import Enum
from dataclasses import dataclass


class RecordingState(Enum):
    """Enumeration for recording states."""
    IDLE = "idle"
    RECORDING = "recording"
    PROCESSING = "processing"


@dataclass
class PushToTalkConfig:
    """Configuration for push-to-talk functionality."""
    start_callback: Optional[Callable] = None
    stop_callback: Optional[Callable] = None
    min_hold_time: float = 0.1  # Minimum time to hold key for activation
    max_hold_time: float = 30.0  # Maximum time to hold key before auto-stop
    visual_feedback: bool = True
    audio_feedback: bool = True


class PushToTalkHandler:
    """
    Handles push-to-talk functionality for voice recording.
    
    Manages keydown/keyup events to start and stop recording based on
    key press duration and provides visual/audio feedback.
    """
    
    def __init__(self, config: PushToTalkConfig = None):
        """
        Initialize the PushToTalkHandler.
        
        Args:
            config: Configuration for push-to-talk behavior
        """
        self.config = config or PushToTalkConfig()
        self.state = RecordingState.IDLE
        self.key_press_time: Optional[float] = None
        self.recording_thread: Optional[threading.Thread] = None
        self.stop_recording_event = threading.Event()
        
        # Initialize logger
        self.logger = logging.getLogger(__name__)
        
        # State change callbacks
        self.state_change_callbacks: Dict[RecordingState, Callable] = {}
    
    def on_key_down(self):
        """
        Handle key down event for push-to-talk activation.
        """
        if self.state != RecordingState.IDLE:
            self.logger.debug("Key down ignored - already recording or processing")
            return
        
        self.key_press_time = time.time()
        self.logger.debug("Key down detected - starting recording timer")
        
        # Start recording after minimum hold time
        self.recording_thread = threading.Thread(
            target=self._delayed_start_recording,
            daemon=True
        )
        self.recording_thread.start()
    
    def on_key_up(self):
        """
        Handle key up event for push-to-talk deactivation.
        """
        if self.state == RecordingState.IDLE:
            self.logger.debug("Key up ignored - not recording")
            return
        
        if self.key_press_time is None:
            self.logger.warning("Key up detected but no key press time recorded")
            return
        
        hold_duration = time.time() - self.key_press_time
        
        if hold_duration < self.config.min_hold_time:
            self.logger.debug(f"Key released too quickly ({hold_duration:.2f}s) - ignoring")
            self._reset_state()
            return
        
        self.logger.info(f"Key released after {hold_duration:.2f}s - stopping recording")
        self._stop_recording()
    
    def _delayed_start_recording(self):
        """
        Start recording after the minimum hold time has elapsed.
        """
        time.sleep(self.config.min_hold_time)
        
        # Check if key is still pressed
        if self.key_press_time is None:
            return
        
        hold_duration = time.time() - self.key_press_time
        if hold_duration >= self.config.min_hold_time:
            self._start_recording()
    
    def _start_recording(self):
        """
        Start the voice recording process.
        """
        if self.state != RecordingState.IDLE:
            return
        
        self.state = RecordingState.RECORDING
        self.logger.info("Starting voice recording")
        
        # Provide feedback
        if self.config.visual_feedback:
            self._provide_visual_feedback(True)
        
        if self.config.audio_feedback:
            self._provide_audio_feedback(True)
        
        # Call the start callback
        if self.config.start_callback:
            try:
                self.config.start_callback()
            except Exception as e:
                self.logger.error(f"Error in start callback: {e}")
        
        # Notify state change
        self._notify_state_change()
        
        # Start auto-stop timer
        self._start_auto_stop_timer()
    
    def _stop_recording(self):
        """
        Stop the voice recording process.
        """
        if self.state != RecordingState.RECORDING:
            return
        
        self.state = RecordingState.PROCESSING
        self.logger.info("Stopping voice recording")
        
        # Provide feedback
        if self.config.visual_feedback:
            self._provide_visual_feedback(False)
        
        if self.config.audio_feedback:
            self._provide_audio_feedback(False)
        
        # Call the stop callback
        if self.config.stop_callback:
            try:
                self.config.stop_callback()
            except Exception as e:
                self.logger.error(f"Error in stop callback: {e}")
        
        # Notify state change
        self._notify_state_change()
        
        # Reset state after processing
        self._reset_state()
    
    def _start_auto_stop_timer(self):
        """
        Start a timer to automatically stop recording if held too long.
        """
        def auto_stop():
            time.sleep(self.config.max_hold_time)
            if self.state == RecordingState.RECORDING:
                self.logger.warning(f"Auto-stopping recording after {self.config.max_hold_time}s")
                self._stop_recording()
        
        auto_stop_thread = threading.Thread(target=auto_stop, daemon=True)
        auto_stop_thread.start()
    
    def _reset_state(self):
        """
        Reset the handler state to idle.
        """
        self.state = RecordingState.IDLE
        self.key_press_time = None
        self.stop_recording_event.clear()
        
        if self.recording_thread and self.recording_thread.is_alive():
            self.recording_thread.join(timeout=1.0)
        
        self._notify_state_change()
    
    def _provide_visual_feedback(self, is_recording: bool):
        """
        Provide visual feedback for recording state.
        
        Args:
            is_recording: True if recording is active, False otherwise
        """
        # This will be implemented by the system tray integration
        self.logger.debug(f"Visual feedback: {'Recording' if is_recording else 'Idle'}")
    
    def _provide_audio_feedback(self, is_recording: bool):
        """
        Provide audio feedback for recording state.
        
        Args:
            is_recording: True if recording is active, False otherwise
        """
        # This will be implemented by the audio feedback system
        self.logger.debug(f"Audio feedback: {'Recording' if is_recording else 'Idle'}")
    
    def _notify_state_change(self):
        """
        Notify registered callbacks of state changes.
        """
        if self.state in self.state_change_callbacks:
            try:
                self.state_change_callbacks[self.state]()
            except Exception as e:
                self.logger.error(f"Error in state change callback: {e}")
    
    def register_state_callback(self, state: RecordingState, callback: Callable):
        """
        Register a callback for state changes.
        
        Args:
            state: The recording state to monitor
            callback: Function to call when state changes
        """
        self.state_change_callbacks[state] = callback
    
    def get_current_state(self) -> RecordingState:
        """
        Get the current recording state.
        
        Returns:
            RecordingState: Current state of the handler
        """
        return self.state
    
    def is_recording(self) -> bool:
        """
        Check if currently recording.
        
        Returns:
            bool: True if recording, False otherwise
        """
        return self.state == RecordingState.RECORDING
    
    def force_stop(self):
        """
        Force stop recording regardless of current state.
        """
        if self.state != RecordingState.IDLE:
            self.logger.warning("Force stopping recording")
            self._stop_recording()
    
    def cleanup(self):
        """
        Clean up resources and stop any ongoing operations.
        """
        self.force_stop()
        self.logger.info("PushToTalkHandler cleanup completed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup() 
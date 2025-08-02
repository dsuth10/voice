"""
Enhanced Hotkey Manager with Push-to-Talk Integration

This module provides an enhanced hotkey management system that combines
the base HotkeyManager with push-to-talk functionality for voice recording.
"""

import logging
from typing import Dict, Callable, Optional, List, Tuple
from .hotkey_manager import HotkeyManager, HotkeyMode, HotkeyConfig
from .push_to_talk import PushToTalkHandler, PushToTalkConfig, RecordingState
from .conflict_detector import HotkeyConflictDetector, ConflictInfo, ConflictLevel
from .feedback_system import HotkeyFeedbackSystem, FeedbackConfig, FeedbackType
from .security_compatibility import WindowsSecurityCompatibility, SecurityLevel


class EnhancedHotkeyManager:
    """
    Enhanced hotkey manager that integrates push-to-talk functionality.
    
    Provides both toggle and push-to-talk modes for voice recording,
    with proper event handling and state management.
    """
    
    def __init__(self, config: Dict = None):
        """
        Initialize the EnhancedHotkeyManager.
        
        Args:
            config: Configuration dictionary containing hotkey settings
        """
        self.config = config or {}
        self.base_manager = HotkeyManager(config)
        self.push_to_talk_handlers: Dict[str, PushToTalkHandler] = {}
        self.conflict_detector = HotkeyConflictDetector()
        self.security_compatibility = WindowsSecurityCompatibility()
        
        # Initialize feedback system
        feedback_config = FeedbackConfig(
            visual_feedback=self.config.get('visual_feedback', True),
            audio_feedback=self.config.get('audio_feedback', True)
        )
        self.feedback_system = HotkeyFeedbackSystem(feedback_config)
        
        # Initialize logger
        self.logger = logging.getLogger(__name__)
        
        # Set up push-to-talk handlers for default hotkeys
        self._setup_push_to_talk_handlers()
    
    def _setup_push_to_talk_handlers(self):
        """Set up push-to-talk handlers for hotkeys that support it."""
        push_to_talk_hotkeys = [
            self.config.get('default_hotkey', 'ctrl+win+space')
        ]
        
        for hotkey in push_to_talk_hotkeys:
            if self.base_manager.is_hotkey_registered(hotkey):
                self._create_push_to_talk_handler(hotkey)
    
    def _create_push_to_talk_handler(self, hotkey: str):
        """
        Create a push-to-talk handler for a specific hotkey.
        
        Args:
            hotkey: The hotkey combination to create a handler for
        """
        # Create push-to-talk configuration
        pt_config = PushToTalkConfig(
            min_hold_time=self.config.get('min_hold_time', 0.1),
            max_hold_time=self.config.get('max_hold_time', 30.0),
            visual_feedback=self.config.get('visual_feedback', True),
            audio_feedback=self.config.get('audio_feedback', True)
        )
        
        # Create the handler
        pt_handler = PushToTalkHandler(pt_config)
        
        # Register callbacks for key events
        self._register_push_to_talk_callbacks(hotkey, pt_handler)
        
        # Store the handler
        self.push_to_talk_handlers[hotkey] = pt_handler
        
        self.logger.info(f"Created push-to-talk handler for hotkey: {hotkey}")
    
    def _register_push_to_talk_callbacks(self, hotkey: str, pt_handler: PushToTalkHandler):
        """
        Register callbacks for push-to-talk key events.
        
        Args:
            hotkey: The hotkey combination
            pt_handler: The push-to-talk handler
        """
        # Note: The global-hotkeys library doesn't provide separate keydown/keyup events
        # We'll need to implement this using a different approach or modify the base manager
        # For now, we'll use the toggle approach and simulate push-to-talk behavior
        
        def toggle_callback():
            """Toggle callback that simulates push-to-talk behavior."""
            current_state = pt_handler.get_current_state()
            
            if current_state == RecordingState.IDLE:
                # Provide feedback for recording start
                self.feedback_system.provide_feedback('recording_start', FeedbackType.BOTH)
                pt_handler.on_key_down()
            elif current_state == RecordingState.RECORDING:
                # Provide feedback for recording stop
                self.feedback_system.provide_feedback('recording_stop', FeedbackType.BOTH)
                pt_handler.on_key_up()
        
        # Register the callback with the base manager
        self.base_manager.register_callback(hotkey, toggle_callback, "Push-to-Talk Recording")
    
    def register_push_to_talk_hotkey(self, hotkey: str, start_callback: Callable = None, 
                                   stop_callback: Callable = None) -> Tuple[bool, str]:
        """
        Register a new push-to-talk hotkey with conflict detection and security checks.
        
        Args:
            hotkey: The hotkey combination
            start_callback: Callback to call when recording starts
            stop_callback: Callback to call when recording stops
            
        Returns:
            Tuple[bool, str]: (success, message) - success status and feedback message
        """
        try:
            # Check security permissions first
            has_perms, security_info = self.security_compatibility.check_operation_permissions(
                'global_hotkey_registration'
            )
            
            if not has_perms:
                message = f"Security permission denied: {security_info.description}"
                mitigation = self.security_compatibility.get_mitigation_strategies('global_hotkey_registration')
                if mitigation:
                    message += f"\nMitigation: {mitigation[0]}"
                return False, message
            
            # Check for conflicts
            conflict_info = self.conflict_detector.check_conflict(hotkey)
            
            if conflict_info.level in [ConflictLevel.HIGH, ConflictLevel.CRITICAL]:
                message = f"Registration failed: {conflict_info.description}"
                if conflict_info.suggested_alternatives:
                    message += f"\nSuggested alternatives: {', '.join(conflict_info.suggested_alternatives[:3])}"
                return False, message
            
            # Warn about medium-level conflicts but allow registration
            if conflict_info.level == ConflictLevel.MEDIUM:
                self.logger.warning(f"Registering hotkey with medium conflict: {conflict_info.description}")
            
            # Create hotkey config
            hotkey_config = HotkeyConfig(
                key_combination=hotkey,
                description="Push-to-Talk Recording",
                mode=HotkeyMode.PUSH_TO_TALK
            )
            
            # Register with base manager
            if not self.base_manager.register_hotkey(hotkey_config):
                return False, "Failed to register hotkey with system"
            
            # Create push-to-talk handler
            pt_config = PushToTalkConfig(
                start_callback=start_callback,
                stop_callback=stop_callback,
                min_hold_time=self.config.get('min_hold_time', 0.1),
                max_hold_time=self.config.get('max_hold_time', 30.0),
                visual_feedback=self.config.get('visual_feedback', True),
                audio_feedback=self.config.get('audio_feedback', True)
            )
            
            pt_handler = PushToTalkHandler(pt_config)
            self.push_to_talk_handlers[hotkey] = pt_handler
            
            # Register callbacks
            self._register_push_to_talk_callbacks(hotkey, pt_handler)
            
            success_message = f"Successfully registered push-to-talk hotkey: {hotkey}"
            if conflict_info.level == ConflictLevel.LOW:
                success_message += f" (Warning: {conflict_info.description})"
            
            self.logger.info(success_message)
            return True, success_message
            
        except Exception as e:
            error_message = f"Failed to register push-to-talk hotkey {hotkey}: {e}"
            self.logger.error(error_message)
            return False, error_message
    
    def register_toggle_hotkey(self, hotkey: str, callback: Callable, description: str = "") -> Tuple[bool, str]:
        """
        Register a toggle hotkey with conflict detection.
        
        Args:
            hotkey: The hotkey combination
            callback: Callback to call when hotkey is activated
            description: Description of what the hotkey does
            
        Returns:
            Tuple[bool, str]: (success, message) - success status and feedback message
        """
        try:
            # Check for conflicts first
            conflict_info = self.conflict_detector.check_conflict(hotkey)
            
            if conflict_info.level in [ConflictLevel.HIGH, ConflictLevel.CRITICAL]:
                message = f"Registration failed: {conflict_info.description}"
                if conflict_info.suggested_alternatives:
                    message += f"\nSuggested alternatives: {', '.join(conflict_info.suggested_alternatives[:3])}"
                return False, message
            
            # Warn about medium-level conflicts but allow registration
            if conflict_info.level == ConflictLevel.MEDIUM:
                self.logger.warning(f"Registering hotkey with medium conflict: {conflict_info.description}")
            
            # Create hotkey config
            hotkey_config = HotkeyConfig(
                key_combination=hotkey,
                description=description,
                mode=HotkeyMode.TOGGLE,
                callback=callback
            )
            
            # Register with base manager
            success = self.base_manager.register_hotkey(hotkey_config)
            
            if success:
                success_message = f"Successfully registered toggle hotkey: {hotkey}"
                if conflict_info.level == ConflictLevel.LOW:
                    success_message += f" (Warning: {conflict_info.description})"
                
                self.logger.info(success_message)
                return True, success_message
            else:
                return False, "Failed to register hotkey with system"
            
        except Exception as e:
            error_message = f"Failed to register toggle hotkey {hotkey}: {e}"
            self.logger.error(error_message)
            return False, error_message
    
    def get_push_to_talk_handler(self, hotkey: str) -> Optional[PushToTalkHandler]:
        """
        Get the push-to-talk handler for a specific hotkey.
        
        Args:
            hotkey: The hotkey combination
            
        Returns:
            PushToTalkHandler: The handler for the hotkey, or None if not found
        """
        return self.push_to_talk_handlers.get(hotkey)
    
    def is_recording(self, hotkey: str = None) -> bool:
        """
        Check if currently recording.
        
        Args:
            hotkey: Specific hotkey to check, or None to check any hotkey
            
        Returns:
            bool: True if recording, False otherwise
        """
        if hotkey:
            handler = self.get_push_to_talk_handler(hotkey)
            return handler.is_recording() if handler else False
        
        # Check any push-to-talk handler
        for handler in self.push_to_talk_handlers.values():
            if handler.is_recording():
                return True
        
        return False
    
    def force_stop_recording(self, hotkey: str = None):
        """
        Force stop recording for a specific hotkey or all hotkeys.
        
        Args:
            hotkey: Specific hotkey to stop, or None to stop all
        """
        if hotkey:
            handler = self.get_push_to_talk_handler(hotkey)
            if handler:
                handler.force_stop()
        else:
            for handler in self.push_to_talk_handlers.values():
                handler.force_stop()
    
    def start_listening(self):
        """Start listening for hotkey events."""
        self.base_manager.start_listening()
    
    def stop_listening(self):
        """Stop listening for hotkey events."""
        self.base_manager.stop_listening()
    
    def cleanup(self):
        """Clean up all resources."""
        # Clean up push-to-talk handlers
        for handler in self.push_to_talk_handlers.values():
            handler.cleanup()
        
        # Clean up feedback system
        self.feedback_system.cleanup()
        
        # Clean up base manager
        self.base_manager.cleanup()
        
        self.logger.info("EnhancedHotkeyManager cleanup completed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()
    
    # Delegate other methods to base manager
    def register_hotkey(self, *args, **kwargs):
        return self.base_manager.register_hotkey(*args, **kwargs)
    
    def unregister_hotkey(self, *args, **kwargs):
        return self.base_manager.unregister_hotkey(*args, **kwargs)
    
    def get_registered_hotkeys(self, *args, **kwargs):
        return self.base_manager.get_registered_hotkeys(*args, **kwargs)
    
    def is_hotkey_registered(self, *args, **kwargs):
        return self.base_manager.is_hotkey_registered(*args, **kwargs)
    
    def check_hotkey_conflicts(self, hotkeys: List[str]) -> Dict[str, ConflictInfo]:
        """
        Check for conflicts in a list of hotkeys.
        
        Args:
            hotkeys: List of hotkey combinations to check
            
        Returns:
            Dict[str, ConflictInfo]: Dictionary mapping hotkeys to conflict information
        """
        return self.conflict_detector.get_conflict_report(hotkeys)
    
    def get_safe_hotkeys(self, count: int = 5) -> List[str]:
        """
        Get a list of safe hotkey combinations.
        
        Args:
            count: Number of safe hotkeys to return
            
        Returns:
            List[str]: List of safe hotkey combinations
        """
        return self.conflict_detector.get_safe_hotkeys(count)
    
    def validate_hotkey(self, hotkey: str) -> Tuple[bool, str]:
        """
        Validate a hotkey combination.
        
        Args:
            hotkey: The hotkey combination to validate
            
        Returns:
            Tuple[bool, str]: (is_valid, feedback_message)
        """
        return self.conflict_detector.validate_hotkey(hotkey)
    
    def get_feedback_system(self) -> HotkeyFeedbackSystem:
        """
        Get the feedback system instance.
        
        Returns:
            HotkeyFeedbackSystem: The feedback system
        """
        return self.feedback_system
    
    def provide_feedback(self, event_type: str, feedback_type: FeedbackType = FeedbackType.BOTH):
        """
        Provide feedback for a specific event.
        
        Args:
            event_type: Type of event
            feedback_type: Type of feedback to provide
        """
        self.feedback_system.provide_feedback(event_type, feedback_type)
    
    def set_system_tray_callback(self, callback: Callable):
        """
        Set the system tray callback for visual feedback.
        
        Args:
            callback: Function to call for system tray updates
        """
        self.feedback_system.set_system_tray_callback(callback)
    
    def set_audio_device_callback(self, callback: Callable):
        """
        Set the audio device callback for custom audio output.
        
        Args:
            callback: Function to call for audio output
        """
        self.feedback_system.set_audio_device_callback(callback)
    
    def check_security_compatibility(self) -> Tuple[bool, List[str]]:
        """
        Check if the system meets security requirements.
        
        Returns:
            Tuple[bool, List[str]]: (compatible, issues)
        """
        return self.security_compatibility.validate_installation_requirements()
    
    def get_security_recommendations(self) -> List[str]:
        """
        Get security recommendations for the application.
        
        Returns:
            List[str]: List of security recommendations
        """
        return self.security_compatibility.get_security_recommendations()
    
    def check_operation_permissions(self, operation: str) -> Tuple[bool, str]:
        """
        Check if the current process has sufficient permissions for an operation.
        
        Args:
            operation: The operation to check
            
        Returns:
            Tuple[bool, str]: (has_permissions, description)
        """
        has_perms, security_info = self.security_compatibility.check_operation_permissions(operation)
        return has_perms, security_info.description 
"""
Application Controller for Voice Dictation Assistant

This module provides the main application controller that coordinates all system components
and implements the core dictation workflow from hotkey press to text insertion.
"""

import threading
import time
import logging
from typing import Optional, Dict, Any, Callable, List
from dataclasses import dataclass
from enum import Enum

# Import all required components
from config.config_manager import ConfigManager
from audio.capture import AudioCapture
from recognition.speech_recognition import SpeechRecognition
from ai_processing.text_enhancement import AITextProcessor
from text_insertion.text_insertion_system import TextInsertionSystem
from hotkeys.hotkey_manager import HotkeyManager
from context.application_context import ApplicationContext
from context.text_formatter import ContextTextFormatter
from context.ai_enhancement_adapter import AIEnhancementAdapter
from .types import ApplicationState, WorkflowStep, WorkflowMetrics
from .workflow_manager import WorkflowManager
from .feedback_system import UserFeedbackSystem, FeedbackType, FeedbackLevel
from .error_handler import ErrorHandler, ErrorNotifier
from .performance_monitor import PerformanceMonitor, PerformanceReporter
from .analytics_dashboard import AnalyticsDashboard
from .system_tray_app import create_system_tray_app


class ApplicationController:
    """
    Main application controller that coordinates all system components.
    
    This class manages the complete dictation workflow from hotkey press to text insertion,
    including audio capture, speech recognition, AI text enhancement, and text insertion.
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize the application controller.
        
        Args:
            config_file: Optional path to configuration file
        """
        self.logger = logging.getLogger(__name__)
        
        # Initialize configuration
        self.config_manager = ConfigManager(config_file)
        
        # Initialize components (lazy loading for API-dependent components)
        self.hotkey_manager = None
        self.audio_capture = None
        self.speech_recognition = None
        self.text_processor = None
        self.text_insertion = None
        self.app_context = None
        self.context_formatter = None
        self.ai_adapter = None
        self.system_tray = None
        
        # Initialize workflow manager
        self.workflow_manager = WorkflowManager()
        
        # Initialize feedback system
        feedback_type = self.config_manager.get('ui.feedback_type', 'both')
        self.feedback_system = UserFeedbackSystem(
            FeedbackType(feedback_type) if feedback_type in ['visual', 'audio', 'both'] else FeedbackType.BOTH
        )
        
        # Initialize error handling system
        self.error_handler = ErrorHandler()
        self.error_notifier = ErrorNotifier(self.feedback_system)
        
        # Initialize performance monitoring with config manager
        monitoring_interval = self.config_manager.get('performance.monitoring_interval', 1.0)
        self.performance_monitor = PerformanceMonitor(self.config_manager, monitoring_interval)
        self.performance_reporter = PerformanceReporter(self.performance_monitor)
        
        # Initialize analytics dashboard
        self.analytics_dashboard = AnalyticsDashboard(self.performance_monitor, self.config_manager)
        
        # State management
        self.state = ApplicationState.IDLE
        self.is_initialized = False
        self.last_error = None
        
        # Workflow tracking
        self.metrics = WorkflowMetrics()
        self.workflow_lock = threading.Lock()
        
        # Callbacks for external feedback
        self.state_change_callbacks: List[Callable[[ApplicationState], None]] = []
        self.error_callbacks: List[Callable[[str], None]] = []
        self.metrics_callbacks: List[Callable[[WorkflowMetrics], None]] = []
        
        # Setup workflow manager callbacks
        self._setup_workflow_callbacks()
        
        # Setup feedback system callbacks
        self._setup_feedback_callbacks()
        
        # Setup error handling callbacks
        self._setup_error_callbacks()
        
        # Setup performance monitoring callbacks
        self._setup_performance_callbacks()
        
        self.logger.info("ApplicationController initialized")
    
    def _setup_workflow_callbacks(self):
        """Setup callbacks for workflow manager events."""
        self.workflow_manager.add_completion_callback(self._on_workflow_completion)
        self.workflow_manager.add_error_callback(self._on_workflow_error)
        # Fix: Pass both step and callback parameters
        self.workflow_manager.add_step_callback(WorkflowStep.RECORDING, self._on_recording_start)
        self.workflow_manager.add_step_callback(WorkflowStep.TRANSCRIBING, self._on_transcribing_start)
        self.workflow_manager.add_step_callback(WorkflowStep.ENHANCING, self._on_enhancing_start)
        self.workflow_manager.add_step_callback(WorkflowStep.FORMATTING, self._on_formatting_start)
        self.workflow_manager.add_step_callback(WorkflowStep.INSERTING, self._on_inserting_start)
        self.workflow_manager.add_step_callback(WorkflowStep.COMPLETED, self._on_workflow_completed)
    
    def _setup_feedback_callbacks(self):
        """Setup callbacks for feedback system events."""
        self.feedback_system.add_state_callback(self._on_feedback_event)
        self.feedback_system.add_workflow_callback(self._on_feedback_event)
    
    def _setup_error_callbacks(self):
        """Setup callbacks for error handling events."""
        self.error_handler.add_error_callback(self._notify_error)
    
    def _setup_performance_callbacks(self):
        """Setup callbacks for performance monitoring events."""
        self.performance_monitor.add_metric_callback(self._on_metric_recorded)
        self.performance_monitor.add_usage_callback(self._on_usage_updated)
    
    def _on_feedback_event(self, feedback_type: str, message: str):
        """Handle feedback system events."""
        self.logger.debug(f"Feedback event: {feedback_type} - {message}")
    
    def _on_metric_recorded(self, metric):
        """Handle performance metric recording."""
        self.logger.debug(f"Performance metric recorded: {metric.name} = {metric.value} {metric.unit}")
    
    def _on_usage_updated(self, usage_stats):
        """Handle usage statistics updates."""
        self.logger.debug(f"Usage statistics updated: {usage_stats.total_workflows} workflows")
    
    def initialize(self) -> bool:
        """
        Initialize all system components.
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            self.logger.info("Initializing application controller...")
            
            # Check API keys first
            if not self._check_api_keys():
                self.logger.warning("API keys not configured, showing configuration wizard")
                self._show_config_wizard()
                if not self._check_api_keys():
                    self.logger.error("Failed to configure API keys")
                    return False
            
            # Initialize speech recognition
            self._initialize_speech_recognition()
            
            # Initialize AI processor
            self._initialize_ai_processor()
            
            # Initialize text insertion
            self._initialize_text_insertion()
            
            # Initialize context awareness
            self._initialize_context_awareness()
            
            # Initialize hotkey manager
            self._initialize_hotkey_manager()
            
            # Initialize system tray
            self._initialize_system_tray()
            
            # Start performance monitoring
            self.performance_monitor.start_monitoring()
            
            self.is_initialized = True
            self._set_state(ApplicationState.IDLE)
            
            self.logger.info("Application controller initialization completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize application controller: {e}")
            self.last_error = str(e)
            self._set_state(ApplicationState.ERROR)
            return False
    
    def _check_api_keys(self) -> bool:
        """Check if required API keys are configured."""
        try:
            assemblyai_key = self.config_manager.get_api_key('assemblyai')
            openai_key = self.config_manager.get_api_key('openai')
            
            return bool(assemblyai_key and openai_key)
            
        except Exception as e:
            self.logger.error(f"Error checking API keys: {e}")
            return False
    
    def _initialize_speech_recognition(self):
        """Initialize speech recognition component."""
        try:
            assemblyai_key = self.config_manager.get_api_key('assemblyai')
            openai_key = self.config_manager.get_api_key('openai')
            
            if not assemblyai_key and not openai_key:
                raise ValueError("No API keys configured for speech recognition")
            
            self.speech_recognition = SpeechRecognition(
                assemblyai_api_key=assemblyai_key,
                openai_api_key=openai_key
            )
            self.logger.info("Speech recognition initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize speech recognition: {e}")
            raise
    
    def _initialize_ai_processor(self):
        """Initialize AI text processor component."""
        try:
            api_key = self.config_manager.get_api_key('openai')
            if not api_key:
                raise ValueError("OpenAI API key not configured")
            
            self.text_processor = AITextProcessor(api_key=api_key)
            self.logger.info("AI text processor initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize AI text processor: {e}")
            raise
    
    def _initialize_text_insertion(self):
        """Initialize text insertion component."""
        try:
            self.text_insertion = TextInsertionSystem()
            self.logger.info("Text insertion system initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize text insertion: {e}")
            raise
    
    def _initialize_context_awareness(self):
        """Initialize application context awareness."""
        try:
            self.app_context = ApplicationContext()
            self.context_formatter = ContextTextFormatter(self.app_context)
            self.ai_adapter = AIEnhancementAdapter(self.app_context, self.context_formatter)
            self.logger.info("Context awareness initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize context awareness: {e}")
            raise
    
    def _initialize_hotkey_manager(self):
        """Initialize hotkey manager component."""
        try:
            self.hotkey_manager = HotkeyManager()
            
            # Register primary hotkey using register_callback method
            primary_hotkey = self.config_manager.get('hotkey.primary_hotkey', 'ctrl+win+space')
            self.hotkey_manager.register_callback(primary_hotkey, self._toggle_recording, "Toggle recording")
            
            # Register secondary hotkey if configured
            secondary_hotkey = self.config_manager.get('hotkey.secondary_hotkey')
            if secondary_hotkey:
                self.hotkey_manager.register_callback(secondary_hotkey, self._undo_last_insertion, "Undo last insertion")
            
            # Start listening for hotkeys
            self.hotkey_manager.start_listening()
            self.logger.info("Hotkey manager initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize hotkey manager: {e}")
            raise
    
    def _initialize_system_tray(self):
        """Initialize system tray application."""
        try:
            self.system_tray = create_system_tray_app(
                self._toggle_recording,
                self._show_analytics_dashboard,
                self._show_config_wizard,
                self.shutdown
            )
            self.logger.info("System tray initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize system tray: {e}")
            raise
    
    def _toggle_recording(self):
        """Toggle recording state."""
        if self.state == ApplicationState.RECORDING:
            self._stop_recording()
        else:
            self._start_recording()
    
    def _start_recording(self):
        """Start audio recording."""
        if not self.is_initialized or self.state != ApplicationState.IDLE:
            self.logger.warning("Cannot start recording - not initialized or not idle")
            return
        
        try:
            self._set_state(ApplicationState.RECORDING)
            
            # Record hotkey press
            self.performance_monitor.record_hotkey_press()
            
            # Initialize audio capture
            sample_rate = self.config_manager.get('audio.sample_rate', 16000)
            channels = self.config_manager.get('audio.channels', 1)
            chunk_size = self.config_manager.get('audio.chunk_size', 1024)
            
            self.audio_capture = AudioCapture(
                sample_rate=sample_rate,
                channels=channels,
                chunk_size=chunk_size
            )
            
            # Start audio capture
            self.audio_capture.start_streaming()
            
            # Show recording indicator
            self.feedback_system.visual_feedback.show_recording_indicator()
            
            # Notify workflow manager
            self.workflow_manager.start_recording_workflow(
                audio_capture=self.audio_capture,
                speech_recognition=self.speech_recognition,
                text_processor=self.text_processor,
                text_insertion=self.text_insertion,
                app_context=self.app_context,
                context_formatter=self.context_formatter
            )
            
            self.logger.info("Recording started")
            
        except Exception as e:
            self.logger.error(f"Failed to start recording: {e}")
            self._set_state(ApplicationState.ERROR)
            raise
    
    def _stop_recording(self):
        """Stop audio recording and process the audio."""
        if self.state != ApplicationState.RECORDING:
            self.logger.warning("Cannot stop recording - not currently recording")
            return
        
        try:
            # Stop audio capture
            if self.audio_capture:
                self.audio_capture.stop_streaming()
            
            # Hide recording indicator
            self.feedback_system.visual_feedback.hide_all_indicators()
            
            # Get recorded audio data
            audio_data = self.audio_capture.get_audio_buffer()
            
            if audio_data is None or len(audio_data) == 0:
                self.logger.warning("No audio data captured")
                self._set_state(ApplicationState.IDLE)
                return
            
            # Process the audio through the workflow
            self._process_audio_data(audio_data)
            
        except Exception as e:
            self.logger.error(f"Failed to stop recording: {e}")
            self._set_state(ApplicationState.ERROR)
            raise
    
    def _cancel_recording(self):
        """Cancel the current recording."""
        if self.state != ApplicationState.RECORDING:
            self.logger.warning("Cannot cancel recording - not currently recording")
            return
        
        try:
            # Stop audio capture
            if self.audio_capture:
                self.audio_capture.stop_streaming()
                self.audio_capture = None
            
            # Hide recording indicator
            self.feedback_system.visual_feedback.hide_all_indicators()
            
            # Reset to idle state
            self._set_state(ApplicationState.IDLE)
            
            self.logger.info("Recording cancelled")
            
        except Exception as e:
            self.logger.error(f"Failed to cancel recording: {e}")
            self._set_state(ApplicationState.ERROR)
            raise
    
    def _undo_last_insertion(self):
        """Undo the last text insertion."""
        try:
            if self.text_insertion:
                self.text_insertion.undo_last_insertion()
                self.logger.info("Last insertion undone")
        except Exception as e:
            self.logger.error(f"Failed to undo last insertion: {e}")
    
    def _record_workflow_step(self, step: WorkflowStep):
        """Record workflow step for performance monitoring."""
        if hasattr(self, 'workflow_start_time'):
            duration = time.time() - self.workflow_start_time
            self.performance_monitor.record_workflow_step(step, duration)
            self.workflow_start_time = time.time()
        else:
            self.workflow_start_time = time.time()
    
    def _on_recording_start(self, context):
        """Handle recording start event."""
        self._record_workflow_step(WorkflowStep.RECORDING)
    
    def _on_transcribing_start(self, context):
        """Handle transcribing start event."""
        self._record_workflow_step(WorkflowStep.TRANSCRIBING)
    
    def _on_enhancing_start(self, context):
        """Handle enhancing start event."""
        self._record_workflow_step(WorkflowStep.ENHANCING)
    
    def _on_formatting_start(self, context):
        """Handle formatting start event."""
        self._record_workflow_step(WorkflowStep.FORMATTING)
    
    def _on_inserting_start(self, context):
        """Handle inserting start event."""
        self._record_workflow_step(WorkflowStep.INSERTING)
    
    def _on_workflow_completed(self, context):
        """Handle workflow completion."""
        try:
            # Record text insertion
            self.performance_monitor.record_text_insertion()
            
            # End workflow tracking
            self.performance_monitor.end_workflow_tracking(True)
            
            # Provide feedback
            self.feedback_system.show_processing_indicator(False)
            self.feedback_system.show_success_indicator(True)
            
            # Update metrics
            self.metrics.successful_workflows += 1
            self._notify_metrics_update()
            
            self._set_state(ApplicationState.IDLE)
            self.logger.info("Workflow completed successfully")
            
        except Exception as e:
            self.logger.error(f"Error in workflow completion: {e}")
            self._on_workflow_error(str(e))
    
    def _on_workflow_error(self, error_message: str, context=None):
        """Handle workflow error."""
        try:
            # Record error
            self.performance_monitor.record_error()
            
            # End workflow tracking
            self.performance_monitor.end_workflow_tracking(False, error_message)
            
            # Provide feedback
            self.feedback_system.show_processing_indicator(False)
            self.feedback_system.show_error_indicator(True)
            
            # Update metrics
            self.metrics.failed_workflows += 1
            self._notify_metrics_update()
            
            # Handle error
            self.error_handler.handle_error(Exception(error_message), context=context)
            
            self._set_state(ApplicationState.ERROR)
            self.last_error = error_message
            self.logger.error(f"Workflow error: {error_message}")
            
        except Exception as e:
            self.logger.error(f"Error handling workflow error: {e}")
    
    def _on_workflow_completion(self, context):
        """Handle workflow completion (legacy callback)."""
        self._on_workflow_completed(context)
    
    def _set_state(self, new_state: ApplicationState):
        """Set application state and notify callbacks."""
        if self.state != new_state:
            old_state = self.state
            self.state = new_state
            
            # Notify state change callbacks
            for callback in self.state_change_callbacks:
                try:
                    callback(new_state)
                except Exception as e:
                    self.logger.error(f"State change callback error: {e}")
            
            self.logger.info(f"Application state changed: {old_state} -> {new_state}")
    
    def _notify_error(self, error_message: str):
        """Notify error callbacks."""
        self.last_error = error_message
        
        for callback in self.error_callbacks:
            try:
                callback(error_message)
            except Exception as e:
                self.logger.error(f"Error callback error: {e}")
    
    def _notify_metrics_update(self):
        """Notify metrics callbacks."""
        for callback in self.metrics_callbacks:
            try:
                callback(self.metrics)
            except Exception as e:
                self.logger.error(f"Metrics callback error: {e}")
    
    def _show_config_wizard(self):
        """Show configuration wizard."""
        # Implementation would show configuration dialog
        self.logger.info("Configuration wizard requested")
    
    def _show_analytics_dashboard(self):
        """Show analytics dashboard."""
        try:
            self.analytics_dashboard.show_dashboard()
            self.logger.info("Analytics dashboard opened")
        except Exception as e:
            self.logger.error(f"Failed to show analytics dashboard: {e}")
    
    def add_state_change_callback(self, callback: Callable[[ApplicationState], None]):
        """Add callback for state changes."""
        self.state_change_callbacks.append(callback)
    
    def add_error_callback(self, callback: Callable[[str], None]):
        """Add callback for errors."""
        self.error_callbacks.append(callback)
    
    def add_metrics_callback(self, callback: Callable[[WorkflowMetrics], None]):
        """Add callback for metrics updates."""
        self.metrics_callbacks.append(callback)
    
    def get_state(self) -> ApplicationState:
        """Get current application state."""
        return self.state
    
    def get_workflow_step(self) -> WorkflowStep:
        """Get current workflow step."""
        return self.workflow_manager.get_current_step()
    
    def get_workflow_context(self):
        """Get current workflow context."""
        return self.workflow_manager.get_current_context()
    
    def get_metrics(self) -> WorkflowMetrics:
        """Get current workflow metrics."""
        return self.metrics
    
    def get_last_error(self) -> Optional[str]:
        """Get last error message."""
        return self.last_error
    
    def get_feedback_system(self) -> UserFeedbackSystem:
        """Get feedback system."""
        return self.feedback_system
    
    def get_error_handler(self):
        """Get error handler."""
        return self.error_handler
    
    def get_performance_monitor(self) -> PerformanceMonitor:
        """Get performance monitor."""
        return self.performance_monitor
    
    def get_performance_reporter(self) -> PerformanceReporter:
        """Get performance reporter."""
        return self.performance_reporter
    
    def get_analytics_dashboard(self) -> AnalyticsDashboard:
        """Get analytics dashboard."""
        return self.analytics_dashboard
    
    def get_system_tray(self):
        """Get system tray application."""
        return self.system_tray
    
    def generate_performance_report(self) -> str:
        """Generate performance report."""
        return self.performance_reporter.generate_performance_report()
    
    def export_anonymized_data(self, filepath: str):
        """Export anonymized data."""
        data = self.performance_monitor.export_anonymized_data()
        with open(filepath, 'w') as f:
            import json
            from dataclasses import asdict
            json.dump(asdict(data), f, indent=2)
    
    def _process_audio_data(self, audio_data):
        """Process audio data through the workflow."""
        try:
            # Show processing indicator
            self.feedback_system.visual_feedback.show_processing_indicator()
            
            # Process audio in background
            self.workflow_manager.execute_workflow(
                audio_data=audio_data.tobytes(),
                speech_recognition=self.speech_recognition,
                text_processor=self.text_processor,
                text_insertion=self.text_insertion,
                app_context=self.app_context,
                context_formatter=self.context_formatter,
                ai_adapter=self.ai_adapter
            )
            
            self.logger.info("Audio processing started")
            
        except Exception as e:
            self.logger.error(f"Failed to process audio data: {e}")
            self._set_state(ApplicationState.ERROR)
            raise
    
    def shutdown(self):
        """Shutdown the application controller."""
        self.logger.info("Shutting down application controller...")
        
        try:
            # Stop performance monitoring
            if self.performance_monitor:
                self.performance_monitor.shutdown()
            
            # Stop hotkey manager
            if self.hotkey_manager:
                self.hotkey_manager.stop_listening()
            
            # Stop audio capture
            if self.audio_capture:
                self.audio_capture.stop_recording()
            
            # Close system tray
            if self.system_tray:
                self.system_tray.shutdown()
            
            # Close analytics dashboard
            if self.analytics_dashboard:
                self.analytics_dashboard.close_dashboard()
            
            self.logger.info("Application controller shutdown completed")
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}") 
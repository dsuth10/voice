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
from .config import ConfigManager
from .audio import AudioCapture
from .recognition import SpeechRecognition
from .ai_processing.text_enhancement import AITextProcessor
from .text_insertion import TextInsertionSystem
from .hotkeys.enhanced_hotkey_manager import EnhancedHotkeyManager
from .context import ApplicationContext, ContextTextFormatter, AIEnhancementAdapter
from .workflow_manager import WorkflowManager, WorkflowStep
from .feedback_system import UserFeedbackSystem, FeedbackType, FeedbackLevel
from .error_handler import ErrorHandler, ErrorNotifier
from .performance_monitor import PerformanceMonitor, PerformanceReporter


class ApplicationState(Enum):
    """Application state enumeration."""
    IDLE = "idle"
    RECORDING = "recording"
    PROCESSING = "processing"
    ERROR = "error"
    CONFIGURING = "configuring"


@dataclass
class WorkflowMetrics:
    """Metrics for tracking workflow performance."""
    recording_start_time: Optional[float] = None
    recording_duration: Optional[float] = None
    transcription_time: Optional[float] = None
    enhancement_time: Optional[float] = None
    insertion_time: Optional[float] = None
    total_time: Optional[float] = None
    error_count: int = 0
    success_count: int = 0


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
        
        # Initialize performance monitoring
        monitoring_interval = self.config_manager.get('performance.monitoring_interval', 1.0)
        self.performance_monitor = PerformanceMonitor(monitoring_interval)
        self.performance_reporter = PerformanceReporter(self.performance_monitor)
        
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
        # Step callbacks
        self.workflow_manager.add_step_callback(WorkflowStep.RECORDING, self._on_recording_start)
        self.workflow_manager.add_step_callback(WorkflowStep.TRANSCRIBING, self._on_transcribing_start)
        self.workflow_manager.add_step_callback(WorkflowStep.ENHANCING, self._on_enhancing_start)
        self.workflow_manager.add_step_callback(WorkflowStep.FORMATTING, self._on_formatting_start)
        self.workflow_manager.add_step_callback(WorkflowStep.INSERTING, self._on_inserting_start)
        self.workflow_manager.add_step_callback(WorkflowStep.COMPLETED, self._on_workflow_completed)
        self.workflow_manager.add_step_callback(WorkflowStep.ERROR, self._on_workflow_error)
        
        # Completion and error callbacks
        self.workflow_manager.add_completion_callback(self._on_workflow_completion)
        self.workflow_manager.add_error_callback(self._on_workflow_error)
    
    def _setup_feedback_callbacks(self):
        """Setup callbacks for feedback system events."""
        # Add feedback system to workflow manager callbacks
        self.workflow_manager.add_step_callback(WorkflowStep.RECORDING, 
            lambda ctx: self.feedback_system.on_workflow_step_change(WorkflowStep.RECORDING))
        self.workflow_manager.add_step_callback(WorkflowStep.TRANSCRIBING, 
            lambda ctx: self.feedback_system.on_workflow_step_change(WorkflowStep.TRANSCRIBING))
        self.workflow_manager.add_step_callback(WorkflowStep.ENHANCING, 
            lambda ctx: self.feedback_system.on_workflow_step_change(WorkflowStep.ENHANCING))
        self.workflow_manager.add_step_callback(WorkflowStep.INSERTING, 
            lambda ctx: self.feedback_system.on_workflow_step_change(WorkflowStep.INSERTING))
        self.workflow_manager.add_step_callback(WorkflowStep.COMPLETED, 
            lambda ctx: self.feedback_system.on_workflow_step_change(WorkflowStep.COMPLETED))
        self.workflow_manager.add_step_callback(WorkflowStep.ERROR, 
            lambda ctx: self.feedback_system.on_workflow_step_change(WorkflowStep.ERROR))
    
    def _setup_error_callbacks(self):
        """Setup callbacks for error handling events."""
        # Add error notifier to error handler callbacks
        self.error_handler.add_error_callback(self.error_notifier.notify_error)
        self.error_handler.add_recovery_callback(self.error_notifier.notify_recovery)
    
    def _setup_performance_callbacks(self):
        """Setup callbacks for performance monitoring events."""
        # Add performance monitoring to workflow manager callbacks
        self.workflow_manager.add_step_callback(WorkflowStep.RECORDING, 
            lambda ctx: self._record_workflow_step(WorkflowStep.RECORDING))
        self.workflow_manager.add_step_callback(WorkflowStep.TRANSCRIBING, 
            lambda ctx: self._record_workflow_step(WorkflowStep.TRANSCRIBING))
        self.workflow_manager.add_step_callback(WorkflowStep.ENHANCING, 
            lambda ctx: self._record_workflow_step(WorkflowStep.ENHANCING))
        self.workflow_manager.add_step_callback(WorkflowStep.FORMATTING, 
            lambda ctx: self._record_workflow_step(WorkflowStep.FORMATTING))
        self.workflow_manager.add_step_callback(WorkflowStep.INSERTING, 
            lambda ctx: self._record_workflow_step(WorkflowStep.INSERTING))
    
    def initialize(self) -> bool:
        """
        Initialize all system components and start the application.
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            self.logger.info("Starting application initialization")
            
            # Check API keys first
            if not self._check_api_keys():
                self._set_state(ApplicationState.CONFIGURING)
                self._show_config_wizard()
                if not self._check_api_keys():
                    self.logger.error("API keys not configured after wizard")
                    return False
            
            # Initialize API-dependent components
            self._initialize_speech_recognition()
            self._initialize_ai_processor()
            
            # Initialize other components
            self._initialize_text_insertion()
            self._initialize_context_awareness()
            self._initialize_hotkey_manager()
            
            # Start hotkey listening
            self.hotkey_manager.start_listening()
            
            # Start performance monitoring
            self.performance_monitor.start_monitoring()
            
            self.is_initialized = True
            self._set_state(ApplicationState.IDLE)
            
            self.logger.info("Application initialization completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Initialization failed: {e}")
            error_info = self.error_handler.handle_error(e, application_state=ApplicationState.CONFIGURING)
            self.last_error = str(e)
            self._set_state(ApplicationState.ERROR)
            return False
    
    def _check_api_keys(self) -> bool:
        """
        Check if required API keys are available.
        
        Returns:
            True if all required keys are present
        """
        try:
            assemblyai_key = self.config_manager.get_api_key('assemblyai')
            openai_key = self.config_manager.get_api_key('openai')
            
            return bool(assemblyai_key and openai_key)
            
        except Exception as e:
            self.logger.error(f"Error checking API keys: {e}")
            self.error_handler.handle_error(e, application_state=ApplicationState.CONFIGURING)
            return False
    
    def _initialize_speech_recognition(self):
        """Initialize speech recognition component."""
        try:
            assemblyai_key = self.config_manager.get_api_key('assemblyai')
            self.speech_recognition = SpeechRecognition(api_key=assemblyai_key)
            self.logger.info("Speech recognition initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize speech recognition: {e}")
            self.error_handler.handle_error(e, application_state=ApplicationState.CONFIGURING)
            raise
    
    def _initialize_ai_processor(self):
        """Initialize AI text processing component."""
        try:
            openai_key = self.config_manager.get_api_key('openai')
            model = self.config_manager.get('ai.model', 'gpt-4o-mini')
            self.text_processor = AITextProcessor(api_key=openai_key, model=model)
            self.logger.info("AI text processor initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize AI processor: {e}")
            self.error_handler.handle_error(e, application_state=ApplicationState.CONFIGURING)
            raise
    
    def _initialize_text_insertion(self):
        """Initialize text insertion component."""
        try:
            self.text_insertion = TextInsertionSystem()
            self.logger.info("Text insertion system initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize text insertion: {e}")
            self.error_handler.handle_error(e, application_state=ApplicationState.CONFIGURING)
            raise
    
    def _initialize_context_awareness(self):
        """Initialize context awareness components."""
        try:
            self.app_context = ApplicationContext()
            self.context_formatter = ContextTextFormatter()
            self.ai_adapter = AIEnhancementAdapter()
            self.logger.info("Context awareness components initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize context awareness: {e}")
            self.error_handler.handle_error(e, application_state=ApplicationState.CONFIGURING)
            raise
    
    def _initialize_hotkey_manager(self):
        """Initialize hotkey management component."""
        try:
            hotkey_config = {
                'default_hotkey': self.config_manager.get('hotkey.default', 'ctrl+win+space'),
                'push_to_talk': self.config_manager.get('hotkey.push_to_talk', True),
                'cancel_hotkey': self.config_manager.get('hotkey.cancel', 'ctrl+win+c'),
                'undo_hotkey': self.config_manager.get('hotkey.undo', 'ctrl+win+z')
            }
            
            self.hotkey_manager = EnhancedHotkeyManager(hotkey_config)
            
            # Register hotkey callbacks
            self.hotkey_manager.register_hotkey(
                hotkey_config['default_hotkey'],
                self._toggle_recording,
                "Toggle recording"
            )
            
            self.hotkey_manager.register_hotkey(
                hotkey_config['cancel_hotkey'],
                self._cancel_recording,
                "Cancel recording"
            )
            
            self.hotkey_manager.register_hotkey(
                hotkey_config['undo_hotkey'],
                self._undo_last_insertion,
                "Undo last insertion"
            )
            
            self.logger.info("Hotkey manager initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize hotkey manager: {e}")
            self.error_handler.handle_error(e, application_state=ApplicationState.CONFIGURING)
            raise
    
    def _toggle_recording(self):
        """Toggle recording state based on current state."""
        with self.workflow_lock:
            current_step = self.workflow_manager.get_current_step()
            
            if current_step == WorkflowStep.RECORDING:
                self._stop_recording()
            elif current_step == WorkflowStep.IDLE:
                self._start_recording()
    
    def _start_recording(self):
        """Start audio recording workflow."""
        if self.workflow_manager.get_current_step() != WorkflowStep.IDLE:
            self.logger.warning(f"Cannot start recording in current state")
            return
        
        try:
            self.logger.info("Starting recording workflow")
            self._set_state(ApplicationState.RECORDING)
            
            # Record hotkey press
            self.performance_monitor.record_hotkey_press()
            
            # Start workflow tracking
            workflow_id = f"workflow_{int(time.time())}"
            self.performance_monitor.start_workflow_tracking(workflow_id)
            
            # Initialize audio capture with configuration
            audio_config = {
                'sample_rate': self.config_manager.get('audio.sample_rate', 16000),
                'channels': self.config_manager.get('audio.channels', 1),
                'chunk_size': self.config_manager.get('audio.chunk_size', 1024),
                'silence_threshold': self.config_manager.get('audio.silence_threshold', 0.01),
                'noise_filter_enabled': self.config_manager.get('audio.noise_filter', True)
            }
            
            self.audio_capture = AudioCapture(**audio_config)
            
            # Start workflow
            success = self.workflow_manager.start_recording_workflow(
                self.audio_capture,
                self.speech_recognition,
                self.text_processor,
                self.text_insertion,
                self.app_context,
                self.context_formatter
            )
            
            if success:
                self.logger.info("Recording workflow started successfully")
            else:
                raise Exception("Failed to start recording workflow")
            
        except Exception as e:
            self.logger.error(f"Failed to start recording: {e}")
            error_info = self.error_handler.handle_error(e, WorkflowStep.RECORDING, ApplicationState.RECORDING)
            self.performance_monitor.record_error()
            self.last_error = str(e)
            self._set_state(ApplicationState.ERROR)
            self._notify_error(f"Failed to start recording: {e}")
    
    def _stop_recording(self):
        """Stop audio recording and process the audio."""
        try:
            self.logger.info("Stopping recording workflow")
            
            # Stop workflow and begin processing
            success = self.workflow_manager.stop_recording_workflow()
            
            if success:
                self._set_state(ApplicationState.PROCESSING)
                self.logger.info("Recording stopped, processing started")
            else:
                raise Exception("Failed to stop recording workflow")
            
        except Exception as e:
            self.logger.error(f"Failed to stop recording: {e}")
            error_info = self.error_handler.handle_error(e, WorkflowStep.RECORDING, ApplicationState.RECORDING)
            self.performance_monitor.record_error()
            self.last_error = str(e)
            self._set_state(ApplicationState.ERROR)
            self._notify_error(f"Failed to stop recording: {e}")
    
    def _cancel_recording(self):
        """Cancel current recording without processing."""
        try:
            self.logger.info("Canceling recording workflow")
            self.workflow_manager.cancel_workflow()
            self._set_state(ApplicationState.IDLE)
            self.logger.info("Recording canceled")
            
        except Exception as e:
            self.logger.error(f"Failed to cancel recording: {e}")
            self.error_handler.handle_error(e, WorkflowStep.RECORDING, ApplicationState.RECORDING)
    
    def _undo_last_insertion(self):
        """Undo the last text insertion."""
        try:
            if self.text_insertion:
                self.text_insertion.undo_last_insertion()
                self.logger.info("Last insertion undone")
        except Exception as e:
            self.logger.error(f"Failed to undo insertion: {e}")
            self.error_handler.handle_error(e, application_state=self.state)
    
    def _record_workflow_step(self, step: WorkflowStep):
        """Record workflow step for performance monitoring."""
        # This will be called by workflow manager step callbacks
        # The actual timing is handled by the workflow manager
        pass
    
    # Workflow callback methods
    def _on_recording_start(self, context):
        """Callback when recording starts."""
        self.logger.info("Recording started")
        self._set_state(ApplicationState.RECORDING)
    
    def _on_transcribing_start(self, context):
        """Callback when transcription starts."""
        self.logger.info("Transcription started")
        self._set_state(ApplicationState.PROCESSING)
    
    def _on_enhancing_start(self, context):
        """Callback when text enhancement starts."""
        self.logger.info("Text enhancement started")
    
    def _on_formatting_start(self, context):
        """Callback when text formatting starts."""
        self.logger.info("Text formatting started")
    
    def _on_inserting_start(self, context):
        """Callback when text insertion starts."""
        self.logger.info("Text insertion started")
    
    def _on_workflow_completed(self, context):
        """Callback when workflow completes successfully."""
        self.logger.info("Workflow completed successfully")
        self._set_state(ApplicationState.IDLE)
        
        # Record text insertion
        self.performance_monitor.record_text_insertion()
        
        # End workflow tracking
        self.performance_monitor.end_workflow_tracking(True)
        
        # Update metrics
        if context.step_times:
            self.metrics.transcription_time = context.step_times.get(WorkflowStep.TRANSCRIBING)
            self.metrics.enhancement_time = context.step_times.get(WorkflowStep.ENHANCING)
            self.metrics.insertion_time = context.step_times.get(WorkflowStep.INSERTING)
            self.metrics.total_time = context.step_times.get(WorkflowStep.COMPLETED)
        
        self._notify_metrics_update()
    
    def _on_workflow_error(self, error_message: str, context=None):
        """Callback when workflow encounters an error."""
        self.logger.error(f"Workflow error: {error_message}")
        # Create a generic exception for error handling
        exception = Exception(error_message)
        error_info = self.error_handler.handle_error(exception, WorkflowStep.ERROR, ApplicationState.ERROR)
        self.performance_monitor.record_error()
        self.last_error = error_message
        self._set_state(ApplicationState.ERROR)
        self._notify_error(error_message)
        
        # End workflow tracking with error
        self.performance_monitor.end_workflow_tracking(False, error_message)
    
    def _on_workflow_completion(self, context):
        """Callback when workflow completes (success or error)."""
        # This is called after the specific step callbacks
        pass
    
    def _set_state(self, new_state: ApplicationState):
        """Update application state and notify callbacks."""
        if self.state != new_state:
            old_state = self.state
            self.state = new_state
            self.logger.info(f"State changed: {old_state} -> {new_state}")
            
            # Notify feedback system
            self.feedback_system.on_application_state_change(new_state)
            
            # Notify state change callbacks
            for callback in self.state_change_callbacks:
                try:
                    callback(new_state)
                except Exception as e:
                    self.logger.error(f"State change callback error: {e}")
    
    def _notify_error(self, error_message: str):
        """Notify error callbacks."""
        # Notify feedback system
        self.feedback_system.on_error(error_message)
        
        for callback in self.error_callbacks:
            try:
                callback(error_message)
            except Exception as e:
                self.logger.error(f"Error callback error: {e}")
    
    def _notify_metrics_update(self):
        """Notify metrics callbacks."""
        # Update metrics from workflow manager
        workflow_metrics = self.workflow_manager.get_metrics()
        self.metrics.recording_duration = workflow_metrics.recording_duration
        self.metrics.transcription_time = workflow_metrics.transcription_time
        self.metrics.enhancement_time = workflow_metrics.enhancement_time
        self.metrics.insertion_time = workflow_metrics.insertion_time
        self.metrics.total_time = workflow_metrics.total_time
        self.metrics.error_count = workflow_metrics.error_count
        self.metrics.success_count = workflow_metrics.success_count
        
        for callback in self.metrics_callbacks:
            try:
                callback(self.metrics)
            except Exception as e:
                self.logger.error(f"Metrics callback error: {e}")
    
    def _show_config_wizard(self):
        """Show configuration wizard for API key setup."""
        # This will be implemented in a separate UI module
        self.logger.info("Configuration wizard should be shown")
        # For now, we'll just log that it should be shown
    
    def add_state_change_callback(self, callback: Callable[[ApplicationState], None]):
        """Add callback for state changes."""
        self.state_change_callbacks.append(callback)
    
    def add_error_callback(self, callback: Callable[[str], None]):
        """Add callback for error notifications."""
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
        return self.workflow_manager.get_workflow_context()
    
    def get_metrics(self) -> WorkflowMetrics:
        """Get current workflow metrics."""
        return self.metrics
    
    def get_last_error(self) -> Optional[str]:
        """Get the last error message."""
        return self.last_error
    
    def get_feedback_system(self) -> UserFeedbackSystem:
        """Get the feedback system for external access."""
        return self.feedback_system
    
    def get_error_handler(self):
        """Get the error handler for external access."""
        return self.error_handler
    
    def get_performance_monitor(self) -> PerformanceMonitor:
        """Get the performance monitor for external access."""
        return self.performance_monitor
    
    def get_performance_reporter(self) -> PerformanceReporter:
        """Get the performance reporter for external access."""
        return self.performance_reporter
    
    def generate_performance_report(self) -> str:
        """Generate a performance report."""
        return self.performance_reporter.generate_performance_report()
    
    def export_anonymized_data(self, filepath: str):
        """Export anonymized performance data."""
        self.performance_reporter.export_anonymized_report(filepath)
    
    def shutdown(self):
        """Shutdown the application and cleanup resources."""
        self.logger.info("Shutting down application controller")
        
        try:
            # Cancel any running workflow
            self.workflow_manager.cancel_workflow()
            
            # Cleanup hotkey manager
            if self.hotkey_manager:
                self.hotkey_manager.unregister_all()
            
            # Cleanup audio capture
            if self.audio_capture:
                self.audio_capture.stop_streaming()
            
            # Shutdown workflow manager
            self.workflow_manager.shutdown()
            
            # Shutdown feedback system
            self.feedback_system.shutdown()
            
            # Shutdown error handler
            self.error_handler.shutdown()
            
            # Shutdown performance monitor
            self.performance_monitor.shutdown()
            
            self._set_state(ApplicationState.IDLE)
            self.logger.info("Application controller shutdown completed")
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}") 
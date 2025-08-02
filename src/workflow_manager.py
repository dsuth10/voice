"""
Workflow Manager for Voice Dictation Assistant

This module provides workflow management functionality for coordinating the dictation process
from hotkey press to text insertion, with proper state transitions and concurrency handling.
"""

import threading
import time
import queue
import logging
from typing import Optional, Callable, Dict, Any, List
from dataclasses import dataclass
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, Future

from .application_controller import ApplicationState, WorkflowMetrics


class WorkflowStep(Enum):
    """Workflow step enumeration."""
    IDLE = "idle"
    RECORDING = "recording"
    TRANSCRIBING = "transcribing"
    ENHANCING = "enhancing"
    FORMATTING = "formatting"
    INSERTING = "inserting"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class WorkflowContext:
    """Context for workflow execution."""
    audio_data: Optional[bytes] = None
    transcription: Optional[str] = None
    enhanced_text: Optional[str] = None
    formatted_text: Optional[str] = None
    context_type: Optional[str] = None
    error_message: Optional[str] = None
    start_time: Optional[float] = None
    step_times: Dict[WorkflowStep, float] = None
    
    def __post_init__(self):
        if self.step_times is None:
            self.step_times = {}


class WorkflowManager:
    """
    Manages the dictation workflow with proper state transitions and concurrency.
    
    This class handles the complete workflow from hotkey press to text insertion,
    ensuring proper state management, error handling, and performance tracking.
    """
    
    def __init__(self, max_workers: int = 2):
        """
        Initialize the workflow manager.
        
        Args:
            max_workers: Maximum number of worker threads for processing
        """
        self.logger = logging.getLogger(__name__)
        
        # Threading and concurrency
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.workflow_lock = threading.Lock()
        self.current_workflow: Optional[Future] = None
        
        # State management
        self.current_step = WorkflowStep.IDLE
        self.workflow_context: Optional[WorkflowContext] = None
        
        # Callbacks
        self.step_callbacks: Dict[WorkflowStep, Callable[[WorkflowContext], None]] = {}
        self.completion_callbacks: List[Callable[[WorkflowContext], None]] = []
        self.error_callbacks: List[Callable[[str, WorkflowContext], None]] = []
        
        # Performance tracking
        self.metrics = WorkflowMetrics()
        
        self.logger.info("WorkflowManager initialized")
    
    def start_recording_workflow(self, 
                                audio_capture,
                                speech_recognition,
                                text_processor,
                                text_insertion,
                                app_context,
                                context_formatter) -> bool:
        """
        Start the recording workflow.
        
        Args:
            audio_capture: Audio capture component
            speech_recognition: Speech recognition component
            text_processor: AI text processor component
            text_insertion: Text insertion component
            app_context: Application context component
            context_formatter: Context formatter component
            
        Returns:
            True if workflow started successfully
        """
        with self.workflow_lock:
            if self.current_step != WorkflowStep.IDLE:
                self.logger.warning(f"Cannot start workflow in state: {self.current_step}")
                return False
            
            try:
                self.logger.info("Starting recording workflow")
                
                # Initialize workflow context
                self.workflow_context = WorkflowContext()
                self.workflow_context.start_time = time.time()
                
                # Start recording
                self._set_step(WorkflowStep.RECORDING)
                
                # Start audio capture
                audio_capture.start_streaming(
                    callback=self._audio_callback,
                    silence_callback=self._silence_callback,
                    speech_callback=self._speech_callback,
                    level_callback=self._level_callback
                )
                
                # Store components for later use
                self._components = {
                    'audio_capture': audio_capture,
                    'speech_recognition': speech_recognition,
                    'text_processor': text_processor,
                    'text_insertion': text_insertion,
                    'app_context': app_context,
                    'context_formatter': context_formatter
                }
                
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to start recording workflow: {e}")
                self._handle_workflow_error(str(e))
                return False
    
    def stop_recording_workflow(self) -> bool:
        """
        Stop recording and begin processing workflow.
        
        Returns:
            True if workflow transitioned successfully
        """
        with self.workflow_lock:
            if self.current_step != WorkflowStep.RECORDING:
                self.logger.warning(f"Cannot stop recording in state: {self.current_step}")
                return False
            
            try:
                self.logger.info("Stopping recording and starting processing")
                
                # Stop audio capture and get data
                audio_capture = self._components['audio_capture']
                audio_data = audio_capture.stop_streaming()
                
                # Store audio data in context
                self.workflow_context.audio_data = audio_data
                
                # Calculate recording duration
                if self.workflow_context.start_time:
                    recording_duration = time.time() - self.workflow_context.start_time
                    self.metrics.recording_duration = recording_duration
                
                # Start processing in background thread
                self.current_workflow = self.executor.submit(
                    self._process_workflow,
                    self.workflow_context,
                    self._components
                )
                
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to stop recording workflow: {e}")
                self._handle_workflow_error(str(e))
                return False
    
    def _process_workflow(self, context: WorkflowContext, components: Dict[str, Any]):
        """Process the complete workflow from transcription to insertion."""
        try:
            self.logger.info("Processing workflow started")
            
            # Step 1: Speech Recognition
            self._set_step(WorkflowStep.TRANSCRIBING)
            transcription_start = time.time()
            
            speech_recognition = components['speech_recognition']
            transcription = speech_recognition.transcribe(context.audio_data)
            
            if not transcription:
                raise Exception("Transcription failed or returned empty result")
            
            context.transcription = transcription
            context.step_times[WorkflowStep.TRANSCRIBING] = time.time() - transcription_start
            self.metrics.transcription_time = context.step_times[WorkflowStep.TRANSCRIBING]
            
            self.logger.info(f"Transcription completed: {transcription[:100]}...")
            
            # Step 2: Detect Application Context
            app_context = components['app_context']
            context.context_type = app_context.detect_context()
            context_prompt = app_context.get_ai_prompt_for_context(context.context_type)
            
            self.logger.info(f"Detected context: {context.context_type}")
            
            # Step 3: AI Text Enhancement
            self._set_step(WorkflowStep.ENHANCING)
            enhancement_start = time.time()
            
            text_processor = components['text_processor']
            enhanced_text = text_processor.enhance_text(
                transcription,
                context=context.context_type,
                custom_instructions=context_prompt
            )
            
            context.enhanced_text = enhanced_text
            context.step_times[WorkflowStep.ENHANCING] = time.time() - enhancement_start
            self.metrics.enhancement_time = context.step_times[WorkflowStep.ENHANCING]
            
            self.logger.info(f"Text enhancement completed: {enhanced_text[:100]}...")
            
            # Step 4: Context-Specific Formatting
            self._set_step(WorkflowStep.FORMATTING)
            formatting_start = time.time()
            
            context_formatter = components['context_formatter']
            formatted_text = context_formatter.format_text(enhanced_text, context.context_type)
            
            context.formatted_text = formatted_text
            context.step_times[WorkflowStep.FORMATTING] = time.time() - formatting_start
            
            self.logger.info(f"Text formatting completed: {formatted_text[:100]}...")
            
            # Step 5: Text Insertion
            self._set_step(WorkflowStep.INSERTING)
            insertion_start = time.time()
            
            text_insertion = components['text_insertion']
            success = text_insertion.insert_text(formatted_text)
            
            context.step_times[WorkflowStep.INSERTING] = time.time() - insertion_start
            self.metrics.insertion_time = context.step_times[WorkflowStep.INSERTING]
            
            if not success:
                raise Exception("Text insertion failed")
            
            # Calculate total processing time
            if context.start_time:
                total_time = time.time() - context.start_time
                self.metrics.total_time = total_time
                context.step_times[WorkflowStep.COMPLETED] = total_time
            
            # Update success metrics
            self.metrics.success_count += 1
            
            # Complete workflow
            self._set_step(WorkflowStep.COMPLETED)
            self._notify_completion(context)
            
            self.logger.info("Workflow completed successfully")
            
        except Exception as e:
            self.logger.error(f"Workflow processing failed: {e}")
            context.error_message = str(e)
            self.metrics.error_count += 1
            self._set_step(WorkflowStep.ERROR)
            self._handle_workflow_error(str(e), context)
    
    def _set_step(self, step: WorkflowStep):
        """Update workflow step and notify callbacks."""
        if self.current_step != step:
            old_step = self.current_step
            self.current_step = step
            self.logger.info(f"Workflow step changed: {old_step} -> {step}")
            
            # Notify step callbacks
            if step in self.step_callbacks:
                try:
                    self.step_callbacks[step](self.workflow_context)
                except Exception as e:
                    self.logger.error(f"Step callback error: {e}")
    
    def _handle_workflow_error(self, error_message: str, context: Optional[WorkflowContext] = None):
        """Handle workflow errors."""
        self.logger.error(f"Workflow error: {error_message}")
        
        # Notify error callbacks
        for callback in self.error_callbacks:
            try:
                callback(error_message, context or self.workflow_context)
            except Exception as e:
                self.logger.error(f"Error callback error: {e}")
    
    def _notify_completion(self, context: WorkflowContext):
        """Notify completion callbacks."""
        for callback in self.completion_callbacks:
            try:
                callback(context)
            except Exception as e:
                self.logger.error(f"Completion callback error: {e}")
    
    def _audio_callback(self, audio_chunk, level):
        """Callback for audio chunks during recording."""
        # Can be used for real-time processing if needed
        pass
    
    def _silence_callback(self, duration):
        """Callback for silence detection."""
        self.logger.debug(f"Silence detected for {duration}s")
    
    def _speech_callback(self, level):
        """Callback for speech detection."""
        self.logger.debug(f"Speech detected at level {level}")
    
    def _level_callback(self, level):
        """Callback for audio level monitoring."""
        # Can be used for visual feedback
        pass
    
    def cancel_workflow(self):
        """Cancel the current workflow."""
        with self.workflow_lock:
            if self.current_step == WorkflowStep.RECORDING:
                self.logger.info("Canceling workflow")
                
                # Stop audio capture
                if 'audio_capture' in self._components:
                    self._components['audio_capture'].stop_streaming()
                
                # Cancel background processing
                if self.current_workflow and not self.current_workflow.done():
                    self.current_workflow.cancel()
                
                self._set_step(WorkflowStep.IDLE)
                self.workflow_context = None
                self._components = {}
                
                self.logger.info("Workflow canceled")
    
    def get_current_step(self) -> WorkflowStep:
        """Get current workflow step."""
        return self.current_step
    
    def get_workflow_context(self) -> Optional[WorkflowContext]:
        """Get current workflow context."""
        return self.workflow_context
    
    def get_metrics(self) -> WorkflowMetrics:
        """Get workflow metrics."""
        return self.metrics
    
    def add_step_callback(self, step: WorkflowStep, callback: Callable[[WorkflowContext], None]):
        """Add callback for specific workflow steps."""
        self.step_callbacks[step] = callback
    
    def add_completion_callback(self, callback: Callable[[WorkflowContext], None]):
        """Add callback for workflow completion."""
        self.completion_callbacks.append(callback)
    
    def add_error_callback(self, callback: Callable[[str, WorkflowContext], None]):
        """Add callback for workflow errors."""
        self.error_callbacks.append(callback)
    
    def shutdown(self):
        """Shutdown the workflow manager."""
        self.logger.info("Shutting down workflow manager")
        
        try:
            # Cancel any running workflow
            self.cancel_workflow()
            
            # Shutdown executor
            self.executor.shutdown(wait=True)
            
            self.logger.info("Workflow manager shutdown completed")
            
        except Exception as e:
            self.logger.error(f"Error during workflow manager shutdown: {e}") 
"""
Shared types and enums for the Voice Dictation Assistant core modules.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict


class ApplicationState(Enum):
    """Application state enumeration."""
    IDLE = "idle"
    RECORDING = "recording"
    PROCESSING = "processing"
    ERROR = "error"
    CONFIGURING = "configuring"


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
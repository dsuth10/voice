"""
Audio module for Voice Dictation Assistant.

This module provides audio capture and processing functionality including:
- Real-time audio streaming
- Batch recording
- Noise filtering
- Audio level monitoring
- Microphone selection and management
"""

from .capture import AudioCapture, audio_capture_context

__all__ = ['AudioCapture', 'audio_capture_context'] 
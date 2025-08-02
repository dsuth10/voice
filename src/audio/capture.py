"""
Audio Capture Module for Voice Dictation Assistant

This module provides real-time audio capture functionality with support for:
- Microphone selection and enumeration
- Streaming and batch recording modes
- Noise filtering using scipy
- Audio level monitoring and silence detection
- Configurable audio buffers and quality settings
"""

import pyaudio
import numpy as np
import scipy.signal as signal
from typing import Optional, List, Dict, Callable, Generator, Tuple
import threading
import time
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class AudioCapture:
    """
    Audio capture class with support for real-time streaming and batch recording.
    
    Features:
    - Microphone selection and enumeration
    - Streaming and batch recording modes
    - Real-time noise filtering
    - Audio level monitoring and silence detection
    - Configurable audio buffers
    - Context manager support for resource management
    """
    
    def __init__(self, 
                 sample_rate: int = 16000,
                 channels: int = 1,
                 chunk_size: int = 1024,
                 format_type: int = pyaudio.paInt16,
                 buffer_duration: float = 3.0,
                 silence_threshold: float = 0.01,
                 noise_filter_enabled: bool = True):
        """
        Initialize the AudioCapture instance.
        
        Args:
            sample_rate: Audio sample rate in Hz (default: 16000)
            channels: Number of audio channels (default: 1 for mono)
            chunk_size: Number of frames per buffer (default: 1024)
            format_type: Audio format type (default: 16-bit integer)
            buffer_duration: Duration of audio buffer in seconds (default: 3.0)
            silence_threshold: Threshold for silence detection (default: 0.01)
            noise_filter_enabled: Enable noise filtering (default: True)
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        self.format_type = format_type
        self.buffer_duration = buffer_duration
        self.silence_threshold = silence_threshold
        self.noise_filter_enabled = noise_filter_enabled
        
        # Audio processing objects
        self.pyaudio = None
        self.stream = None
        self.device_index = None
        
        # State management
        self.is_recording = False
        self.is_streaming = False
        self.audio_buffer = []
        self.buffer_lock = threading.Lock()
        
        # Noise filter parameters
        self.filter_coefficients = None
        self._setup_noise_filter()
        
        # Callbacks
        self.silence_callback = None
        self.speech_callback = None
        self.level_callback = None
        
        logger.info(f"AudioCapture initialized: {sample_rate}Hz, {channels}ch, {chunk_size} chunks")
    
    def _setup_noise_filter(self):
        """Setup noise filtering coefficients."""
        if not self.noise_filter_enabled:
            return
            
        # Design a bandpass filter for speech frequencies (80Hz - 8000Hz)
        nyquist = self.sample_rate / 2
        low_freq = 80 / nyquist
        high_freq = 8000 / nyquist
        
        # Butterworth filter for smooth frequency response
        self.filter_coefficients = signal.butter(
            N=4,  # Filter order
            Wn=[low_freq, high_freq],
            btype='band',
            output='sos'
        )
        
        logger.debug("Noise filter configured for speech frequencies")
    
    def list_microphones(self) -> List[Dict[str, any]]:
        """
        List all available microphones with their properties.
        
        Returns:
            List of dictionaries containing microphone information
        """
        if self.pyaudio is None:
            self.pyaudio = pyaudio.PyAudio()
        
        microphones = []
        
        try:
            for i in range(self.pyaudio.get_device_count()):
                device_info = self.pyaudio.get_device_info_by_index(i)
                
                # Only include input devices
                if device_info['maxInputChannels'] > 0:
                    microphones.append({
                        'index': i,
                        'name': device_info['name'],
                        'channels': device_info['maxInputChannels'],
                        'sample_rate': int(device_info['defaultSampleRate']),
                        'latency_low': device_info.get('defaultLowInputLatency', 0),
                        'latency_high': device_info.get('defaultHighInputLatency', 0)
                    })
        except Exception as e:
            logger.error(f"Error enumerating microphones: {e}")
        
        logger.info(f"Found {len(microphones)} microphone(s)")
        return microphones
    
    def select_microphone(self, device_index: Optional[int] = None, 
                         device_name: Optional[str] = None) -> bool:
        """
        Select a microphone by index or name.
        
        Args:
            device_index: Index of the microphone device
            device_name: Name of the microphone device (partial match supported)
            
        Returns:
            True if microphone was successfully selected, False otherwise
        """
        if self.pyaudio is None:
            self.pyaudio = pyaudio.PyAudio()
        
        try:
            if device_index is not None:
                # Select by index
                device_info = self.pyaudio.get_device_info_by_index(device_index)
                if device_info['maxInputChannels'] > 0:
                    self.device_index = device_index
                    logger.info(f"Selected microphone by index: {device_index} - {device_info['name']}")
                    return True
                else:
                    logger.error(f"Device {device_index} is not an input device")
                    return False
            
            elif device_name is not None:
                # Select by name (partial match)
                microphones = self.list_microphones()
                for mic in microphones:
                    if device_name.lower() in mic['name'].lower():
                        self.device_index = mic['index']
                        logger.info(f"Selected microphone by name: {mic['name']}")
                        return True
                
                logger.error(f"No microphone found matching '{device_name}'")
                return False
            
            else:
                # Use default microphone
                self.device_index = self.pyaudio.get_default_input_device_info()['index']
                logger.info("Using default microphone")
                return True
                
        except Exception as e:
            logger.error(f"Error selecting microphone: {e}")
            return False
    
    def _calculate_audio_level(self, audio_data: np.ndarray) -> float:
        """
        Calculate the RMS (Root Mean Square) level of audio data.
        
        Args:
            audio_data: Audio data as numpy array
            
        Returns:
            RMS level as float
        """
        if len(audio_data) == 0:
            return 0.0
        
        # Convert to float if needed
        if audio_data.dtype != np.float32:
            audio_data = audio_data.astype(np.float32) / 32768.0  # Normalize 16-bit
        
        # Calculate RMS
        rms = np.sqrt(np.mean(audio_data**2))
        return float(rms)
    
    def _apply_noise_filter(self, audio_data: np.ndarray) -> np.ndarray:
        """
        Apply noise filtering to audio data.
        
        Args:
            audio_data: Raw audio data
            
        Returns:
            Filtered audio data
        """
        if not self.noise_filter_enabled or self.filter_coefficients is None:
            return audio_data
        
        try:
            # Apply the bandpass filter
            filtered_data = signal.sosfilt(self.filter_coefficients, audio_data)
            return filtered_data
        except Exception as e:
            logger.warning(f"Error applying noise filter: {e}")
            return audio_data
    
    def _process_audio_chunk(self, audio_data: bytes) -> Tuple[np.ndarray, float]:
        """
        Process a chunk of audio data.
        
        Args:
            audio_data: Raw audio data as bytes
            
        Returns:
            Tuple of (processed_audio, audio_level)
        """
        # Convert bytes to numpy array
        audio_array = np.frombuffer(audio_data, dtype=np.int16)
        
        # Apply noise filtering
        filtered_audio = self._apply_noise_filter(audio_array)
        
        # Calculate audio level
        audio_level = self._calculate_audio_level(filtered_audio)
        
        # Check for silence/speech
        if audio_level < self.silence_threshold:
            if self.silence_callback:
                self.silence_callback(audio_level)
        else:
            if self.speech_callback:
                self.speech_callback(audio_level)
        
        # Level monitoring callback
        if self.level_callback:
            self.level_callback(audio_level)
        
        return filtered_audio, audio_level
    
    def start_streaming(self, 
                       callback: Optional[Callable[[np.ndarray, float], None]] = None,
                       silence_callback: Optional[Callable[[float], None]] = None,
                       speech_callback: Optional[Callable[[float], None]] = None,
                       level_callback: Optional[Callable[[float], None]] = None) -> bool:
        """
        Start real-time audio streaming.
        
        Args:
            callback: Function called with (audio_data, level) for each chunk
            silence_callback: Function called when silence is detected
            speech_callback: Function called when speech is detected
            level_callback: Function called with audio level for each chunk
            
        Returns:
            True if streaming started successfully, False otherwise
        """
        if self.is_streaming:
            logger.warning("Streaming already in progress")
            return False
        
        if self.pyaudio is None:
            self.pyaudio = pyaudio.PyAudio()
        
        # Set callbacks
        self.silence_callback = silence_callback
        self.speech_callback = speech_callback
        self.level_callback = level_callback
        
        try:
            # Select default microphone if none selected
            if self.device_index is None:
                self.select_microphone()
            
            # Open audio stream
            self.stream = self.pyaudio.open(
                format=self.format_type,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=self.device_index,
                frames_per_buffer=self.chunk_size,
                stream_callback=self._stream_callback
            )
            
            self.is_streaming = True
            self.stream.start_stream()
            
            logger.info("Audio streaming started")
            return True
            
        except Exception as e:
            logger.error(f"Error starting audio streaming: {e}")
            return False
    
    def _stream_callback(self, in_data: bytes, frame_count: int, 
                        time_info: dict, status: int) -> Tuple[bytes, int]:
        """
        Callback function for audio streaming.
        
        Args:
            in_data: Input audio data
            frame_count: Number of frames
            time_info: Timing information
            status: Status flags
            
        Returns:
            Tuple of (output_data, status)
        """
        try:
            # Process the audio chunk
            processed_audio, level = self._process_audio_chunk(in_data)
            
            # Add to buffer
            with self.buffer_lock:
                self.audio_buffer.append(processed_audio)
                
                # Maintain buffer size
                max_chunks = int(self.buffer_duration * self.sample_rate / self.chunk_size)
                if len(self.audio_buffer) > max_chunks:
                    self.audio_buffer.pop(0)
            
            # Call user callback if provided
            if hasattr(self, '_user_callback') and self._user_callback:
                self._user_callback(processed_audio, level)
            
        except Exception as e:
            logger.error(f"Error in stream callback: {e}")
        
        return (in_data, pyaudio.paContinue)
    
    def stop_streaming(self):
        """Stop audio streaming."""
        if not self.is_streaming:
            return
        
        try:
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
                self.stream = None
            
            self.is_streaming = False
            logger.info("Audio streaming stopped")
            
        except Exception as e:
            logger.error(f"Error stopping audio streaming: {e}")
    
    def record_batch(self, duration: float) -> Optional[np.ndarray]:
        """
        Record audio for a specified duration.
        
        Args:
            duration: Recording duration in seconds
            
        Returns:
            Recorded audio data as numpy array, or None if recording failed
        """
        if self.is_recording:
            logger.warning("Recording already in progress")
            return None
        
        if self.pyaudio is None:
            self.pyaudio = pyaudio.PyAudio()
        
        try:
            # Select default microphone if none selected
            if self.device_index is None:
                self.select_microphone()
            
            # Calculate number of chunks needed
            num_chunks = int(duration * self.sample_rate / self.chunk_size)
            
            # Open audio stream
            stream = self.pyaudio.open(
                format=self.format_type,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=self.device_index,
                frames_per_buffer=self.chunk_size
            )
            
            self.is_recording = True
            logger.info(f"Starting batch recording for {duration} seconds")
            
            # Record audio
            frames = []
            for _ in range(num_chunks):
                data = stream.read(self.chunk_size)
                frames.append(data)
            
            # Stop recording
            stream.stop_stream()
            stream.close()
            self.is_recording = False
            
            # Combine all frames
            audio_data = b''.join(frames)
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            
            # Apply noise filtering
            filtered_audio = self._apply_noise_filter(audio_array)
            
            logger.info(f"Batch recording completed: {len(filtered_audio)} samples")
            return filtered_audio
            
        except Exception as e:
            logger.error(f"Error during batch recording: {e}")
            self.is_recording = False
            return None
    
    def get_audio_buffer(self) -> np.ndarray:
        """
        Get the current audio buffer as a single numpy array.
        
        Returns:
            Audio buffer as numpy array
        """
        with self.buffer_lock:
            if not self.audio_buffer:
                return np.array([], dtype=np.int16)
            
            # Concatenate all chunks
            return np.concatenate(self.audio_buffer)
    
    def clear_audio_buffer(self):
        """Clear the audio buffer."""
        with self.buffer_lock:
            self.audio_buffer.clear()
            logger.debug("Audio buffer cleared")
    
    def get_audio_level(self) -> float:
        """
        Get the current audio level from the buffer.
        
        Returns:
            Current audio level as float
        """
        audio_data = self.get_audio_buffer()
        return self._calculate_audio_level(audio_data)
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with resource cleanup."""
        try:
            self.stop_streaming()
            
            if self.stream:
                self.stream.close()
                self.stream = None
            
            if self.pyaudio:
                self.pyaudio.terminate()
                self.pyaudio = None
            
            logger.info("AudioCapture resources cleaned up")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


@contextmanager
def audio_capture_context(**kwargs):
    """
    Context manager for AudioCapture with automatic resource management.
    
    Args:
        **kwargs: Arguments to pass to AudioCapture constructor
        
    Yields:
        AudioCapture instance
    """
    capture = AudioCapture(**kwargs)
    try:
        yield capture
    finally:
        capture.__exit__(None, None, None) 
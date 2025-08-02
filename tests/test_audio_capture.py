"""
Unit tests for AudioCapture module.

Tests cover:
- Audio capture initialization and configuration
- Microphone enumeration and selection
- Streaming and batch recording modes
- Noise filtering functionality
- Audio level monitoring and silence detection
- Error handling and resource management
- Context manager behavior
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import numpy as np
import pyaudio
import tempfile
import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from audio.capture import AudioCapture, audio_capture_context


class TestAudioCapture(unittest.TestCase):
    """Test cases for AudioCapture class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock PyAudio to avoid actual hardware access
        self.pyaudio_patcher = patch('audio.capture.pyaudio')
        self.mock_pyaudio = self.pyaudio_patcher.start()
        
        # Create mock PyAudio instance
        self.mock_pyaudio_instance = Mock()
        self.mock_pyaudio.PyAudio.return_value = self.mock_pyaudio_instance
        
        # Mock device info
        self.mock_device_info = {
            'index': 0,
            'name': 'Test Microphone',
            'maxInputChannels': 1,
            'defaultSampleRate': 16000,
            'defaultLowInputLatency': 0.01,
            'defaultHighInputLatency': 0.1
        }
        
        self.mock_pyaudio_instance.get_device_info_by_index.return_value = self.mock_device_info
        self.mock_pyaudio_instance.get_device_count.return_value = 1
        self.mock_pyaudio_instance.get_default_input_device_info.return_value = self.mock_device_info
        
        # Mock audio stream
        self.mock_stream = Mock()
        self.mock_pyaudio_instance.open.return_value = self.mock_stream
        
    def tearDown(self):
        """Clean up after tests."""
        self.pyaudio_patcher.stop()
    
    def test_initialization(self):
        """Test AudioCapture initialization with default parameters."""
        capture = AudioCapture()
        
        self.assertEqual(capture.sample_rate, 16000)
        self.assertEqual(capture.channels, 1)
        self.assertEqual(capture.chunk_size, 1024)
        self.assertEqual(capture.format_type, pyaudio.paInt16)
        self.assertEqual(capture.buffer_duration, 3.0)
        self.assertEqual(capture.silence_threshold, 0.01)
        self.assertTrue(capture.noise_filter_enabled)
        self.assertFalse(capture.is_recording)
        self.assertFalse(capture.is_streaming)
    
    def test_initialization_custom_params(self):
        """Test AudioCapture initialization with custom parameters."""
        capture = AudioCapture(
            sample_rate=44100,
            channels=2,
            chunk_size=2048,
            buffer_duration=5.0,
            silence_threshold=0.05,
            noise_filter_enabled=False
        )
        
        self.assertEqual(capture.sample_rate, 44100)
        self.assertEqual(capture.channels, 2)
        self.assertEqual(capture.chunk_size, 2048)
        self.assertEqual(capture.buffer_duration, 5.0)
        self.assertEqual(capture.silence_threshold, 0.05)
        self.assertFalse(capture.noise_filter_enabled)
    
    def test_list_microphones(self):
        """Test microphone enumeration."""
        # Mock multiple devices
        self.mock_pyaudio_instance.get_device_count.return_value = 3
        
        device_infos = [
            {'index': 0, 'name': 'Mic 1', 'maxInputChannels': 1, 'defaultSampleRate': 16000},
            {'index': 1, 'name': 'Mic 2', 'maxInputChannels': 0, 'defaultSampleRate': 16000},  # Output device
            {'index': 2, 'name': 'Mic 3', 'maxInputChannels': 2, 'defaultSampleRate': 48000}
        ]
        
        self.mock_pyaudio_instance.get_device_info_by_index.side_effect = device_infos
        
        capture = AudioCapture()
        microphones = capture.list_microphones()
        
        self.assertEqual(len(microphones), 2)  # Only input devices
        self.assertEqual(microphones[0]['name'], 'Mic 1')
        self.assertEqual(microphones[1]['name'], 'Mic 3')
        self.assertEqual(microphones[1]['channels'], 2)
    
    def test_select_microphone_by_index(self):
        """Test microphone selection by index."""
        capture = AudioCapture()
        
        # Test successful selection
        result = capture.select_microphone(device_index=0)
        self.assertTrue(result)
        self.assertEqual(capture.device_index, 0)
        
        # Test invalid device
        self.mock_pyaudio_instance.get_device_info_by_index.return_value = {
            'maxInputChannels': 0  # Output device
        }
        result = capture.select_microphone(device_index=1)
        self.assertFalse(result)
    
    def test_select_microphone_by_name(self):
        """Test microphone selection by name."""
        # Mock multiple devices
        self.mock_pyaudio_instance.get_device_count.return_value = 2
        device_infos = [
            {'index': 0, 'name': 'USB Microphone', 'maxInputChannels': 1, 'defaultSampleRate': 16000},
            {'index': 1, 'name': 'Built-in Microphone', 'maxInputChannels': 1, 'defaultSampleRate': 16000}
        ]
        self.mock_pyaudio_instance.get_device_info_by_index.side_effect = device_infos
        
        capture = AudioCapture()
        
        # Test successful selection
        result = capture.select_microphone(device_name='USB')
        self.assertTrue(result)
        self.assertEqual(capture.device_index, 0)
        
        # Test no match
        result = capture.select_microphone(device_name='Nonexistent')
        self.assertFalse(result)
    
    def test_select_default_microphone(self):
        """Test default microphone selection."""
        capture = AudioCapture()
        
        result = capture.select_microphone()
        self.assertTrue(result)
        self.assertEqual(capture.device_index, 0)
    
    def test_calculate_audio_level(self):
        """Test audio level calculation."""
        capture = AudioCapture()
        
        # Test with silence
        silence_data = np.zeros(1024, dtype=np.int16)
        level = capture._calculate_audio_level(silence_data)
        self.assertEqual(level, 0.0)
        
        # Test with audio data
        audio_data = np.random.randint(-1000, 1000, 1024, dtype=np.int16)
        level = capture._calculate_audio_level(audio_data)
        self.assertGreater(level, 0.0)
        self.assertLessEqual(level, 1.0)
    
    def test_noise_filter_setup(self):
        """Test noise filter setup."""
        capture = AudioCapture(noise_filter_enabled=True)
        self.assertIsNotNone(capture.filter_coefficients)
        
        capture = AudioCapture(noise_filter_enabled=False)
        self.assertIsNone(capture.filter_coefficients)
    
    def test_apply_noise_filter(self):
        """Test noise filtering functionality."""
        capture = AudioCapture(noise_filter_enabled=True)
        
        # Create test audio data
        audio_data = np.random.randint(-1000, 1000, 1024, dtype=np.int16)
        
        # Test filtering
        filtered_data = capture._apply_noise_filter(audio_data)
        self.assertEqual(len(filtered_data), len(audio_data))
        self.assertIsInstance(filtered_data, np.ndarray)
        
        # Test with disabled filter
        capture.noise_filter_enabled = False
        unfiltered_data = capture._apply_noise_filter(audio_data)
        np.testing.assert_array_equal(unfiltered_data, audio_data)
    
    def test_process_audio_chunk(self):
        """Test audio chunk processing."""
        capture = AudioCapture()
        
        # Mock callbacks
        silence_called = []
        speech_called = []
        level_called = []
        
        def silence_callback(level):
            silence_called.append(level)
        
        def speech_callback(level):
            speech_called.append(level)
        
        def level_callback(level):
            level_called.append(level)
        
        capture.silence_callback = silence_callback
        capture.speech_callback = speech_callback
        capture.level_callback = level_callback
        
        # Test with silence
        silence_data = np.zeros(1024, dtype=np.int16).tobytes()
        processed_audio, level = capture._process_audio_chunk(silence_data)
        
        self.assertEqual(level, 0.0)
        self.assertEqual(len(silence_called), 1)
        self.assertEqual(len(speech_called), 0)
        self.assertEqual(len(level_called), 1)
        
        # Test with audio
        audio_data = np.random.randint(-1000, 1000, 1024, dtype=np.int16).tobytes()
        processed_audio, level = capture._process_audio_chunk(audio_data)
        
        self.assertGreater(level, 0.0)
        self.assertEqual(len(speech_called), 1)
        self.assertEqual(len(level_called), 2)
    
    def test_start_streaming(self):
        """Test audio streaming start."""
        capture = AudioCapture()
        
        # Mock callbacks
        callback_called = []
        def test_callback(audio_data, level):
            callback_called.append((audio_data, level))
        
        # Test successful start
        result = capture.start_streaming(callback=test_callback)
        self.assertTrue(result)
        self.assertTrue(capture.is_streaming)
        
        # Test already streaming
        result = capture.start_streaming()
        self.assertFalse(result)
    
    def test_stop_streaming(self):
        """Test audio streaming stop."""
        capture = AudioCapture()
        
        # Start streaming first
        capture.start_streaming()
        self.assertTrue(capture.is_streaming)
        
        # Stop streaming
        capture.stop_streaming()
        self.assertFalse(capture.is_streaming)
        
        # Test stopping when not streaming
        capture.stop_streaming()  # Should not raise error
    
    def test_record_batch(self):
        """Test batch recording."""
        capture = AudioCapture()
        
        # Mock stream read
        test_audio = np.random.randint(-1000, 1000, 1024, dtype=np.int16).tobytes()
        self.mock_stream.read.return_value = test_audio
        
        # Test successful recording
        audio_data = capture.record_batch(duration=0.1)  # Short duration for testing
        
        self.assertIsNotNone(audio_data)
        self.assertIsInstance(audio_data, np.ndarray)
        self.assertGreater(len(audio_data), 0)
        
        # Test already recording
        result = capture.record_batch(duration=0.1)
        self.assertIsNone(result)
    
    def test_audio_buffer_operations(self):
        """Test audio buffer operations."""
        capture = AudioCapture()
        
        # Test empty buffer
        buffer_data = capture.get_audio_buffer()
        self.assertEqual(len(buffer_data), 0)
        
        # Test buffer level
        level = capture.get_audio_level()
        self.assertEqual(level, 0.0)
        
        # Test buffer clearing
        capture.clear_audio_buffer()
        buffer_data = capture.get_audio_buffer()
        self.assertEqual(len(buffer_data), 0)
    
    def test_context_manager(self):
        """Test context manager functionality."""
        with AudioCapture() as capture:
            self.assertIsInstance(capture, AudioCapture)
            # Context should be active
        
        # Context should be cleaned up
        self.assertIsNone(capture.pyaudio)
    
    def test_audio_capture_context(self):
        """Test audio_capture_context function."""
        with audio_capture_context(sample_rate=44100) as capture:
            self.assertEqual(capture.sample_rate, 44100)
            self.assertIsInstance(capture, AudioCapture)
    
    def test_error_handling(self):
        """Test error handling scenarios."""
        # Test PyAudio initialization error
        self.mock_pyaudio.PyAudio.side_effect = Exception("PyAudio error")
        
        with self.assertRaises(Exception):
            AudioCapture()
        
        # Reset mock
        self.mock_pyaudio.PyAudio.side_effect = None
        
        # Test stream creation error
        capture = AudioCapture()
        self.mock_pyaudio_instance.open.side_effect = Exception("Stream error")
        
        result = capture.start_streaming()
        self.assertFalse(result)
    
    def test_resource_cleanup(self):
        """Test proper resource cleanup."""
        capture = AudioCapture()
        
        # Start streaming
        capture.start_streaming()
        
        # Cleanup
        capture.__exit__(None, None, None)
        
        # Verify cleanup
        self.assertIsNone(capture.stream)
        self.assertIsNone(capture.pyaudio)
        self.assertFalse(capture.is_streaming)


class TestAudioCaptureIntegration(unittest.TestCase):
    """Integration tests for AudioCapture with real hardware (if available)."""
    
    @unittest.skip("Requires real microphone hardware")
    def test_real_microphone_access(self):
        """Test with real microphone hardware."""
        # This test requires actual hardware and should be run separately
        capture = AudioCapture()
        
        # List available microphones
        microphones = capture.list_microphones()
        self.assertGreater(len(microphones), 0)
        
        # Test default microphone selection
        result = capture.select_microphone()
        self.assertTrue(result)
        
        # Test short recording
        audio_data = capture.record_batch(duration=0.5)
        self.assertIsNotNone(audio_data)
        self.assertGreater(len(audio_data), 0)


if __name__ == '__main__':
    unittest.main() 
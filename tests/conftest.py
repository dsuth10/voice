"""
Pytest configuration and fixtures for Voice Dictation Assistant tests.
"""
import pytest
import tempfile
import os
import sys
from unittest.mock import MagicMock, patch
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

@pytest.fixture
def temp_config_dir():
    """Create a temporary directory for configuration files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir

@pytest.fixture
def mock_audio_data():
    """Generate mock audio data for testing."""
    import numpy as np
    # Generate 1 second of 16kHz audio data
    sample_rate = 16000
    duration = 1.0
    samples = int(sample_rate * duration)
    # Generate random audio data
    audio_data = np.random.randn(samples).astype(np.float32)
    return audio_data.tobytes()

@pytest.fixture
def mock_transcription_result():
    """Mock transcription result for testing."""
    return {
        "text": "This is a test transcription.",
        "confidence": 0.95,
        "words": [
            {"text": "This", "start": 0.0, "end": 0.3, "confidence": 0.98},
            {"text": "is", "start": 0.3, "end": 0.5, "confidence": 0.95},
            {"text": "a", "start": 0.5, "end": 0.6, "confidence": 0.92},
            {"text": "test", "start": 0.6, "end": 0.9, "confidence": 0.94},
            {"text": "transcription.", "start": 0.9, "end": 1.2, "confidence": 0.96}
        ]
    }

@pytest.fixture
def mock_enhanced_text():
    """Mock enhanced text result for testing."""
    return {
        "original": "this is a test transcription",
        "enhanced": "This is a test transcription.",
        "changes": [
            {"type": "capitalization", "position": 0, "original": "this", "enhanced": "This"},
            {"type": "punctuation", "position": 24, "original": "", "enhanced": "."}
        ]
    }

@pytest.fixture
def mock_windows_api():
    """Mock Windows API calls for testing."""
    with patch('win32gui.GetForegroundWindow') as mock_foreground, \
         patch('win32gui.GetWindowText') as mock_window_text, \
         patch('win32gui.GetWindowRect') as mock_window_rect, \
         patch('win32api.GetCursorPos') as mock_cursor_pos:
        
        # Mock window information
        mock_foreground.return_value = 12345
        mock_window_text.return_value = "Test Application"
        mock_window_rect.return_value = (100, 100, 800, 600)
        mock_cursor_pos.return_value = (400, 300)
        
        yield {
            'foreground': mock_foreground,
            'window_text': mock_window_text,
            'window_rect': mock_window_rect,
            'cursor_pos': mock_cursor_pos
        }

@pytest.fixture
def mock_pyaudio():
    """Mock PyAudio for testing."""
    with patch('pyaudio.PyAudio') as mock_pa:
        mock_stream = MagicMock()
        mock_pa.return_value.open.return_value = mock_stream
        mock_pa.return_value.get_device_count.return_value = 2
        mock_pa.return_value.get_device_info_by_index.side_effect = [
            {'name': 'Microphone 1', 'maxInputChannels': 1},
            {'name': 'Microphone 2', 'maxInputChannels': 2}
        ]
        yield mock_pa

@pytest.fixture
def mock_openai_api():
    """Mock OpenAI API for testing."""
    with patch('openai.ChatCompletion.create') as mock_create:
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "This is enhanced text."
        mock_create.return_value = mock_response
        yield mock_create

@pytest.fixture
def mock_assemblyai_api():
    """Mock AssemblyAI API for testing."""
    with patch('assemblyai.Transcriber') as mock_transcriber:
        mock_transcriber_instance = MagicMock()
        mock_transcriber.return_value = mock_transcriber_instance
        
        # Mock transcription result
        mock_result = MagicMock()
        mock_result.text = "This is a test transcription."
        mock_result.confidence = 0.95
        mock_result.words = [
            MagicMock(text="This", start=0.0, end=0.3, confidence=0.98),
            MagicMock(text="is", start=0.3, end=0.5, confidence=0.95),
            MagicMock(text="a", start=0.5, end=0.6, confidence=0.92),
            MagicMock(text="test", start=0.6, end=0.9, confidence=0.94),
            MagicMock(text="transcription.", start=0.9, end=1.2, confidence=0.96)
        ]
        
        mock_transcriber_instance.transcribe.return_value = mock_result
        yield mock_transcriber

@pytest.fixture
def test_config():
    """Test configuration for the application."""
    return {
        "audio": {
            "sample_rate": 16000,
            "channels": 1,
            "chunk_size": 1024,
            "format": "int16"
        },
        "api_keys": {
            "openai": "test_openai_key",
            "assemblyai": "test_assemblyai_key"
        },
        "hotkeys": {
            "start_recording": "ctrl+shift+v",
            "stop_recording": "ctrl+shift+v"
        },
        "enhancement": {
            "enable_grammar_correction": True,
            "enable_punctuation": True,
            "enable_capitalization": True
        }
    }

@pytest.fixture
def mock_logger():
    """Mock logger for testing."""
    with patch('src.utils.logger.logger') as mock_log:
        yield mock_log

@pytest.fixture
def performance_thresholds():
    """Performance thresholds for testing."""
    return {
        "max_response_time": 5.0,  # seconds
        "max_memory_usage": 100,   # MB
        "max_cpu_usage": 50,       # percent
        "min_accuracy": 0.85       # transcription accuracy
    }

# Mark tests that require Windows
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "windows: mark test as Windows-specific"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as performance test"
    )

def pytest_collection_modifyitems(config, items):
    """Modify test collection to handle platform-specific tests."""
    skip_windows = pytest.mark.skip(reason="Test requires Windows")
    skip_slow = pytest.mark.skip(reason="Test is slow, run with --runslow")
    
    for item in items:
        # Skip Windows-specific tests on non-Windows platforms
        if "windows" in item.keywords and not os.name == "nt":
            item.add_marker(skip_windows)
        
        # Skip slow tests unless --runslow is specified
        if "slow" in item.keywords and not config.getoption("--runslow"):
            item.add_marker(skip_slow)

def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--runslow", action="store_true", default=False, help="run slow tests"
    )
    parser.addoption(
        "--runperformance", action="store_true", default=False, help="run performance tests"
    ) 
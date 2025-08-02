"""
Tests for the SpeechRecognition module.

This module contains comprehensive tests for the SpeechRecognition class,
covering all functionality including error handling, caching, and confidence scoring.
"""

import pytest
import asyncio
import tempfile
import os
from unittest.mock import Mock, patch, AsyncMock
import numpy as np

from src.recognition.speech_recognition import (
    SpeechRecognition,
    SpeechRecognitionError,
    ServiceType,
    TranscriptionResult,
    RetryableError,
    NonRetryableError
)


class TestSpeechRecognition:
    """Test cases for the SpeechRecognition class."""
    
    @pytest.fixture
    def mock_assemblyai_client(self):
        """Mock AssemblyAI client."""
        mock_client = Mock()
        mock_transcript = Mock()
        mock_transcript.status = "completed"
        mock_transcript.text = "Hello world"
        mock_transcript.confidence = 0.95
        mock_transcript.language_code = "en"
        mock_client.transcribe.return_value = mock_transcript
        return mock_client
    
    @pytest.fixture
    def mock_openai_client(self):
        """Mock OpenAI client."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = "Hello world"
        mock_response.language = "en"
        mock_client.audio.transcriptions.create.return_value = mock_response
        return mock_client
    
    @pytest.fixture
    def sample_audio_data(self):
        """Generate sample audio data for testing."""
        # Generate 1 second of 16kHz audio data
        sample_rate = 16000
        duration = 1.0
        samples = int(sample_rate * duration)
        audio_data = np.random.randint(-32768, 32767, samples, dtype=np.int16)
        return audio_data.tobytes()
    
    def test_initialization_with_assemblyai(self, mock_assemblyai_client):
        """Test initialization with AssemblyAI service."""
        with patch('assemblyai.Client', return_value=mock_assemblyai_client):
            recognizer = SpeechRecognition(
                assemblyai_api_key="test_key",
                service=ServiceType.ASSEMBLYAI
            )
        
        assert recognizer.service == ServiceType.ASSEMBLYAI
        assert recognizer.assemblyai_client is not None
        assert recognizer.openai_client is None
    
    def test_initialization_with_whisper(self, mock_openai_client):
        """Test initialization with OpenAI Whisper service."""
        with patch('openai.OpenAI', return_value=mock_openai_client):
            recognizer = SpeechRecognition(
                openai_api_key="test_key",
                service=ServiceType.WHISPER
            )
        
        assert recognizer.service == ServiceType.WHISPER
        assert recognizer.openai_client is not None
        assert recognizer.assemblyai_client is None
    
    def test_initialization_with_fallback(self, mock_assemblyai_client, mock_openai_client):
        """Test initialization with fallback enabled."""
        with patch('assemblyai.Client', return_value=mock_assemblyai_client), \
             patch('openai.OpenAI', return_value=mock_openai_client):
            recognizer = SpeechRecognition(
                assemblyai_api_key="test_key",
                openai_api_key="test_key",
                fallback=True
            )
        
        assert recognizer.fallback is True
        assert recognizer.assemblyai_client is not None
        assert recognizer.openai_client is not None
    
    def test_initialization_no_services(self):
        """Test initialization with no available services."""
        with pytest.raises(SpeechRecognitionError, match="No speech recognition services available"):
            SpeechRecognition()
    
    def test_custom_vocabulary_management(self, mock_assemblyai_client):
        """Test custom vocabulary management."""
        with patch('assemblyai.Client', return_value=mock_assemblyai_client):
            recognizer = SpeechRecognition(
                assemblyai_api_key="test_key",
                custom_vocabulary=["test", "example"]
            )
        
        assert len(recognizer.custom_vocabulary) == 2
        assert "test" in recognizer.custom_vocabulary
        assert "example" in recognizer.custom_vocabulary
        
        # Test adding vocabulary
        recognizer.add_custom_vocabulary(["new", "terms"])
        assert len(recognizer.custom_vocabulary) == 4
        assert "new" in recognizer.custom_vocabulary
        
        # Test removing vocabulary
        recognizer.remove_custom_vocabulary(["test"])
        assert len(recognizer.custom_vocabulary) == 3
        assert "test" not in recognizer.custom_vocabulary
        
        # Test clearing vocabulary
        recognizer.clear_custom_vocabulary()
        assert len(recognizer.custom_vocabulary) == 0
    
    def test_cache_management(self, mock_assemblyai_client):
        """Test cache management functionality."""
        with patch('assemblyai.Client', return_value=mock_assemblyai_client):
            recognizer = SpeechRecognition(
                assemblyai_api_key="test_key",
                cache_size=2
            )
        
        # Test cache stats
        stats = recognizer.get_cache_stats()
        assert stats["size"] == 0
        assert stats["max_size"] == 2
        
        # Test cache info
        info = recognizer.get_cache_info()
        assert info["size"] == 0
        assert info["max_size"] == 2
        assert info["custom_vocabulary_size"] == 0
        
        # Test cache resize
        recognizer.resize_cache(5)
        assert recognizer.cache_size == 5
        
        # Test cache clear
        recognizer.clear_cache()
        assert len(recognizer._cache) == 0
    
    def test_confidence_analysis(self, mock_assemblyai_client):
        """Test confidence analysis functionality."""
        with patch('assemblyai.Client', return_value=mock_assemblyai_client):
            recognizer = SpeechRecognition(assemblyai_api_key="test_key")
        
        # Test with high confidence result
        high_conf_result = TranscriptionResult(
            text="Hello world",
            confidence=0.95,
            service=ServiceType.ASSEMBLYAI
        )
        
        analysis = recognizer.analyze_confidence(high_conf_result)
        assert analysis["confidence_score"] == 0.95
        assert analysis["confidence_level"] == "excellent"
        assert analysis["is_high_confidence"] is True
        assert analysis["is_acceptable"] is True
        
        # Test with low confidence result
        low_conf_result = TranscriptionResult(
            text="Hello world",
            confidence=0.3,
            service=ServiceType.ASSEMBLYAI
        )
        
        analysis = recognizer.analyze_confidence(low_conf_result)
        assert analysis["confidence_score"] == 0.3
        assert analysis["confidence_level"] == "poor"
        assert analysis["is_high_confidence"] is False
        assert analysis["is_acceptable"] is False
    
    def test_confidence_filtering(self, mock_assemblyai_client):
        """Test confidence filtering functionality."""
        with patch('assemblyai.Client', return_value=mock_assemblyai_client):
            recognizer = SpeechRecognition(assemblyai_api_key="test_key")
        
        results = [
            TranscriptionResult("text1", 0.9, ServiceType.ASSEMBLYAI),
            TranscriptionResult("text2", 0.7, ServiceType.ASSEMBLYAI),
            TranscriptionResult("text3", 0.3, ServiceType.ASSEMBLYAI),
            TranscriptionResult("text4", 0.8, ServiceType.ASSEMBLYAI)
        ]
        
        # Test filtering by confidence
        filtered = recognizer.filter_by_confidence(results, min_confidence=0.7)
        assert len(filtered) == 3
        assert all(r.confidence >= 0.7 for r in filtered)
        
        # Test confidence statistics
        stats = recognizer.get_confidence_statistics(results)
        assert stats["count"] == 4
        assert stats["average_confidence"] == 0.675
        assert stats["min_confidence"] == 0.3
        assert stats["max_confidence"] == 0.9
        assert stats["high_confidence_count"] == 2
        assert stats["acceptable_count"] == 3
    
    def test_service_availability(self, mock_assemblyai_client, mock_openai_client):
        """Test service availability checking."""
        with patch('assemblyai.Client', return_value=mock_assemblyai_client), \
             patch('openai.OpenAI', return_value=mock_openai_client):
            recognizer = SpeechRecognition(
                assemblyai_api_key="test_key",
                openai_api_key="test_key"
            )
        
        assert recognizer.is_service_available(ServiceType.ASSEMBLYAI) is True
        assert recognizer.is_service_available(ServiceType.WHISPER) is True
        
        # Test with only one service
        recognizer.openai_client = None
        assert recognizer.is_service_available(ServiceType.ASSEMBLYAI) is True
        assert recognizer.is_service_available(ServiceType.WHISPER) is False
    
    def test_service_switching(self, mock_assemblyai_client, mock_openai_client):
        """Test service switching functionality."""
        with patch('assemblyai.Client', return_value=mock_assemblyai_client), \
             patch('openai.OpenAI', return_value=mock_openai_client):
            recognizer = SpeechRecognition(
                assemblyai_api_key="test_key",
                openai_api_key="test_key"
            )
        
        # Test switching to Whisper
        assert recognizer.switch_service(ServiceType.WHISPER) is True
        assert recognizer.service == ServiceType.WHISPER
        
        # Test switching to AssemblyAI
        assert recognizer.switch_service(ServiceType.ASSEMBLYAI) is True
        assert recognizer.service == ServiceType.ASSEMBLYAI
        
        # Test switching to unavailable service
        recognizer.openai_client = None
        assert recognizer.switch_service(ServiceType.WHISPER) is False
    
    def test_get_available_services(self, mock_assemblyai_client, mock_openai_client):
        """Test getting available services."""
        with patch('assemblyai.Client', return_value=mock_assemblyai_client), \
             patch('openai.OpenAI', return_value=mock_openai_client):
            recognizer = SpeechRecognition(
                assemblyai_api_key="test_key",
                openai_api_key="test_key"
            )
        
        available = recognizer.get_available_services()
        assert ServiceType.ASSEMBLYAI in available
        assert ServiceType.WHISPER in available
        assert len(available) == 2
        
        # Test with only one service
        recognizer.openai_client = None
        available = recognizer.get_available_services()
        assert ServiceType.ASSEMBLYAI in available
        assert ServiceType.WHISPER not in available
        assert len(available) == 1
    
    @pytest.mark.asyncio
    async def test_transcribe_assemblyai_success(self, mock_assemblyai_client, sample_audio_data):
        """Test successful AssemblyAI transcription."""
        with patch('assemblyai.Client', return_value=mock_assemblyai_client):
            recognizer = SpeechRecognition(assemblyai_api_key="test_key")
            
            result = await recognizer._transcribe_assemblyai_stream(sample_audio_data)
            
            assert result.text == "Hello world"
            assert result.confidence == 0.95
            assert result.service == ServiceType.ASSEMBLYAI
            assert result.language == "en"
            assert result.is_final is True
    
    @pytest.mark.asyncio
    async def test_transcribe_whisper_success(self, mock_openai_client, sample_audio_data):
        """Test successful Whisper transcription."""
        with patch('openai.OpenAI', return_value=mock_openai_client):
            recognizer = SpeechRecognition(openai_api_key="test_key")
            
            result = await recognizer._transcribe_whisper(sample_audio_data)
            
            assert result.text == "Hello world"
            assert result.confidence == 0.8  # Default confidence for Whisper
            assert result.service == ServiceType.WHISPER
            assert result.language == "en"
            assert result.is_final is True
    
    @pytest.mark.asyncio
    async def test_transcribe_stream_with_cache(self, mock_assemblyai_client, sample_audio_data):
        """Test transcription with caching."""
        with patch('assemblyai.Client', return_value=mock_assemblyai_client):
            recognizer = SpeechRecognition(assemblyai_api_key="test_key")
            
            # First transcription
            result1 = await recognizer.transcribe_stream(sample_audio_data)
            assert result1.text == "Hello world"
            
            # Second transcription (should use cache)
            result2 = await recognizer.transcribe_stream(sample_audio_data)
            assert result2.text == "Hello world"
            assert result1.text == result2.text
    
    @pytest.mark.asyncio
    async def test_transcribe_stream_with_fallback(self, sample_audio_data):
        """Test transcription with fallback mechanism."""
        # Mock AssemblyAI failure
        mock_assemblyai_client = Mock()
        mock_assemblyai_client.transcribe.side_effect = Exception("AssemblyAI failed")
        
        # Mock OpenAI success
        mock_openai_client = Mock()
        mock_response = Mock()
        mock_response.text = "Hello world"
        mock_response.language = "en"
        mock_openai_client.audio.transcriptions.create.return_value = mock_response
        
        with patch('assemblyai.Client', return_value=mock_assemblyai_client), \
             patch('openai.OpenAI', return_value=mock_openai_client):
            recognizer = SpeechRecognition(
                assemblyai_api_key="test_key",
                openai_api_key="test_key",
                service=ServiceType.ASSEMBLYAI,
                fallback=True
            )
            
            result = await recognizer.transcribe_stream(sample_audio_data)
            
            assert result.text == "Hello world"
            assert result.service == ServiceType.WHISPER  # Should use fallback
    
    @pytest.mark.asyncio
    async def test_transcribe_stream_force_service(self, mock_assemblyai_client, sample_audio_data):
        """Test transcription with forced service selection."""
        with patch('assemblyai.Client', return_value=mock_assemblyai_client):
            recognizer = SpeechRecognition(
                assemblyai_api_key="test_key",
                service=ServiceType.ASSEMBLYAI
            )
            
            # Force use of AssemblyAI
            result = await recognizer.transcribe_stream(
                sample_audio_data,
                force_service=ServiceType.ASSEMBLYAI
            )
            
            assert result.service == ServiceType.ASSEMBLYAI
    
    def test_error_classification(self, mock_assemblyai_client):
        """Test error classification functionality."""
        with patch('assemblyai.Client', return_value=mock_assemblyai_client):
            recognizer = SpeechRecognition(assemblyai_api_key="test_key")
        
        # Test retryable errors
        connection_error = ConnectionError("Network error")
        assert recognizer._classify_error(connection_error) == RetryableError
        
        timeout_error = TimeoutError("Request timeout")
        assert recognizer._classify_error(timeout_error) == RetryableError
        
        # Test non-retryable errors
        auth_error = Mock()
        auth_error.status_code = 401
        assert recognizer._classify_error(auth_error) == NonRetryableError
        
        invalid_error = Mock()
        invalid_error.status_code = 400
        assert recognizer._classify_error(invalid_error) == NonRetryableError
    
    def test_confidence_threshold_setting(self, mock_assemblyai_client):
        """Test confidence threshold setting."""
        with patch('assemblyai.Client', return_value=mock_assemblyai_client):
            recognizer = SpeechRecognition(assemblyai_api_key="test_key")
        
        # Test valid threshold
        recognizer.set_confidence_threshold(0.8)
        assert recognizer.confidence_threshold == 0.8
        
        # Test invalid threshold
        with pytest.raises(ValueError, match="Confidence threshold must be between 0.0 and 1.0"):
            recognizer.set_confidence_threshold(1.5)
        
        with pytest.raises(ValueError, match="Confidence threshold must be between 0.0 and 1.0"):
            recognizer.set_confidence_threshold(-0.1)


class TestTranscriptionResult:
    """Test cases for the TranscriptionResult class."""
    
    def test_confidence_levels(self):
        """Test confidence level determination."""
        # Test excellent confidence
        result = TranscriptionResult("text", 0.95, ServiceType.ASSEMBLYAI)
        assert result.get_confidence_level() == "excellent"
        assert result.is_high_confidence() is True
        assert result.is_acceptable_confidence() is True
        
        # Test good confidence
        result = TranscriptionResult("text", 0.85, ServiceType.ASSEMBLYAI)
        assert result.get_confidence_level() == "good"
        assert result.is_high_confidence() is True
        assert result.is_acceptable_confidence() is True
        
        # Test fair confidence
        result = TranscriptionResult("text", 0.7, ServiceType.ASSEMBLYAI)
        assert result.get_confidence_level() == "fair"
        assert result.is_high_confidence() is False
        assert result.is_acceptable_confidence() is True
        
        # Test poor confidence
        result = TranscriptionResult("text", 0.4, ServiceType.ASSEMBLYAI)
        assert result.get_confidence_level() == "poor"
        assert result.is_high_confidence() is False
        assert result.is_acceptable_confidence() is False
        
        # Test very poor confidence
        result = TranscriptionResult("text", 0.2, ServiceType.ASSEMBLYAI)
        assert result.get_confidence_level() == "very_poor"
        assert result.is_high_confidence() is False
        assert result.is_acceptable_confidence() is False
    
    def test_custom_confidence_thresholds(self):
        """Test custom confidence thresholds."""
        result = TranscriptionResult("text", 0.7, ServiceType.ASSEMBLYAI)
        
        # Test with custom high confidence threshold
        assert result.is_high_confidence(threshold=0.6) is True
        assert result.is_high_confidence(threshold=0.8) is False
        
        # Test with custom acceptable confidence threshold
        assert result.is_acceptable_confidence(threshold=0.6) is True
        assert result.is_acceptable_confidence(threshold=0.8) is False


class TestSpeechRecognitionIntegration:
    """Integration tests for SpeechRecognition."""
    
    @pytest.mark.asyncio
    async def test_full_workflow(self, sample_audio_data):
        """Test the complete speech recognition workflow."""
        # Mock both services
        mock_assemblyai_client = Mock()
        mock_transcript = Mock()
        mock_transcript.status = "completed"
        mock_transcript.text = "Hello world"
        mock_transcript.confidence = 0.95
        mock_transcript.language_code = "en"
        mock_assemblyai_client.transcribe.return_value = mock_transcript
        
        mock_openai_client = Mock()
        mock_response = Mock()
        mock_response.text = "Hello world"
        mock_response.language = "en"
        mock_openai_client.audio.transcriptions.create.return_value = mock_response
        
        with patch('assemblyai.Client', return_value=mock_assemblyai_client), \
             patch('openai.OpenAI', return_value=mock_openai_client):
            
            # Initialize recognizer
            recognizer = SpeechRecognition(
                assemblyai_api_key="test_key",
                openai_api_key="test_key",
                custom_vocabulary=["test", "example"],
                cache_size=10,
                confidence_threshold=0.5
            )
            
            # Test transcription
            result = await recognizer.transcribe_stream(sample_audio_data)
            assert result.text == "Hello world"
            assert result.confidence == 0.95
            
            # Test cache hit
            cached_result = await recognizer.transcribe_stream(sample_audio_data)
            assert cached_result.text == result.text
            
            # Test confidence analysis
            analysis = recognizer.analyze_confidence(result)
            assert analysis["confidence_level"] == "excellent"
            
            # Test service switching
            assert recognizer.switch_service(ServiceType.WHISPER) is True
            assert recognizer.service == ServiceType.WHISPER
            
            # Test custom vocabulary management
            recognizer.add_custom_vocabulary(["new", "terms"])
            assert len(recognizer.custom_vocabulary) == 4
            
            # Test cache management
            cache_info = recognizer.get_cache_info()
            assert cache_info["size"] > 0
            assert cache_info["custom_vocabulary_size"] == 4


if __name__ == "__main__":
    pytest.main([__file__]) 
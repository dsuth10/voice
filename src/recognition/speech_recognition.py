"""
Speech Recognition Module

This module provides speech-to-text transcription capabilities using AssemblyAI
as the primary service with OpenAI Whisper as a fallback option.
"""

import asyncio
import logging
import hashlib
import json
import time
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass
from enum import Enum

import assemblyai as aai
import openai
import numpy as np
from scipy import signal

logger = logging.getLogger(__name__)


class ServiceType(Enum):
    """Enumeration of available speech recognition services."""
    ASSEMBLYAI = "assemblyai"
    WHISPER = "whisper"


@dataclass
class TranscriptionResult:
    """Container for transcription results with metadata."""
    text: str
    confidence: float
    service: ServiceType
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    language: Optional[str] = None
    is_final: bool = True
    
    def is_high_confidence(self, threshold: float = 0.8) -> bool:
        """Check if the transcription has high confidence."""
        return self.confidence >= threshold
    
    def is_acceptable_confidence(self, threshold: float = 0.5) -> bool:
        """Check if the transcription has acceptable confidence."""
        return self.confidence >= threshold
    
    def get_confidence_level(self) -> str:
        """Get a human-readable confidence level."""
        if self.confidence >= 0.9:
            return "excellent"
        elif self.confidence >= 0.8:
            return "good"
        elif self.confidence >= 0.6:
            return "fair"
        elif self.confidence >= 0.4:
            return "poor"
        else:
            return "very_poor"


class SpeechRecognitionError(Exception):
    """Custom exception for speech recognition errors."""
    pass


class RetryableError(Exception):
    """Exception that can be retried."""
    pass


class NonRetryableError(Exception):
    """Exception that should not be retried."""
    pass


class SpeechRecognition:
    """
    Speech recognition engine with AssemblyAI as primary service and OpenAI Whisper as fallback.
    
    Supports real-time streaming transcription, confidence scoring, and custom vocabulary.
    """
    
    def __init__(
        self,
        assemblyai_api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        service: ServiceType = ServiceType.ASSEMBLYAI,
        fallback: bool = True,
        cache_size: int = 1000,
        confidence_threshold: float = 0.5,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        retry_backoff: float = 2.0,
        custom_vocabulary: Optional[List[str]] = None
    ):
        """
        Initialize the speech recognition engine.
        
        Args:
            assemblyai_api_key: API key for AssemblyAI service
            openai_api_key: API key for OpenAI Whisper service
            service: Primary service to use for transcription
            fallback: Whether to use fallback service on primary failure
            cache_size: Maximum number of cached transcriptions
            confidence_threshold: Minimum confidence score for acceptable results
        """
        self.service = service
        self.fallback = fallback
        self.confidence_threshold = confidence_threshold
        self.cache_size = cache_size
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.retry_backoff = retry_backoff
        self.custom_vocabulary = custom_vocabulary or []
        self._cache: Dict[str, TranscriptionResult] = {}
        
        # Initialize AssemblyAI client
        self.assemblyai_client = None
        if service == ServiceType.ASSEMBLYAI or fallback:
            if not assemblyai_api_key:
                logger.warning("AssemblyAI API key not provided")
            else:
                try:
                    self.assemblyai_client = aai.Client(assemblyai_api_key)
                    logger.info("AssemblyAI client initialized successfully")
                except Exception as e:
                    logger.error(f"Failed to initialize AssemblyAI client: {e}")
                    if service == ServiceType.ASSEMBLYAI:
                        raise SpeechRecognitionError(f"AssemblyAI initialization failed: {e}")
        
        # Initialize OpenAI client
        self.openai_client = None
        if service == ServiceType.WHISPER or fallback:
            if not openai_api_key:
                logger.warning("OpenAI API key not provided")
            else:
                try:
                    self.openai_client = openai.OpenAI(api_key=openai_api_key)
                    logger.info("OpenAI client initialized successfully")
                except Exception as e:
                    logger.error(f"Failed to initialize OpenAI client: {e}")
                    if service == ServiceType.WHISPER:
                        raise SpeechRecognitionError(f"OpenAI initialization failed: {e}")
        
        # Validate that at least one service is available
        if not self.assemblyai_client and not self.openai_client:
            raise SpeechRecognitionError("No speech recognition services available")
    
    def _get_audio_hash(self, audio_data: bytes) -> str:
        """Generate a hash for audio data for caching purposes."""
        return hashlib.md5(audio_data).hexdigest()
    
    def _add_to_cache(self, audio_hash: str, result: TranscriptionResult) -> None:
        """Add transcription result to cache with size management."""
        if len(self._cache) >= self.cache_size:
            # Remove oldest entry (simple FIFO)
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
            logger.debug(f"Removed oldest cache entry: {oldest_key}")
        
        self._cache[audio_hash] = result
        logger.debug(f"Added transcription to cache: {audio_hash[:8]}...")
    
    def _get_cache_key(self, audio_data: bytes, custom_vocabulary: Optional[List[str]] = None) -> str:
        """
        Generate a cache key that includes both audio data and custom vocabulary.
        
        Args:
            audio_data: Audio data as bytes
            custom_vocabulary: Optional custom vocabulary terms
            
        Returns:
            Cache key string
        """
        # Include custom vocabulary in the hash for more accurate caching
        vocab_str = "|".join(sorted(custom_vocabulary or []))
        combined_data = audio_data + vocab_str.encode('utf-8')
        return hashlib.md5(combined_data).hexdigest()
    
    def _get_audio_hash(self, audio_data: bytes) -> str:
        """Generate a hash for audio data for caching purposes."""
        return hashlib.md5(audio_data).hexdigest()
    
    def _get_from_cache(self, audio_hash: str) -> Optional[TranscriptionResult]:
        """Retrieve transcription result from cache."""
        return self._cache.get(audio_hash)
    
    async def _transcribe_assemblyai_stream(
        self,
        audio_stream: bytes,
        custom_vocabulary: Optional[List[str]] = None
    ) -> TranscriptionResult:
        """
        Transcribe audio using AssemblyAI streaming API.
        
        Args:
            audio_stream: Audio data as bytes
            custom_vocabulary: Optional list of custom terms for improved recognition
            
        Returns:
            TranscriptionResult with text and confidence score
        """
        if not self.assemblyai_client:
            raise SpeechRecognitionError("AssemblyAI client not initialized")
        
        async def _transcribe_operation():
            try:
                # Configure transcription options
                config = aai.TranscriptionConfig(
                    language_code="en",
                    custom_spelling=custom_vocabulary if custom_vocabulary else None,
                    punctuate=True,
                    format_text=True
                )
                
                # Create transcription request
                transcript = self.assemblyai_client.transcribe(
                    audio_stream,
                    config=config
                )
                
                if transcript.status == aai.TranscriptStatus.error:
                    raise SpeechRecognitionError(f"AssemblyAI transcription error: {transcript.error}")
                
                # Extract text and confidence
                text = transcript.text or ""
                confidence = getattr(transcript, 'confidence', 0.0) or 0.0
                
                return TranscriptionResult(
                    text=text,
                    confidence=confidence,
                    service=ServiceType.ASSEMBLYAI,
                    language=transcript.language_code,
                    is_final=True
                )
                
            except Exception as e:
                self._handle_api_error(e, "AssemblyAI")
                raise
        
        return await self._retry_with_backoff(_transcribe_operation)
    
    async def _transcribe_whisper(
        self,
        audio_stream: bytes,
        custom_vocabulary: Optional[List[str]] = None
    ) -> TranscriptionResult:
        """
        Transcribe audio using OpenAI Whisper API.
        
        Args:
            audio_stream: Audio data as bytes
            custom_vocabulary: Optional list of custom terms (note: Whisper doesn't support custom vocabulary)
            
        Returns:
            TranscriptionResult with text and confidence score
        """
        if not self.openai_client:
            raise SpeechRecognitionError("OpenAI client not initialized")
        
        async def _transcribe_operation():
            try:
                # OpenAI Whisper doesn't support custom vocabulary in the same way
                # We'll use the whisper-1 model for best accuracy
                response = self.openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=("audio.wav", audio_stream, "audio/wav"),
                    response_format="verbose_json"
                )
                
                # Extract text and confidence
                text = response.text or ""
                # Whisper doesn't provide confidence scores, so we'll use a default
                confidence = 0.8  # Default confidence for Whisper
                
                return TranscriptionResult(
                    text=text,
                    confidence=confidence,
                    service=ServiceType.WHISPER,
                    language=response.language,
                    is_final=True
                )
                
            except Exception as e:
                self._handle_api_error(e, "OpenAI Whisper")
                raise
        
        return await self._retry_with_backoff(_transcribe_operation)
    
    async def transcribe_stream(
        self,
        audio_stream: bytes,
        custom_vocabulary: Optional[List[str]] = None,
        force_service: Optional[ServiceType] = None
    ) -> TranscriptionResult:
        """
        Transcribe audio stream using the configured service with fallback.
        
        Args:
            audio_stream: Audio data as bytes
            custom_vocabulary: Optional list of custom terms for improved recognition
            force_service: Optional service to force use (bypasses primary/fallback logic)
            
        Returns:
            TranscriptionResult with transcription text and metadata
        """
        # Use provided custom vocabulary or default
        vocab_to_use = custom_vocabulary if custom_vocabulary is not None else self.custom_vocabulary
        
        # Check cache first
        cache_key = self._get_cache_key(audio_stream, vocab_to_use)
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            logger.debug("Using cached transcription result")
            return cached_result
        
        # Determine which service to use
        if force_service:
            service_to_use = force_service
            logger.info(f"Forcing use of {service_to_use.value} service")
        else:
            service_to_use = self.service
        
        # Try primary service
        try:
            if service_to_use == ServiceType.ASSEMBLYAI:
                result = await self._transcribe_assemblyai_stream(audio_stream, vocab_to_use)
            else:
                result = await self._transcribe_whisper(audio_stream, vocab_to_use)
            
            # Cache the result if confidence is above threshold
            if result.confidence >= self.confidence_threshold:
                self._add_to_cache(cache_key, result)
            
            return result
            
        except Exception as e:
            logger.warning(f"Primary service ({service_to_use.value}) failed: {e}")
            
            # Try fallback service if not forcing a specific service
            if self.fallback and not force_service:
                fallback_service = ServiceType.WHISPER if service_to_use == ServiceType.ASSEMBLYAI else ServiceType.ASSEMBLYAI
                logger.info(f"Attempting fallback to {fallback_service.value}")
                
                try:
                    if fallback_service == ServiceType.ASSEMBLYAI:
                        result = await self._transcribe_assemblyai_stream(audio_stream, vocab_to_use)
                    else:
                        result = await self._transcribe_whisper(audio_stream, vocab_to_use)
                    
                    # Cache the result if confidence is above threshold
                    if result.confidence >= self.confidence_threshold:
                        self._add_to_cache(cache_key, result)
                    
                    return result
                    
                except Exception as fallback_error:
                    logger.error(f"Fallback service ({fallback_service.value}) also failed: {fallback_error}")
                    raise SpeechRecognitionError(f"All transcription services failed. Primary: {e}, Fallback: {fallback_error}")
            else:
                raise SpeechRecognitionError(f"Primary service failed and fallback disabled: {e}")
    
    def get_available_services(self) -> List[ServiceType]:
        """Get list of available services."""
        available = []
        if self.assemblyai_client:
            available.append(ServiceType.ASSEMBLYAI)
        if self.openai_client:
            available.append(ServiceType.WHISPER)
        return available
    
    def switch_service(self, new_service: ServiceType) -> bool:
        """
        Switch to a different service.
        
        Args:
            new_service: The service to switch to
            
        Returns:
            True if switch was successful, False otherwise
        """
        if new_service == ServiceType.ASSEMBLYAI and not self.assemblyai_client:
            logger.error("Cannot switch to AssemblyAI - client not available")
            return False
        elif new_service == ServiceType.WHISPER and not self.openai_client:
            logger.error("Cannot switch to Whisper - client not available")
            return False
        
        self.service = new_service
        logger.info(f"Switched to {new_service.value} service")
        return True
    
    def add_custom_vocabulary(self, terms: List[str]) -> None:
        """
        Add custom vocabulary terms for improved recognition.
        
        Args:
            terms: List of terms to add to custom vocabulary
        """
        for term in terms:
            if term not in self.custom_vocabulary:
                self.custom_vocabulary.append(term)
        logger.info(f"Added {len(terms)} terms to custom vocabulary")
    
    def remove_custom_vocabulary(self, terms: List[str]) -> None:
        """
        Remove terms from custom vocabulary.
        
        Args:
            terms: List of terms to remove from custom vocabulary
        """
        for term in terms:
            if term in self.custom_vocabulary:
                self.custom_vocabulary.remove(term)
        logger.info(f"Removed {len(terms)} terms from custom vocabulary")
    
    def clear_custom_vocabulary(self) -> None:
        """Clear all custom vocabulary terms."""
        self.custom_vocabulary.clear()
        logger.info("Cleared custom vocabulary")
    
    def get_custom_vocabulary(self) -> List[str]:
        """Get the current custom vocabulary."""
        return self.custom_vocabulary.copy()
    
    def set_custom_vocabulary(self, terms: List[str]) -> None:
        """
        Set the complete custom vocabulary.
        
        Args:
            terms: Complete list of custom vocabulary terms
        """
        self.custom_vocabulary = terms.copy()
        logger.info(f"Set custom vocabulary to {len(terms)} terms")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get detailed cache information."""
        return {
            "size": len(self._cache),
            "max_size": self.cache_size,
            "hit_rate": len(self._cache) / self.cache_size if self.cache_size > 0 else 0,
            "custom_vocabulary_size": len(self.custom_vocabulary),
            "custom_vocabulary_terms": self.custom_vocabulary.copy()
        }
    
    def resize_cache(self, new_size: int) -> None:
        """
        Resize the cache to a new maximum size.
        
        Args:
            new_size: New maximum cache size
        """
        if new_size < 0:
            raise ValueError("Cache size must be non-negative")
        
        old_size = self.cache_size
        self.cache_size = new_size
        
        # Remove excess entries if new size is smaller
        while len(self._cache) > new_size:
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
        
        logger.info(f"Resized cache from {old_size} to {new_size} entries")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "size": len(self._cache),
            "max_size": self.cache_size,
            "hit_rate": len(self._cache) / self.cache_size if self.cache_size > 0 else 0
        }
    
    def clear_cache(self) -> None:
        """Clear the transcription cache."""
        self._cache.clear()
        logger.info("Transcription cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "size": len(self._cache),
            "max_size": self.cache_size,
            "hit_rate": len(self._cache) / self.cache_size if self.cache_size > 0 else 0
        }
    
    def set_confidence_threshold(self, threshold: float) -> None:
        """Set the confidence threshold for acceptable transcriptions."""
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("Confidence threshold must be between 0.0 and 1.0")
        self.confidence_threshold = threshold
        logger.info(f"Confidence threshold set to {threshold}")
    
    def _classify_error(self, error: Exception) -> type:
        """
        Classify an error as retryable or non-retryable.
        
        Args:
            error: The exception to classify
            
        Returns:
            RetryableError or NonRetryableError
        """
        # Network-related errors are typically retryable
        if isinstance(error, (ConnectionError, TimeoutError, OSError)):
            return RetryableError
        
        # API rate limiting and temporary server errors
        if hasattr(error, 'status_code'):
            if error.status_code in [429, 500, 502, 503, 504]:
                return RetryableError
        
        # Authentication and authorization errors are not retryable
        if hasattr(error, 'status_code') and error.status_code in [401, 403]:
            return NonRetryableError
        
        # Invalid input errors are not retryable
        if hasattr(error, 'status_code') and error.status_code in [400, 422]:
            return NonRetryableError
        
        # Default to retryable for unknown errors
        return RetryableError
    
    def _should_retry(self, error: Exception, attempt: int) -> bool:
        """
        Determine if an error should be retried.
        
        Args:
            error: The exception that occurred
            attempt: Current attempt number (1-based)
            
        Returns:
            True if the error should be retried, False otherwise
        """
        if attempt >= self.max_retries:
            return False
        
        error_type = self._classify_error(error)
        return error_type == RetryableError
    
    async def _retry_with_backoff(
        self,
        operation: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute an operation with exponential backoff retry logic.
        
        Args:
            operation: The async function to execute
            *args: Arguments to pass to the operation
            **kwargs: Keyword arguments to pass to the operation
            
        Returns:
            Result of the operation
            
        Raises:
            SpeechRecognitionError: If all retries are exhausted
        """
        last_error = None
        
        for attempt in range(1, self.max_retries + 1):
            try:
                return await operation(*args, **kwargs)
                
            except Exception as e:
                last_error = e
                logger.warning(f"Attempt {attempt} failed: {e}")
                
                if not self._should_retry(e, attempt):
                    logger.error(f"Non-retryable error encountered: {e}")
                    raise SpeechRecognitionError(f"Non-retryable error: {e}")
                
                if attempt < self.max_retries:
                    delay = self.retry_delay * (self.retry_backoff ** (attempt - 1))
                    logger.info(f"Retrying in {delay:.2f} seconds...")
                    await asyncio.sleep(delay)
        
        # All retries exhausted
        raise SpeechRecognitionError(f"Operation failed after {self.max_retries} attempts. Last error: {last_error}")
    
    def _handle_api_error(self, error: Exception, service_name: str) -> None:
        """
        Handle API-specific errors with appropriate logging and error classification.
        
        Args:
            error: The API error
            service_name: Name of the service that generated the error
        """
        error_msg = str(error)
        
        # Log the error with appropriate level
        if hasattr(error, 'status_code'):
            if error.status_code >= 500:
                logger.error(f"{service_name} server error ({error.status_code}): {error_msg}")
            elif error.status_code == 429:
                logger.warning(f"{service_name} rate limit exceeded: {error_msg}")
            elif error.status_code in [401, 403]:
                logger.error(f"{service_name} authentication error ({error.status_code}): {error_msg}")
            else:
                logger.warning(f"{service_name} API error ({error.status_code}): {error_msg}")
        else:
            logger.error(f"{service_name} error: {error_msg}")
    
    def analyze_confidence(self, result: TranscriptionResult) -> Dict[str, Any]:
        """
        Analyze the confidence of a transcription result.
        
        Args:
            result: The transcription result to analyze
            
        Returns:
            Dictionary with confidence analysis
        """
        analysis = {
            "confidence_score": result.confidence,
            "confidence_level": result.get_confidence_level(),
            "is_high_confidence": result.is_high_confidence(),
            "is_acceptable": result.is_acceptable_confidence(self.confidence_threshold),
            "recommendation": self._get_confidence_recommendation(result)
        }
        
        return analysis
    
    def _get_confidence_recommendation(self, result: TranscriptionResult) -> str:
        """
        Get a recommendation based on confidence level.
        
        Args:
            result: The transcription result
            
        Returns:
            Recommendation string
        """
        if result.confidence >= 0.9:
            return "Excellent transcription quality - ready for use"
        elif result.confidence >= 0.8:
            return "Good transcription quality - minor review recommended"
        elif result.confidence >= 0.6:
            return "Fair transcription quality - review recommended"
        elif result.confidence >= 0.4:
            return "Poor transcription quality - significant review needed"
        else:
            return "Very poor transcription quality - consider re-recording"
    
    def filter_by_confidence(
        self,
        results: List[TranscriptionResult],
        min_confidence: float = 0.5
    ) -> List[TranscriptionResult]:
        """
        Filter transcription results by confidence threshold.
        
        Args:
            results: List of transcription results
            min_confidence: Minimum confidence threshold
            
        Returns:
            Filtered list of results
        """
        return [result for result in results if result.confidence >= min_confidence]
    
    def get_confidence_statistics(
        self,
        results: List[TranscriptionResult]
    ) -> Dict[str, Any]:
        """
        Calculate confidence statistics for a list of results.
        
        Args:
            results: List of transcription results
            
        Returns:
            Dictionary with confidence statistics
        """
        if not results:
            return {
                "count": 0,
                "average_confidence": 0.0,
                "min_confidence": 0.0,
                "max_confidence": 0.0,
                "high_confidence_count": 0,
                "acceptable_count": 0
            }
        
        confidences = [result.confidence for result in results]
        
        return {
            "count": len(results),
            "average_confidence": sum(confidences) / len(confidences),
            "min_confidence": min(confidences),
            "max_confidence": max(confidences),
            "high_confidence_count": len([r for r in results if r.is_high_confidence()]),
            "acceptable_count": len([r for r in results if r.is_acceptable_confidence()])
        }
    
    def is_service_available(self, service: ServiceType) -> bool:
        """Check if a specific service is available."""
        if service == ServiceType.ASSEMBLYAI:
            return self.assemblyai_client is not None
        elif service == ServiceType.WHISPER:
            return self.openai_client is not None
        return False 
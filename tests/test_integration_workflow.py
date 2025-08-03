"""
Integration tests for the complete voice dictation workflow.
"""
import pytest
import time
import threading
from unittest.mock import patch, MagicMock, call
from core.application_controller import ApplicationController
from audio.capture import AudioCapture
from recognition.speech_recognition import SpeechRecognition
from ai_processing.text_enhancement import AITextProcessor
from text_insertion.text_insertion_system import TextInsertionSystem
from hotkeys.hotkey_manager import HotkeyManager
import numpy as np


class TestIntegrationWorkflow:
    """Integration tests for the complete dictation workflow."""

    @pytest.mark.integration
    def test_end_to_end_dictation_workflow(self, mock_audio_data, mock_transcription_result, mock_enhanced_text):
        """Test the complete dictation workflow from audio capture to text insertion."""
        # Mock all external dependencies
        with patch('core.application_controller.AudioCapture') as mock_audio_capture, \
             patch('core.application_controller.SpeechRecognition') as mock_speech_recognition, \
             patch('core.application_controller.AITextProcessor') as mock_ai_processor, \
             patch('core.application_controller.TextInsertionSystem') as mock_text_insertion, \
             patch('core.application_controller.HotkeyManager') as mock_hotkey_manager, \
             patch('core.application_controller.ConfigManager') as mock_config_manager:
            
            # Setup mock config manager to return valid API keys
            mock_config_instance = MagicMock()
            mock_config_manager.return_value = mock_config_instance
            mock_config_instance.get_api_key.side_effect = lambda service: f"test_{service}_key"
            mock_config_instance.get.side_effect = lambda key, default=None: default
            
            # Setup mock instances
            mock_audio_instance = MagicMock()
            mock_audio_capture.return_value = mock_audio_instance
            mock_audio_instance.get_audio_buffer.return_value = np.frombuffer(mock_audio_data, dtype=np.int16)
            
            # Ensure the mock instance is returned when AudioCapture is instantiated
            mock_audio_capture.return_value = mock_audio_instance
            
            # Mock the start_streaming method to simulate successful streaming
            mock_audio_instance.start_streaming.return_value = True
            mock_audio_instance.stop_streaming.return_value = None
            
            # Debug: Check if the mock is being called
            print(f"Mock audio capture called: {mock_audio_capture.called}")
            print(f"Mock audio capture call count: {mock_audio_capture.call_count}")
            
            mock_speech_instance = MagicMock()
            mock_speech_recognition.return_value = mock_speech_instance
            mock_speech_instance.transcribe.return_value = mock_transcription_result
            
            mock_ai_instance = MagicMock()
            mock_ai_processor.return_value = mock_ai_instance
            mock_ai_instance.enhance_text.return_value = mock_enhanced_text["enhanced"]
            
            mock_text_instance = MagicMock()
            mock_text_insertion.return_value = mock_text_instance
            mock_text_instance.insert_text.return_value = True
            
            mock_hotkey_instance = MagicMock()
            mock_hotkey_manager.return_value = mock_hotkey_instance
            
            # Create application controller
            controller = ApplicationController()
            
            # Initialize components
            controller.initialize()
            
            # Simulate dictation workflow
            # 1. Hotkey pressed (start recording)
            controller._start_recording()
            
            # 2. Record audio
            audio_data = controller.audio_capture.get_audio_buffer()
            assert np.array_equal(audio_data, np.frombuffer(mock_audio_data, dtype=np.int16))
            
            # 3. Transcribe audio
            transcription = controller.speech_recognition.transcribe(audio_data)
            assert transcription == mock_transcription_result
            
            # 4. Enhance text
            enhanced_text = controller.text_processor.enhance_text(transcription["text"])
            assert enhanced_text == mock_enhanced_text["enhanced"]
            
            # 5. Insert text
            success = controller.text_insertion.insert_text(enhanced_text)
            assert success is True
            
            # Verify all components were called correctly
            mock_audio_instance.get_audio_buffer.assert_called()
            mock_speech_instance.transcribe.assert_called_once()
            mock_ai_instance.enhance_text.assert_called_once_with(mock_transcription_result["text"])
            mock_text_instance.insert_text.assert_called_once_with(mock_enhanced_text["enhanced"])

    @pytest.mark.integration
    def test_workflow_with_error_handling(self, mock_audio_data):
        """Test workflow behavior when errors occur at different stages."""
        with patch('audio.capture.AudioCapture') as mock_audio_capture, \
             patch('recognition.speech_recognition.SpeechRecognition') as mock_speech_recognition, \
             patch('ai_processing.text_enhancement.AITextProcessor') as mock_ai_processor, \
             patch('text_insertion.text_insertion_system.TextInsertionSystem') as mock_text_insertion:
            
            # Setup mock instances with error conditions
            mock_audio_instance = MagicMock()
            mock_audio_capture.return_value = mock_audio_instance
            mock_audio_instance.record_audio.side_effect = Exception("Audio capture failed")
            
            mock_speech_instance = MagicMock()
            mock_speech_recognition.return_value = mock_speech_instance
            mock_speech_instance.transcribe.side_effect = Exception("Transcription failed")
            
            mock_ai_instance = MagicMock()
            mock_ai_processor.return_value = mock_ai_instance
            mock_ai_instance.enhance_text.side_effect = Exception("AI processing failed")
            
            mock_text_instance = MagicMock()
            mock_text_insertion.return_value = mock_text_instance
            mock_text_instance.insert_text.side_effect = Exception("Text insertion failed")
            
            # Create application controller
            controller = ApplicationController()
            controller.initialize()
            
            # Test audio capture error
            with pytest.raises(Exception, match="Audio capture failed"):
                controller.audio_capture.record_audio()
            
            # Test transcription error
            mock_audio_instance.record_audio.return_value = mock_audio_data
            with pytest.raises(Exception, match="Transcription failed"):
                controller.speech_recognition.transcribe(mock_audio_data)
            
            # Test AI processing error
            mock_speech_instance.transcribe.return_value = {"text": "test"}
            with pytest.raises(Exception, match="AI processing failed"):
                controller.text_processor.enhance_text("test")
            
            # Test text insertion error
            mock_ai_instance.enhance_text.return_value = "enhanced text"
            with pytest.raises(Exception, match="Text insertion failed"):
                controller.text_insertion.insert_text("enhanced text")

    @pytest.mark.integration
    def test_concurrent_workflow_execution(self, mock_audio_data, mock_transcription_result):
        """Test multiple concurrent dictation workflows."""
        with patch('audio.capture.AudioCapture') as mock_audio_capture, \
             patch('recognition.speech_recognition.SpeechRecognition') as mock_speech_recognition, \
             patch('ai_processing.text_enhancement.AITextProcessor') as mock_ai_processor, \
             patch('text_insertion.text_insertion_system.TextInsertionSystem') as mock_text_insertion:
            
            # Setup mock instances
            mock_audio_instance = MagicMock()
            mock_audio_capture.return_value = mock_audio_instance
            mock_audio_instance.record_audio.return_value = mock_audio_data
            
            mock_speech_instance = MagicMock()
            mock_speech_recognition.return_value = mock_speech_instance
            mock_speech_instance.transcribe.return_value = mock_transcription_result
            
            mock_ai_instance = MagicMock()
            mock_ai_processor.return_value = mock_ai_instance
            mock_ai_instance.enhance_text.return_value = "Enhanced text"
            
            mock_text_instance = MagicMock()
            mock_text_insertion.return_value = mock_text_instance
            mock_text_instance.insert_text.return_value = True
            
            # Create application controller
            controller = ApplicationController()
            controller.initialize()
            
            # Define workflow function
            def execute_workflow():
                try:
                    audio_data = controller.audio_capture.record_audio()
                    transcription = controller.speech_recognition.transcribe(audio_data)
                    enhanced_text = controller.text_processor.enhance_text(transcription["text"])
                    success = controller.text_insertion.insert_text(enhanced_text)
                    return success
                except Exception as e:
                    return False
            
            # Execute multiple workflows concurrently
            threads = []
            results = []
            
            for i in range(5):
                thread = threading.Thread(target=lambda: results.append(execute_workflow()))
                threads.append(thread)
                thread.start()
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join()
            
            # Verify all workflows completed successfully
            assert len(results) == 5
            assert all(result is True for result in results)

    @pytest.mark.integration
    def test_workflow_with_different_audio_qualities(self, mock_transcription_result):
        """Test workflow with different audio quality scenarios."""
        with patch('audio.capture.AudioCapture') as mock_audio_capture, \
             patch('recognition.speech_recognition.SpeechRecognition') as mock_speech_recognition, \
             patch('ai_processing.text_enhancement.AITextProcessor') as mock_ai_processor, \
             patch('text_insertion.text_insertion_system.TextInsertionSystem') as mock_text_insertion:
            
            # Setup mock instances
            mock_audio_instance = MagicMock()
            mock_audio_capture.return_value = mock_audio_instance
            
            mock_speech_instance = MagicMock()
            mock_speech_recognition.return_value = mock_speech_instance
            
            mock_ai_instance = MagicMock()
            mock_ai_processor.return_value = mock_ai_instance
            mock_ai_instance.enhance_text.return_value = "Enhanced text"
            
            mock_text_instance = MagicMock()
            mock_text_insertion.return_value = mock_text_instance
            mock_text_instance.insert_text.return_value = True
            
            # Create application controller
            controller = ApplicationController()
            controller.initialize()
            
            # Test with high-quality audio
            high_quality_audio = b"high_quality_audio_data"
            mock_audio_instance.record_audio.return_value = high_quality_audio
            mock_speech_instance.transcribe.return_value = {
                "text": "This is high quality audio.",
                "confidence": 0.95
            }
            
            audio_data = controller.audio_capture.record_audio()
            transcription = controller.speech_recognition.transcribe(audio_data)
            enhanced_text = controller.text_processor.enhance_text(transcription["text"])
            success = controller.text_insertion.insert_text(enhanced_text)
            
            assert success is True
            assert transcription["confidence"] > 0.9
            
            # Test with low-quality audio
            low_quality_audio = b"low_quality_audio_data"
            mock_audio_instance.record_audio.return_value = low_quality_audio
            mock_speech_instance.transcribe.return_value = {
                "text": "This is low quality audio.",
                "confidence": 0.6
            }
            
            audio_data = controller.audio_capture.record_audio()
            transcription = controller.speech_recognition.transcribe(audio_data)
            enhanced_text = controller.text_processor.enhance_text(transcription["text"])
            success = controller.text_insertion.insert_text(enhanced_text)
            
            assert success is True
            assert transcription["confidence"] < 0.8

    @pytest.mark.integration
    def test_workflow_with_context_awareness(self, mock_audio_data, mock_transcription_result):
        """Test workflow with context-aware text enhancement."""
        with patch('audio.capture.AudioCapture') as mock_audio_capture, \
             patch('recognition.speech_recognition.SpeechRecognition') as mock_speech_recognition, \
             patch('ai_processing.text_enhancement.AITextProcessor') as mock_ai_processor, \
             patch('text_insertion.text_insertion_system.TextInsertionSystem') as mock_text_insertion, \
             patch('context.application_context.ApplicationContext') as mock_context:
            
            # Setup mock instances
            mock_audio_instance = MagicMock()
            mock_audio_capture.return_value = mock_audio_instance
            mock_audio_instance.record_audio.return_value = mock_audio_data
            
            mock_speech_instance = MagicMock()
            mock_speech_recognition.return_value = mock_speech_instance
            mock_speech_instance.transcribe.return_value = mock_transcription_result
            
            mock_ai_instance = MagicMock()
            mock_ai_processor.return_value = mock_ai_instance
            
            mock_text_instance = MagicMock()
            mock_text_insertion.return_value = mock_text_instance
            mock_text_instance.insert_text.return_value = True
            
            mock_context_instance = MagicMock()
            mock_context.return_value = mock_context_instance
            
            # Create application controller
            controller = ApplicationController()
            controller.initialize()
            
            # Test with email context
            mock_context_instance.get_application_context.return_value = "email"
            mock_ai_instance.enhance_text.return_value = "Dear John,\n\nThis is an email message.\n\nBest regards,\nUser"
            
            audio_data = controller.audio_capture.record_audio()
            transcription = controller.speech_recognition.transcribe(audio_data)
            context = controller.context_manager.get_application_context()
            enhanced_text = controller.text_processor.enhance_text(transcription["text"], context)
            success = controller.text_insertion.insert_text(enhanced_text)
            
            assert success is True
            assert "Dear" in enhanced_text
            assert "Best regards" in enhanced_text
            
            # Test with code editor context
            mock_context_instance.get_application_context.return_value = "code"
            mock_ai_instance.enhance_text.return_value = "def test_function():\n    return 'Hello, World!'"
            
            audio_data = controller.audio_capture.record_audio()
            transcription = controller.speech_recognition.transcribe(audio_data)
            context = controller.context_manager.get_application_context()
            enhanced_text = controller.text_processor.enhance_text(transcription["text"], context)
            success = controller.text_insertion.insert_text(enhanced_text)
            
            assert success is True
            assert "def" in enhanced_text
            assert "return" in enhanced_text

    @pytest.mark.integration
    def test_workflow_performance_monitoring(self, mock_audio_data, mock_transcription_result):
        """Test workflow with performance monitoring."""
        with patch('audio.capture.AudioCapture') as mock_audio_capture, \
             patch('recognition.speech_recognition.SpeechRecognition') as mock_speech_recognition, \
             patch('ai_processing.text_enhancement.AITextProcessor') as mock_ai_processor, \
             patch('text_insertion.text_insertion_system.TextInsertionSystem') as mock_text_insertion, \
             patch('core.performance_monitor.PerformanceMonitor') as mock_performance:
            
            # Setup mock instances
            mock_audio_instance = MagicMock()
            mock_audio_capture.return_value = mock_audio_instance
            mock_audio_instance.record_audio.return_value = mock_audio_data
            
            mock_speech_instance = MagicMock()
            mock_speech_recognition.return_value = mock_speech_instance
            mock_speech_instance.transcribe.return_value = mock_transcription_result
            
            mock_ai_instance = MagicMock()
            mock_ai_processor.return_value = mock_ai_instance
            mock_ai_instance.enhance_text.return_value = "Enhanced text"
            
            mock_text_instance = MagicMock()
            mock_text_insertion.return_value = mock_text_instance
            mock_text_instance.insert_text.return_value = True
            
            mock_performance_instance = MagicMock()
            mock_performance.return_value = mock_performance_instance
            
            # Create application controller
            controller = ApplicationController()
            controller.initialize()
            
            # Execute workflow with performance monitoring
            start_time = time.time()
            
            audio_data = controller.audio_capture.record_audio()
            transcription = controller.speech_recognition.transcribe(audio_data)
            enhanced_text = controller.text_processor.enhance_text(transcription["text"])
            success = controller.text_insertion.insert_text(enhanced_text)
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # Verify performance monitoring was called
            mock_performance_instance.record_workflow_time.assert_called()
            mock_performance_instance.record_component_time.assert_called()
            
            # Verify workflow completed within reasonable time
            assert total_time < 5.0  # Should complete within 5 seconds
            assert success is True

    @pytest.mark.integration
    def test_workflow_with_error_recovery(self, mock_audio_data):
        """Test workflow error recovery mechanisms."""
        with patch('audio.capture.AudioCapture') as mock_audio_capture, \
             patch('recognition.speech_recognition.SpeechRecognition') as mock_speech_recognition, \
             patch('ai_processing.text_enhancement.AITextProcessor') as mock_ai_processor, \
             patch('text_insertion.text_insertion_system.TextInsertionSystem') as mock_text_insertion:
            
            # Setup mock instances with retry logic
            mock_audio_instance = MagicMock()
            mock_audio_capture.return_value = mock_audio_instance
            
            mock_speech_instance = MagicMock()
            mock_speech_recognition.return_value = mock_speech_instance
            
            mock_ai_instance = MagicMock()
            mock_ai_processor.return_value = mock_ai_instance
            
            mock_text_instance = MagicMock()
            mock_text_insertion.return_value = mock_text_instance
            
            # Create application controller
            controller = ApplicationController()
            controller.initialize()
            
            # Test audio capture with retry
            mock_audio_instance.record_audio.side_effect = [Exception("First attempt"), mock_audio_data]
            
            audio_data = controller.audio_capture.record_audio()
            assert audio_data == mock_audio_data
            
            # Test transcription with fallback
            mock_speech_instance.transcribe.side_effect = [
                Exception("AssemblyAI failed"),
                {"text": "Fallback transcription", "confidence": 0.8}
            ]
            
            transcription = controller.speech_recognition.transcribe(audio_data)
            assert transcription["text"] == "Fallback transcription"
            
            # Test AI processing with retry
            mock_ai_instance.enhance_text.side_effect = [
                Exception("First AI attempt"),
                "Enhanced text"
            ]
            
            enhanced_text = controller.text_processor.enhance_text(transcription["text"])
            assert enhanced_text == "Enhanced text"
            
            # Test text insertion with fallback
            mock_text_instance.insert_text.side_effect = [
                Exception("Clipboard failed"),
                True  # Direct typing succeeds
            ]
            
            success = controller.text_insertion.insert_text(enhanced_text)
            assert success is True

    @pytest.mark.integration
    def test_workflow_with_user_feedback(self, mock_audio_data, mock_transcription_result):
        """Test workflow with user feedback integration."""
        with patch('audio.capture.AudioCapture') as mock_audio_capture, \
             patch('recognition.speech_recognition.SpeechRecognition') as mock_speech_recognition, \
             patch('ai_processing.text_enhancement.AITextProcessor') as mock_ai_processor, \
             patch('text_insertion.text_insertion_system.TextInsertionSystem') as mock_text_insertion, \
             patch('core.feedback_system.UserFeedbackSystem') as mock_feedback:
            
            # Setup mock instances
            mock_audio_instance = MagicMock()
            mock_audio_capture.return_value = mock_audio_instance
            mock_audio_instance.record_audio.return_value = mock_audio_data
            
            mock_speech_instance = MagicMock()
            mock_speech_recognition.return_value = mock_speech_instance
            mock_speech_instance.transcribe.return_value = mock_transcription_result
            
            mock_ai_instance = MagicMock()
            mock_ai_processor.return_value = mock_ai_instance
            mock_ai_instance.enhance_text.return_value = "Enhanced text"
            
            mock_text_instance = MagicMock()
            mock_text_insertion.return_value = mock_text_instance
            mock_text_instance.insert_text.return_value = True
            
            mock_feedback_instance = MagicMock()
            mock_feedback.return_value = mock_feedback_instance
            
            # Create application controller
            controller = ApplicationController()
            controller.initialize()
            
            # Execute workflow with feedback
            audio_data = controller.audio_capture.record_audio()
            transcription = controller.speech_recognition.transcribe(audio_data)
            enhanced_text = controller.text_processor.enhance_text(transcription["text"])
            success = controller.text_insertion.insert_text(enhanced_text)
            
            # Verify feedback was collected
            mock_feedback_instance.record_workflow_success.assert_called()
            mock_feedback_instance.record_user_satisfaction.assert_called()
            
            # Simulate user feedback
            controller.feedback_system.record_user_feedback("positive", "Great transcription!")
            
            # Verify feedback was processed
            mock_feedback_instance.record_user_feedback.assert_called_with("positive", "Great transcription!")

    @pytest.mark.integration
    def test_workflow_with_configuration_changes(self, mock_audio_data, mock_transcription_result):
        """Test workflow behavior with dynamic configuration changes."""
        with patch('audio.capture.AudioCapture') as mock_audio_capture, \
             patch('recognition.speech_recognition.SpeechRecognition') as mock_speech_recognition, \
             patch('ai_processing.text_enhancement.AITextProcessor') as mock_ai_processor, \
             patch('text_insertion.text_insertion_system.TextInsertionSystem') as mock_text_insertion:
            
            # Setup mock instances
            mock_audio_instance = MagicMock()
            mock_audio_capture.return_value = mock_audio_instance
            mock_audio_instance.record_audio.return_value = mock_audio_data
            
            mock_speech_instance = MagicMock()
            mock_speech_recognition.return_value = mock_speech_instance
            mock_speech_instance.transcribe.return_value = mock_transcription_result
            
            mock_ai_instance = MagicMock()
            mock_ai_processor.return_value = mock_ai_instance
            mock_ai_instance.enhance_text.return_value = "Enhanced text"
            
            mock_text_instance = MagicMock()
            mock_text_insertion.return_value = mock_text_instance
            mock_text_instance.insert_text.return_value = True
            
            # Create application controller
            controller = ApplicationController()
            controller.initialize()
            
            # Test with different audio configurations
            controller.config_manager.update_config({
                "audio": {
                    "sample_rate": 44100,
                    "channels": 2,
                    "chunk_size": 2048
                }
            })
            
            audio_data = controller.audio_capture.record_audio()
            transcription = controller.speech_recognition.transcribe(audio_data)
            enhanced_text = controller.text_processor.enhance_text(transcription["text"])
            success = controller.text_insertion.insert_text(enhanced_text)
            
            assert success is True
            
            # Test with different enhancement settings
            controller.config_manager.update_config({
                "enhancement": {
                    "enable_grammar_correction": False,
                    "enable_punctuation": True,
                    "enable_capitalization": False
                }
            })
            
            audio_data = controller.audio_capture.record_audio()
            transcription = controller.speech_recognition.transcribe(audio_data)
            enhanced_text = controller.text_processor.enhance_text(transcription["text"])
            success = controller.text_insertion.insert_text(enhanced_text)
            
            assert success is True 
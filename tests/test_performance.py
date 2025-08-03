"""
Performance tests for the Voice Dictation Assistant.

This module contains performance benchmarks and stress tests for all major components
to ensure the application meets performance requirements.
"""

import pytest
import time
import psutil
import threading
from unittest.mock import patch, MagicMock
from core.application_controller import ApplicationController
from audio.capture import AudioCapture
from recognition.speech_recognition import SpeechRecognition
from ai_processing.text_enhancement import AITextProcessor
from text_insertion.text_insertion_system import TextInsertionSystem
from hotkeys.hotkey_manager import HotkeyManager


class TestPerformance:
    """Performance tests for the application."""

    @pytest.mark.performance
    def test_response_time_benchmark(self, mock_audio_data, mock_transcription_result, performance_thresholds):
        """Test end-to-end response time performance."""
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
            
            # Run multiple iterations to get average response time
            response_times = []
            num_iterations = 10
            
            for _ in range(num_iterations):
                start_time = time.time()
                
                # Execute workflow
                audio_data = controller.audio_capture.record_audio()
                transcription = controller.speech_recognition.transcribe(audio_data)
                enhanced_text = controller.text_processor.enhance_text(transcription["text"])
                success = controller.text_insertion.insert_text(enhanced_text)
                
                end_time = time.time()
                response_time = end_time - start_time
                response_times.append(response_time)
                
                assert success is True
            
            # Calculate statistics
            avg_response_time = statistics.mean(response_times)
            max_response_time = max(response_times)
            min_response_time = min(response_times)
            
            # Verify performance meets requirements
            assert avg_response_time < performance_thresholds["max_response_time"], \
                f"Average response time {avg_response_time:.2f}s exceeds threshold {performance_thresholds['max_response_time']}s"
            
            assert max_response_time < performance_thresholds["max_response_time"] * 1.5, \
                f"Maximum response time {max_response_time:.2f}s exceeds threshold"
            
            print(f"Performance Results:")
            print(f"  Average response time: {avg_response_time:.3f}s")
            print(f"  Minimum response time: {min_response_time:.3f}s")
            print(f"  Maximum response time: {max_response_time:.3f}s")

    @pytest.mark.performance
    def test_memory_usage_monitoring(self, mock_audio_data, mock_transcription_result, performance_thresholds):
        """Test memory usage during extended operation."""
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
            
            # Monitor memory usage
            process = psutil.Process()
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            memory_usage = []
            num_iterations = 50
            
            for i in range(num_iterations):
                # Execute workflow
                audio_data = controller.audio_capture.record_audio()
                transcription = controller.speech_recognition.transcribe(audio_data)
                enhanced_text = controller.text_processor.enhance_text(transcription["text"])
                success = controller.text_insertion.insert_text(enhanced_text)
                
                # Record memory usage
                current_memory = process.memory_info().rss / 1024 / 1024  # MB
                memory_usage.append(current_memory)
                
                assert success is True
                
                # Small delay to simulate real usage
                time.sleep(0.01)
            
            # Calculate memory statistics
            final_memory = memory_usage[-1]
            max_memory = max(memory_usage)
            memory_increase = final_memory - initial_memory
            
            # Verify memory usage is within limits
            assert final_memory < performance_thresholds["max_memory_usage"], \
                f"Final memory usage {final_memory:.1f}MB exceeds threshold {performance_thresholds['max_memory_usage']}MB"
            
            assert memory_increase < 50, \
                f"Memory increase {memory_increase:.1f}MB is too high"
            
            print(f"Memory Usage Results:")
            print(f"  Initial memory: {initial_memory:.1f}MB")
            print(f"  Final memory: {final_memory:.1f}MB")
            print(f"  Maximum memory: {max_memory:.1f}MB")
            print(f"  Memory increase: {memory_increase:.1f}MB")

    @pytest.mark.performance
    def test_cpu_usage_monitoring(self, mock_audio_data, mock_transcription_result, performance_thresholds):
        """Test CPU usage during operation."""
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
            
            # Monitor CPU usage
            process = psutil.Process()
            cpu_usage = []
            num_iterations = 20
            
            for _ in range(num_iterations):
                # Execute workflow
                audio_data = controller.audio_capture.record_audio()
                transcription = controller.speech_recognition.transcribe(audio_data)
                enhanced_text = controller.text_processor.enhance_text(transcription["text"])
                success = controller.text_insertion.insert_text(enhanced_text)
                
                # Record CPU usage
                current_cpu = process.cpu_percent()
                cpu_usage.append(current_cpu)
                
                assert success is True
                
                # Small delay for CPU measurement
                time.sleep(0.1)
            
            # Calculate CPU statistics
            avg_cpu = statistics.mean(cpu_usage)
            max_cpu = max(cpu_usage)
            
            # Verify CPU usage is within limits
            assert avg_cpu < performance_thresholds["max_cpu_usage"], \
                f"Average CPU usage {avg_cpu:.1f}% exceeds threshold {performance_thresholds['max_cpu_usage']}%"
            
            print(f"CPU Usage Results:")
            print(f"  Average CPU usage: {avg_cpu:.1f}%")
            print(f"  Maximum CPU usage: {max_cpu:.1f}%")

    @pytest.mark.performance
    def test_concurrent_workflow_performance(self, mock_audio_data, mock_transcription_result):
        """Test performance under concurrent load."""
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
                start_time = time.time()
                try:
                    audio_data = controller.audio_capture.record_audio()
                    transcription = controller.speech_recognition.transcribe(audio_data)
                    enhanced_text = controller.text_processor.enhance_text(transcription["text"])
                    success = controller.text_insertion.insert_text(enhanced_text)
                    end_time = time.time()
                    return end_time - start_time, success
                except Exception as e:
                    return None, False
            
            # Test with different concurrency levels
            concurrency_levels = [1, 2, 4, 8]
            results = {}
            
            for num_threads in concurrency_levels:
                threads = []
                response_times = []
                
                start_time = time.time()
                
                for _ in range(num_threads):
                    thread = threading.Thread(target=lambda: response_times.append(execute_workflow()))
                    threads.append(thread)
                    thread.start()
                
                # Wait for all threads to complete
                for thread in threads:
                    thread.join()
                
                end_time = time.time()
                total_time = end_time - start_time
                
                # Filter out failed workflows
                successful_times = [time for time, success in response_times if success]
                
                if successful_times:
                    avg_response_time = statistics.mean(successful_times)
                    throughput = len(successful_times) / total_time
                    
                    results[num_threads] = {
                        'avg_response_time': avg_response_time,
                        'throughput': throughput,
                        'success_rate': len(successful_times) / len(response_times)
                    }
            
            # Verify performance characteristics
            for num_threads, result in results.items():
                assert result['success_rate'] > 0.8, \
                    f"Success rate {result['success_rate']:.2f} too low for {num_threads} threads"
                
                assert result['avg_response_time'] < 5.0, \
                    f"Average response time {result['avg_response_time']:.2f}s too high for {num_threads} threads"
            
            print(f"Concurrent Performance Results:")
            for num_threads, result in results.items():
                print(f"  {num_threads} threads:")
                print(f"    Avg response time: {result['avg_response_time']:.3f}s")
                print(f"    Throughput: {result['throughput']:.2f} workflows/second")
                print(f"    Success rate: {result['success_rate']:.2f}")

    @pytest.mark.performance
    def test_large_text_processing_performance(self, mock_audio_data):
        """Test performance with large text inputs."""
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
            
            mock_ai_instance = MagicMock()
            mock_ai_processor.return_value = mock_ai_instance
            
            mock_text_instance = MagicMock()
            mock_text_insertion.return_value = mock_text_instance
            mock_text_instance.insert_text.return_value = True
            
            # Create application controller
            controller = ApplicationController()
            controller.initialize()
            
            # Test with different text sizes
            text_sizes = [100, 500, 1000, 2000]  # words
            results = {}
            
            for size in text_sizes:
                # Generate large text
                large_text = "This is a test sentence. " * size
                mock_speech_instance.transcribe.return_value = {
                    "text": large_text,
                    "confidence": 0.9
                }
                
                mock_ai_instance.enhance_text.return_value = large_text + " Enhanced."
                
                # Measure processing time
                start_time = time.time()
                
                audio_data = controller.audio_capture.record_audio()
                transcription = controller.speech_recognition.transcribe(audio_data)
                enhanced_text = controller.text_processor.enhance_text(transcription["text"])
                success = controller.text_insertion.insert_text(enhanced_text)
                
                end_time = time.time()
                processing_time = end_time - start_time
                
                results[size] = {
                    'processing_time': processing_time,
                    'words_per_second': size / processing_time,
                    'success': success
                }
            
            # Verify performance characteristics
            for size, result in results.items():
                assert result['success'] is True, \
                    f"Processing failed for {size} words"
                
                assert result['processing_time'] < 10.0, \
                    f"Processing time {result['processing_time']:.2f}s too high for {size} words"
                
                assert result['words_per_second'] > 50, \
                    f"Processing rate {result['words_per_second']:.1f} words/second too low for {size} words"
            
            print(f"Large Text Processing Results:")
            for size, result in results.items():
                print(f"  {size} words:")
                print(f"    Processing time: {result['processing_time']:.3f}s")
                print(f"    Words per second: {result['words_per_second']:.1f}")

    @pytest.mark.performance
    def test_stress_test_long_session(self, mock_audio_data, mock_transcription_result):
        """Test application stability during long sessions."""
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
            
            # Monitor system resources
            process = psutil.Process()
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Run stress test
            num_iterations = 100
            successful_workflows = 0
            memory_usage = []
            
            start_time = time.time()
            
            for i in range(num_iterations):
                try:
                    # Execute workflow
                    audio_data = controller.audio_capture.record_audio()
                    transcription = controller.speech_recognition.transcribe(audio_data)
                    enhanced_text = controller.text_processor.enhance_text(transcription["text"])
                    success = controller.text_insertion.insert_text(enhanced_text)
                    
                    if success:
                        successful_workflows += 1
                    
                    # Record memory usage every 10 iterations
                    if i % 10 == 0:
                        current_memory = process.memory_info().rss / 1024 / 1024  # MB
                        memory_usage.append(current_memory)
                    
                    # Small delay to simulate real usage
                    time.sleep(0.01)
                    
                except Exception as e:
                    print(f"Error at iteration {i}: {e}")
                    continue
            
            end_time = time.time()
            total_time = end_time - start_time
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Calculate statistics
            success_rate = successful_workflows / num_iterations
            throughput = successful_workflows / total_time
            memory_increase = final_memory - initial_memory
            
            # Verify stability
            assert success_rate > 0.95, \
                f"Success rate {success_rate:.2f} too low for stress test"
            
            assert memory_increase < 100, \
                f"Memory increase {memory_increase:.1f}MB too high for stress test"
            
            assert throughput > 1.0, \
                f"Throughput {throughput:.2f} workflows/second too low"
            
            print(f"Stress Test Results:")
            print(f"  Total iterations: {num_iterations}")
            print(f"  Successful workflows: {successful_workflows}")
            print(f"  Success rate: {success_rate:.2f}")
            print(f"  Total time: {total_time:.2f}s")
            print(f"  Throughput: {throughput:.2f} workflows/second")
            print(f"  Memory increase: {memory_increase:.1f}MB")

    @pytest.mark.performance
    def test_accuracy_performance(self, mock_audio_data, performance_thresholds):
        """Test transcription accuracy performance."""
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
            
            mock_ai_instance = MagicMock()
            mock_ai_processor.return_value = mock_ai_instance
            mock_ai_instance.enhance_text.return_value = "Enhanced text"
            
            mock_text_instance = MagicMock()
            mock_text_insertion.return_value = mock_text_instance
            mock_text_instance.insert_text.return_value = True
            
            # Create application controller
            controller = ApplicationController()
            controller.initialize()
            
            # Test with different confidence levels
            confidence_levels = [0.6, 0.7, 0.8, 0.9, 0.95]
            accuracy_results = {}
            
            for confidence in confidence_levels:
                mock_speech_instance.transcribe.return_value = {
                    "text": "This is a test transcription.",
                    "confidence": confidence
                }
                
                # Execute workflow
                audio_data = controller.audio_capture.record_audio()
                transcription = controller.speech_recognition.transcribe(audio_data)
                
                # Record accuracy
                accuracy_results[confidence] = transcription["confidence"]
            
            # Verify accuracy meets requirements
            for confidence, actual_accuracy in accuracy_results.items():
                assert actual_accuracy >= confidence, \
                    f"Actual accuracy {actual_accuracy:.2f} below expected {confidence:.2f}"
            
            # Verify minimum accuracy threshold
            min_accuracy = min(accuracy_results.values())
            assert min_accuracy >= performance_thresholds["min_accuracy"], \
                f"Minimum accuracy {min_accuracy:.2f} below threshold {performance_thresholds['min_accuracy']:.2f}"
            
            print(f"Accuracy Performance Results:")
            for confidence, actual_accuracy in accuracy_results.items():
                print(f"  Expected {confidence:.2f}: Actual {actual_accuracy:.2f}")
            print(f"  Minimum accuracy: {min_accuracy:.2f}") 
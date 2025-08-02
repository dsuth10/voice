"""
Example script demonstrating AudioCapture functionality.

This script shows how to:
- List and select microphones
- Perform batch recording
- Start real-time streaming
- Monitor audio levels
- Handle silence and speech detection
"""

import sys
import os
import time
import numpy as np

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from audio.capture import AudioCapture, audio_capture_context


def list_microphones_example():
    """Example: List all available microphones."""
    print("=== Microphone Enumeration Example ===")
    
    with AudioCapture() as capture:
        microphones = capture.list_microphones()
        
        if not microphones:
            print("No microphones found!")
            return
        
        print(f"Found {len(microphones)} microphone(s):")
        for i, mic in enumerate(microphones):
            print(f"  {i}: {mic['name']}")
            print(f"     Channels: {mic['channels']}")
            print(f"     Sample Rate: {mic['sample_rate']} Hz")
            print(f"     Latency: {mic['latency_low']:.3f}s - {mic['latency_high']:.3f}s")
            print()


def microphone_selection_example():
    """Example: Select microphone by index or name."""
    print("=== Microphone Selection Example ===")
    
    with AudioCapture() as capture:
        # List available microphones
        microphones = capture.list_microphones()
        
        if not microphones:
            print("No microphones available for testing")
            return
        
        # Select by index
        print(f"Selecting microphone by index: 0")
        if capture.select_microphone(device_index=0):
            print("✓ Successfully selected microphone by index")
        else:
            print("✗ Failed to select microphone by index")
        
        # Select by name (partial match)
        if microphones:
            mic_name = microphones[0]['name']
            print(f"Selecting microphone by name: '{mic_name}'")
            if capture.select_microphone(device_name=mic_name):
                print("✓ Successfully selected microphone by name")
            else:
                print("✗ Failed to select microphone by name")
        
        print()


def batch_recording_example():
    """Example: Record audio for a specified duration."""
    print("=== Batch Recording Example ===")
    
    with AudioCapture() as capture:
        print("Recording 3 seconds of audio...")
        print("Please speak into your microphone...")
        
        # Record for 3 seconds
        audio_data = capture.record_batch(duration=3.0)
        
        if audio_data is not None:
            print(f"✓ Recording completed!")
            print(f"   Samples: {len(audio_data)}")
            print(f"   Duration: {len(audio_data) / capture.sample_rate:.2f} seconds")
            print(f"   Audio level: {capture._calculate_audio_level(audio_data):.4f}")
        else:
            print("✗ Recording failed!")
        
        print()


def streaming_example():
    """Example: Real-time audio streaming with callbacks."""
    print("=== Streaming Example ===")
    
    # Callback counters
    silence_count = 0
    speech_count = 0
    level_sum = 0.0
    level_count = 0
    
    def silence_callback(level):
        nonlocal silence_count
        silence_count += 1
        print(f"Silence detected (level: {level:.4f})")
    
    def speech_callback(level):
        nonlocal speech_count
        speech_count += 1
        print(f"Speech detected (level: {level:.4f})")
    
    def level_callback(level):
        nonlocal level_sum, level_count
        level_sum += level
        level_count += 1
    
    with AudioCapture(silence_threshold=0.005) as capture:
        print("Starting audio streaming for 5 seconds...")
        print("Please speak into your microphone...")
        
        # Start streaming
        if capture.start_streaming(
            silence_callback=silence_callback,
            speech_callback=speech_callback,
            level_callback=level_callback
        ):
            print("✓ Streaming started")
            
            # Stream for 5 seconds
            time.sleep(5.0)
            
            # Stop streaming
            capture.stop_streaming()
            print("✓ Streaming stopped")
            
            # Print statistics
            print(f"\nStreaming Statistics:")
            print(f"  Silence events: {silence_count}")
            print(f"  Speech events: {speech_count}")
            if level_count > 0:
                avg_level = level_sum / level_count
                print(f"  Average audio level: {avg_level:.4f}")
            
            # Show buffer contents
            buffer_data = capture.get_audio_buffer()
            print(f"  Buffer samples: {len(buffer_data)}")
            
        else:
            print("✗ Failed to start streaming")
        
        print()


def audio_level_monitoring_example():
    """Example: Monitor audio levels in real-time."""
    print("=== Audio Level Monitoring Example ===")
    
    with AudioCapture() as capture:
        print("Monitoring audio levels for 5 seconds...")
        print("Please speak at different volumes...")
        
        # Start streaming
        if capture.start_streaming():
            print("✓ Level monitoring started")
            
            # Monitor levels for 5 seconds
            start_time = time.time()
            while time.time() - start_time < 5.0:
                level = capture.get_audio_level()
                print(f"Audio level: {level:.4f}", end='\r')
                time.sleep(0.1)
            
            print()  # New line after progress
            capture.stop_streaming()
            print("✓ Level monitoring stopped")
            
        else:
            print("✗ Failed to start level monitoring")
        
        print()


def noise_filtering_example():
    """Example: Demonstrate noise filtering functionality."""
    print("=== Noise Filtering Example ===")
    
    # Create test audio data with noise
    sample_rate = 16000
    duration = 1.0
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # Create signal with noise
    signal_freq = 1000  # 1kHz tone
    signal_data = np.sin(2 * np.pi * signal_freq * t)
    noise = np.random.normal(0, 0.1, len(t))  # Add noise
    noisy_signal = signal_data + noise
    
    # Convert to 16-bit audio
    audio_data = (noisy_signal * 32767).astype(np.int16)
    
    print("Testing noise filtering...")
    
    with AudioCapture(noise_filter_enabled=True) as capture:
        # Apply noise filter
        filtered_audio = capture._apply_noise_filter(audio_data)
        
        # Calculate signal-to-noise ratios
        original_level = capture._calculate_audio_level(audio_data)
        filtered_level = capture._calculate_audio_level(filtered_audio)
        
        print(f"Original audio level: {original_level:.4f}")
        print(f"Filtered audio level: {filtered_level:.4f}")
        print(f"Improvement: {((filtered_level - original_level) / original_level * 100):.1f}%")
        
        # Test with disabled filter
        capture.noise_filter_enabled = False
        unfiltered_audio = capture._apply_noise_filter(audio_data)
        unfiltered_level = capture._calculate_audio_level(unfiltered_audio)
        print(f"Unfiltered audio level: {unfiltered_level:.4f}")
    
    print()


def context_manager_example():
    """Example: Using AudioCapture with context manager."""
    print("=== Context Manager Example ===")
    
    print("Using AudioCapture with context manager...")
    
    with audio_capture_context(
        sample_rate=16000,
        chunk_size=512,
        buffer_duration=2.0,
        silence_threshold=0.01
    ) as capture:
        print("✓ AudioCapture initialized with context manager")
        print(f"   Sample rate: {capture.sample_rate} Hz")
        print(f"   Chunk size: {capture.chunk_size}")
        print(f"   Buffer duration: {capture.buffer_duration} seconds")
        print(f"   Silence threshold: {capture.silence_threshold}")
        
        # Test microphone selection
        if capture.select_microphone():
            print("✓ Microphone selected")
        else:
            print("✗ Failed to select microphone")
    
    print("✓ Context manager cleanup completed")
    print()


def main():
    """Run all audio capture examples."""
    print("AudioCapture Module Examples")
    print("=" * 50)
    print()
    
    try:
        # Run examples
        list_microphones_example()
        microphone_selection_example()
        batch_recording_example()
        streaming_example()
        audio_level_monitoring_example()
        noise_filtering_example()
        context_manager_example()
        
        print("All examples completed successfully!")
        
    except Exception as e:
        print(f"Error running examples: {e}")
        print("Make sure you have a microphone connected and PyAudio is properly installed.")


if __name__ == '__main__':
    main() 
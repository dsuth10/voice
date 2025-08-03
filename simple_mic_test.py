#!/usr/bin/env python3
"""
Simple Microphone Test
"""

import pyaudio
import time

def simple_mic_test():
    """Simple microphone test"""
    print("🎤 Simple Microphone Test")
    print("=" * 30)
    
    p = pyaudio.PyAudio()
    
    try:
        # Get default input device
        default_input = p.get_default_input_device_info()
        print(f"📋 Default input device: {default_input['name']}")
        
        # Try to open a stream
        print("🔴 Testing microphone access...")
        
        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=1024
        )
        
        print("✅ Microphone access successful!")
        print("🎯 Your microphone is working correctly.")
        
        # Close the stream
        stream.stop_stream()
        stream.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Microphone access failed: {e}")
        print("\n🔧 Troubleshooting steps:")
        print("1. Check Windows microphone permissions")
        print("2. Make sure microphone is not muted")
        print("3. Try running as administrator")
        return False
        
    finally:
        p.terminate()

if __name__ == "__main__":
    simple_mic_test() 
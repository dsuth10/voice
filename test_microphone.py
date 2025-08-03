#!/usr/bin/env python3
"""
Test Microphone and Hotkey Functionality
"""

import pyaudio
import wave
import time
import sys
from pathlib import Path

def test_microphone():
    """Test microphone recording"""
    print("🎤 Testing Microphone...")
    
    # Audio settings
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    RECORD_SECONDS = 3
    
    p = pyaudio.PyAudio()
    
    try:
        # List available input devices
        print("\n📋 Available Input Devices:")
        input_devices = []
        for i in range(p.get_device_count()):
            device_info = p.get_device_info_by_index(i)
            if device_info['maxInputChannels'] > 0:
                input_devices.append((i, device_info['name']))
                print(f"  Device {i}: {device_info['name']}")
        
        # Use default device or first available
        device_index = None
        for i, name in input_devices:
            if 'realtek' in name.lower() or 'built-in' in name.lower():
                device_index = i
                break
        
        if device_index is None and input_devices:
            device_index = input_devices[0][0]
        
        if device_index is None:
            print("❌ No input devices found!")
            return False
        
        print(f"\n🎯 Using Device {device_index}: {p.get_device_info_by_index(device_index)['name']}")
        
        # Test recording
        print("\n🔴 Recording test (3 seconds)...")
        print("Speak into your microphone now...")
        
        stream = p.open(format=FORMAT,
                       channels=CHANNELS,
                       rate=RATE,
                       input=True,
                       input_device_index=device_index,
                       frames_per_buffer=CHUNK)
        
        frames = []
        
        for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
            data = stream.read(CHUNK)
            frames.append(data)
        
        print("✅ Recording completed!")
        
        # Check if we got any audio data
        audio_data = b''.join(frames)
        if len(audio_data) > 0:
            print("✅ Microphone is working!")
            return True
        else:
            print("❌ No audio data captured!")
            return False
            
    except Exception as e:
        print(f"❌ Microphone test failed: {e}")
        return False
    finally:
        if 'stream' in locals():
            stream.stop_stream()
            stream.close()
        p.terminate()

def test_hotkey_config():
    """Test hotkey configuration"""
    print("\n🔧 Testing Hotkey Configuration...")
    
    try:
        import yaml
        config_file = Path.home() / "AppData" / "Roaming" / "VoiceDictationAssistant" / "config.yaml"
        
        if not config_file.exists():
            print("❌ Configuration file not found!")
            return False
        
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        hotkey = config.get('hotkey', {}).get('primary_hotkey', 'Not found')
        print(f"📋 Current hotkey: {hotkey}")
        
        if hotkey == 'win+alt':
            print("✅ Hotkey configured correctly!")
            return True
        else:
            print("❌ Hotkey not configured correctly!")
            return False
            
    except Exception as e:
        print(f"❌ Hotkey test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Voice Dictation Assistant - System Test")
    print("=" * 50)
    
    # Test microphone
    mic_ok = test_microphone()
    
    # Test hotkey
    hotkey_ok = test_hotkey_config()
    
    print("\n📊 Test Results:")
    print(f"Microphone: {'✅ Working' if mic_ok else '❌ Failed'}")
    print(f"Hotkey Config: {'✅ Correct' if hotkey_ok else '❌ Failed'}")
    
    if mic_ok and hotkey_ok:
        print("\n🎉 All tests passed! Your system should work correctly.")
        print("Try running: python run_voice_assistant.py")
    else:
        print("\n⚠️  Some tests failed. Please check the issues above.")

if __name__ == "__main__":
    main() 
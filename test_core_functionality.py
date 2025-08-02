#!/usr/bin/env python3
"""
Core Functionality Test Script
Tests the main application controller and basic workflow
"""

import sys
import os
import time
import logging
from pathlib import Path

# Add src to path
src_path = str(Path(__file__).parent / "src")
sys.path.insert(0, src_path)
print(f"Added {src_path} to Python path")

def setup_logging():
    """Setup basic logging for testing"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('test_core.log')
        ]
    )

def test_configuration():
    """Test configuration loading"""
    print("🔧 Testing Configuration System...")
    try:
        from config.config_manager import ConfigManager
        config = ConfigManager()
        print("✅ Configuration system loaded successfully")
        return config
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return None

def test_audio_capture():
    """Test audio capture functionality"""
    print("🎤 Testing Audio Capture...")
    try:
        from audio.capture import AudioCapture
        with AudioCapture() as audio:
            print("✅ Audio capture initialized successfully")
            # Test microphone enumeration
            devices = audio.list_microphones()
            print(f"✅ Found {len(devices)} microphone devices")
        return True
    except Exception as e:
        print(f"❌ Audio capture test failed: {e}")
        return False

def test_speech_recognition():
    """Test speech recognition setup"""
    print("🗣️ Testing Speech Recognition...")
    try:
        from recognition.speech_recognition import SpeechRecognition
        recognizer = SpeechRecognition()
        print("✅ Speech recognition initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Speech recognition test failed: {e}")
        return False

def test_ai_enhancement():
    """Test AI text enhancement"""
    print("🤖 Testing AI Text Enhancement...")
    try:
        from ai_processing.text_enhancement import AITextProcessor
        processor = AITextProcessor()
        print("✅ AI text processor initialized successfully")
        return True
    except Exception as e:
        print(f"❌ AI enhancement test failed: {e}")
        return False

def test_text_insertion():
    """Test text insertion system"""
    print("📝 Testing Text Insertion...")
    try:
        from text_insertion.text_insertion_system import TextInsertionSystem
        inserter = TextInsertionSystem()
        print("✅ Text insertion system initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Text insertion test failed: {e}")
        return False

def test_hotkey_system():
    """Test hotkey management"""
    print("⌨️ Testing Hotkey System...")
    try:
        from hotkeys.hotkey_manager import HotkeyManager
        hotkey_manager = HotkeyManager()
        print("✅ Hotkey system initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Hotkey system test failed: {e}")
        return False

def test_application_controller():
    """Test the main application controller"""
    print("🎮 Testing Application Controller...")
    try:
        from core.application_controller import ApplicationController
        controller = ApplicationController()
        print("✅ Application controller initialized successfully")
        return controller
    except Exception as e:
        print(f"❌ Application controller test failed: {e}")
        return None

def main():
    """Run all core functionality tests"""
    print("🚀 Starting Core Functionality Tests")
    print("=" * 50)
    
    setup_logging()
    
    # Test individual components
    config_ok = test_configuration()
    audio_ok = test_audio_capture()
    speech_ok = test_speech_recognition()
    ai_ok = test_ai_enhancement()
    text_ok = test_text_insertion()
    hotkey_ok = test_hotkey_system()
    
    # Test main controller
    controller = test_application_controller()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print(f"Configuration: {'✅ PASS' if config_ok else '❌ FAIL'}")
    print(f"Audio Capture: {'✅ PASS' if audio_ok else '❌ FAIL'}")
    print(f"Speech Recognition: {'✅ PASS' if speech_ok else '❌ FAIL'}")
    print(f"AI Enhancement: {'✅ PASS' if ai_ok else '❌ FAIL'}")
    print(f"Text Insertion: {'✅ PASS' if text_ok else '❌ FAIL'}")
    print(f"Hotkey System: {'✅ PASS' if hotkey_ok else '❌ FAIL'}")
    print(f"Application Controller: {'✅ PASS' if controller else '❌ FAIL'}")
    
    if all([config_ok, audio_ok, speech_ok, ai_ok, text_ok, hotkey_ok, controller]):
        print("\n🎉 ALL TESTS PASSED! The application is ready for testing.")
        print("\nTo start the application:")
        print("1. Ensure you have API keys configured")
        print("2. Run: python -m src.core.application_controller")
        print("3. Press Ctrl+Win+Space to start dictation")
    else:
        print("\n⚠️ Some tests failed. Please check the error messages above.")
        print("The application may need configuration or dependency fixes.")

if __name__ == "__main__":
    main() 
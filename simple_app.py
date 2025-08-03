#!/usr/bin/env python3
"""
Simplified Voice Dictation Assistant
Bypasses secure storage issues for testing
"""

import sys
import time
import logging
from pathlib import Path

def setup_logging():
    """Setup logging"""
    log_dir = Path.home() / "AppData" / "Local" / "VoiceDictationAssistant" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_dir / "voice_assistant.log")
        ]
    )

def main():
    """Simplified main function"""
    print("🎤 Voice Dictation Assistant (Simplified)")
    print("=" * 50)
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Import components
        from src.core.application_controller import ApplicationController
        
        print("🚀 Initializing Voice Dictation Assistant...")
        logger.info("Starting Voice Dictation Assistant")
        
        # Create controller
        controller = ApplicationController()
        
        # Bypass API key check for testing
        print("✅ Bypassing API key validation for testing...")
        
        # Initialize components manually
        controller._initialize_text_insertion()
        controller._initialize_context_awareness()
        controller._initialize_hotkey_manager()
        
        # Start hotkey listening
        controller.hotkey_manager.start_listening()
        
        print("✅ Application initialized successfully!")
        print("\n📋 Usage Instructions:")
        print("- Press Windows key + Alt to start dictation")
        print("- Speak clearly into your microphone")
        print("- Release the hotkey to process and insert text")
        print("- Press Ctrl+C to exit the application")
        print("\n🎯 Ready for dictation! Press Windows key + Alt to begin...")
        
        # Keep running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Shutting down...")
            
    except Exception as e:
        print(f"❌ Application startup failed: {e}")
        logger.error(f"Application startup failed: {e}", exc_info=True)
        return 1
    
    finally:
        logger.info("Voice Dictation Assistant shutdown complete")
        print("👋 Goodbye!")

if __name__ == "__main__":
    sys.exit(main()) 
#!/usr/bin/env python3
"""
Voice Dictation Assistant - Main Entry Point
Simple script to start the voice dictation application
"""

import sys
import os
import signal
import logging
from pathlib import Path

def setup_logging():
    """Setup logging for the application"""
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

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    print("\n🛑 Shutting down Voice Dictation Assistant...")
    sys.exit(0)

def main():
    """Main entry point for the voice dictation assistant"""
    print("🎤 Voice Dictation Assistant")
    print("=" * 40)
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Setup signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Import and initialize the application controller
        from src.core.application_controller import ApplicationController
        
        print("🚀 Initializing Voice Dictation Assistant...")
        logger.info("Starting Voice Dictation Assistant")
        
        # Create and initialize the application controller
        controller = ApplicationController()
        
        print("✅ Application initialized successfully!")
        print("\n📋 Usage Instructions:")
        print("- Press Ctrl+Win+Space to start dictation")
        print("- Speak clearly into your microphone")
        print("- Release the hotkey to process and insert text")
        print("- Press Ctrl+C to exit the application")
        print("\n🎯 Ready for dictation! Press Ctrl+Win+Space to begin...")
        
        # Keep the application running
        try:
            while True:
                # The application runs in the background via hotkeys
                # This loop just keeps the main thread alive
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Shutting down...")
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Please ensure all dependencies are installed:")
        print("pip install -r requirements.txt")
        return 1
        
    except Exception as e:
        print(f"❌ Application startup failed: {e}")
        logger.error(f"Application startup failed: {e}", exc_info=True)
        return 1
    
    finally:
        logger.info("Voice Dictation Assistant shutdown complete")
        print("👋 Goodbye!")

if __name__ == "__main__":
    sys.exit(main()) 
#!/usr/bin/env python3
"""
Final Working Voice Dictation Assistant
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
    """Final working main function"""
    print("🎤 Voice Dictation Assistant (Final Working Version)")
    print("=" * 55)
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Import components
        from src.hotkeys.hotkey_manager import HotkeyManager, HotkeyConfig, HotkeyMode
        
        print("🚀 Initializing Voice Dictation Assistant...")
        logger.info("Starting Voice Dictation Assistant")
        
        # Create hotkey manager with minimal config
        hotkey_config = {
            'default_hotkey': 'window+alt',
            'push_to_talk': True
        }
        
        hotkey_manager = HotkeyManager(hotkey_config)
        
        # Clear any existing hotkeys to avoid conflicts
        hotkey_manager.cleanup()
        
        # Define test callback
        def test_callback():
            print("🎉 HOTKEY DETECTED! Windows key + Alt pressed!")
            print("📝 This would start dictation in the full application")
        
        # Register the hotkey
        primary_config = HotkeyConfig(
            key_combination='window+alt',
            description="Start dictation",
            mode=HotkeyMode.PUSH_TO_TALK,
            callback=test_callback
        )
        
        success = hotkey_manager.register_hotkey(primary_config)
        print(f"✅ Hotkey registration: {'Success' if success else 'Failed'}")
        
        if success:
            # Start hotkey listening
            hotkey_manager.start_listening()
            
            print("✅ Application initialized successfully!")
            print("\n📋 Usage Instructions:")
            print("- Press Windows key + Alt to test hotkey detection")
            print("- Speak clearly into your microphone")
            print("- Release the hotkey to process and insert text")
            print("- Press Ctrl+C to exit the application")
            print("\n🎯 Ready for testing! Press Windows key + Alt to test...")
            
            # Keep running
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n🛑 Shutting down...")
                hotkey_manager.stop_listening()
        else:
            print("❌ Hotkey registration failed!")
            
    except Exception as e:
        print(f"❌ Application startup failed: {e}")
        logger.error(f"Application startup failed: {e}", exc_info=True)
        return 1
    
    finally:
        logger.info("Voice Dictation Assistant shutdown complete")
        print("👋 Goodbye!")

if __name__ == "__main__":
    sys.exit(main()) 
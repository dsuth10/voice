#!/usr/bin/env python3
"""
Test Hotkey Only
Minimal test to verify hotkey registration works
"""

import time
import logging
from pathlib import Path

def test_hotkey_only():
    """Test just the hotkey functionality"""
    print("🎯 Testing Hotkey Registration")
    print("=" * 40)
    
    try:
        # Import hotkey manager
        from src.hotkeys.hotkey_manager import HotkeyManager, HotkeyConfig, HotkeyMode
        
        # Create simple config
        config = {
            'default_hotkey': 'control+alt+t',
            'push_to_talk': True
        }
        
        # Create hotkey manager
        hotkey_manager = HotkeyManager(config)
        
        # Clear any existing hotkeys
        hotkey_manager.cleanup()
        
        # Test callback
        def test_callback():
            print("🎉 HOTKEY PRESSED! Ctrl+Alt+T detected!")
        
        # Register hotkey
        hotkey_config = HotkeyConfig(
            key_combination='control+alt+t',
            description="Test hotkey",
            mode=HotkeyMode.PUSH_TO_TALK,
            callback=test_callback
        )
        
        success = hotkey_manager.register_hotkey(hotkey_config)
        print(f"✅ Hotkey registration: {'Success' if success else 'Failed'}")
        
        if success:
            print("🎧 Starting hotkey listener...")
            print("📋 Press Ctrl+Alt+T to test")
            print("📋 Press Ctrl+C to exit")
            
            # Start listening
            hotkey_manager.start_listening()
            
            # Keep running
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n🛑 Stopping hotkey listener...")
                hotkey_manager.stop_listening()
                print("✅ Hotkey test completed!")
        else:
            print("❌ Hotkey registration failed!")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    test_hotkey_only() 
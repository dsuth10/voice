#!/usr/bin/env python3
"""
Simple Hotkey Test
Test global-hotkeys library directly
"""

import time
import global_hotkeys

def test_simple_hotkey():
    """Test hotkey registration directly"""
    print("🎯 Simple Hotkey Test")
    print("=" * 30)
    
    def on_hotkey():
        print("🎉 HOTKEY PRESSED! Ctrl+Alt+T detected!")
    
    try:
        # Register hotkey directly
        print("📋 Registering Ctrl+Alt+T hotkey...")
        key_id = global_hotkeys.register_hotkey(
            "control+alt+t",
            on_hotkey,  # press_callback
            on_hotkey,  # release_callback
            actuate_on_partial_release=False
        )
        
        print(f"✅ Hotkey registered with ID: {key_id}")
        print("🎧 Starting hotkey listener...")
        print("📋 Press Ctrl+Alt+T to test")
        print("📋 Press Ctrl+C to exit")
        
        # Start listening
        global_hotkeys.start_checking_hotkeys()
        
        # Keep running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Stopping hotkey listener...")
            global_hotkeys.stop_checking_hotkeys()
            global_hotkeys.remove_hotkey(key_id)
            print("✅ Hotkey test completed!")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    test_simple_hotkey() 
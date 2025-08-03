#!/usr/bin/env python3
"""
Test Windows Key + Alt Hotkey
"""

import time
import global_hotkeys

def test_win_alt():
    """Test Windows key + Alt hotkey"""
    print("🎯 Testing Windows Key + Alt Hotkey")
    print("=" * 40)
    
    def on_hotkey():
        print("🎉 HOTKEY DETECTED! Windows key + Alt pressed!")
        print("📝 This would start dictation in the full application")
    
    try:
        # Register hotkey directly
        print("📋 Registering Windows key + Alt hotkey...")
        key_id = global_hotkeys.register_hotkey(
            "window+alt",
            on_hotkey,  # press_callback
            on_hotkey,  # release_callback
            actuate_on_partial_release=False
        )
        
        print(f"✅ Hotkey registered with ID: {key_id}")
        print("🎧 Starting hotkey listener...")
        print("📋 Press Windows key + Alt to test")
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
    test_win_alt() 
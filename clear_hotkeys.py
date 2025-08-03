#!/usr/bin/env python3
"""
Script to clear existing hotkey registrations before starting the application.
This helps resolve the "hotkey already registered" issue.
"""

import sys
import logging
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

def clear_hotkeys():
    """Clear existing hotkey registrations."""
    print("🔧 Clearing existing hotkey registrations...")
    
    try:
        # Try to import and use the hotkey manager to clear registrations
        from hotkeys.hotkey_manager import HotkeyManager
        
        # Create a temporary hotkey manager to unregister all hotkeys
        temp_manager = HotkeyManager()
        temp_manager.unregister_all()
        temp_manager.cleanup()
        
        print("✅ Hotkey registrations cleared successfully")
        return True
        
    except Exception as e:
        print(f"❌ Failed to clear hotkeys: {e}")
        return False

def clear_global_hotkeys():
    """Clear global hotkey registrations using the library directly."""
    print("🔧 Clearing global hotkey registrations...")
    
    try:
        import global_hotkeys
        
        # Stop any running hotkey listeners
        global_hotkeys.stop_checking_hotkeys()
        
        # Clear all registered hotkeys
        # Note: global_hotkeys doesn't have a direct "clear all" method
        # So we'll just stop the listener
        
        print("✅ Global hotkey listener stopped")
        return True
        
    except Exception as e:
        print(f"❌ Failed to clear global hotkeys: {e}")
        return False

def main():
    """Main function to clear hotkeys."""
    print("🚀 Voice Dictation Assistant - Hotkey Cleanup")
    print("=" * 50)
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Clear hotkeys using our manager
    success1 = clear_hotkeys()
    
    # Clear global hotkeys directly
    success2 = clear_global_hotkeys()
    
    if success1 or success2:
        print("\n✅ Hotkey cleanup completed!")
        print("You can now start the Voice Dictation Assistant without hotkey conflicts.")
    else:
        print("\n⚠️  Hotkey cleanup had issues.")
        print("You may need to restart your computer to clear all hotkey registrations.")
    
    print("\nTo start the application, run:")
    print("python run_voice_assistant.py")

if __name__ == "__main__":
    main() 
"""
Example Usage of the Complete Hotkey System

This module demonstrates how to use the EnhancedHotkeyManager with all its features:
- Push-to-talk functionality
- Conflict detection
- Visual and audio feedback
- Security compatibility
- Error handling
"""

import logging
import time
from typing import Callable
from .enhanced_hotkey_manager import EnhancedHotkeyManager
from .feedback_system import FeedbackType


def setup_logging():
    """Set up logging for the example."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def recording_start_callback():
    """Callback function for when recording starts."""
    print("🎤 Recording started!")
    # In a real application, you would start audio capture here


def recording_stop_callback():
    """Callback function for when recording stops."""
    print("⏹️ Recording stopped!")
    # In a real application, you would stop audio capture and process the audio here


def cancel_recording_callback():
    """Callback function for canceling recording."""
    print("❌ Recording canceled!")
    # In a real application, you would cancel the current recording


def undo_last_insertion_callback():
    """Callback function for undoing the last insertion."""
    print("↶ Undoing last insertion!")
    # In a real application, you would undo the last text insertion


def system_tray_callback(state: str, config: dict):
    """Callback function for system tray updates."""
    print(f"🖥️ System tray updated: {state} ({config})")
    # In a real application, you would update the system tray icon here


def audio_device_callback(frequency: int, duration: int):
    """Callback function for custom audio output."""
    print(f"🔊 Custom audio: {frequency}Hz for {duration}ms")
    # In a real application, you would use a custom audio library here


def main():
    """Main example function demonstrating the hotkey system."""
    setup_logging()
    
    print("🚀 Voice Dictation Assistant - Hotkey System Example")
    print("=" * 60)
    
    # Configuration for the hotkey manager
    config = {
        'default_hotkey': 'ctrl+win+space',
        'push_to_talk': True,
        'min_hold_time': 0.1,
        'max_hold_time': 30.0,
        'visual_feedback': True,
        'audio_feedback': True
    }
    
    # Create the enhanced hotkey manager
    print("\n📋 Creating EnhancedHotkeyManager...")
    hotkey_manager = EnhancedHotkeyManager(config)
    
    # Check security compatibility
    print("\n🔒 Checking security compatibility...")
    compatible, issues = hotkey_manager.check_security_compatibility()
    if compatible:
        print("✅ Security compatibility check passed")
    else:
        print("❌ Security compatibility issues found:")
        for issue in issues:
            print(f"   - {issue}")
    
    # Get security recommendations
    print("\n📋 Security recommendations:")
    recommendations = hotkey_manager.get_security_recommendations()
    for rec in recommendations[:3]:  # Show first 3 recommendations
        print(f"   - {rec}")
    
    # Set up callbacks
    print("\n🔗 Setting up callbacks...")
    hotkey_manager.set_system_tray_callback(system_tray_callback)
    hotkey_manager.set_audio_device_callback(audio_device_callback)
    
    # Register push-to-talk hotkey
    print("\n🎤 Registering push-to-talk hotkey...")
    success, message = hotkey_manager.register_push_to_talk_hotkey(
        'ctrl+win+space',
        recording_start_callback,
        recording_stop_callback
    )
    
    if success:
        print(f"✅ {message}")
    else:
        print(f"❌ {message}")
        # Try alternative hotkey
        print("🔄 Trying alternative hotkey...")
        success, message = hotkey_manager.register_push_to_talk_hotkey(
            'ctrl+win+r',
            recording_start_callback,
            recording_stop_callback
        )
        if success:
            print(f"✅ {message}")
        else:
            print(f"❌ {message}")
    
    # Register toggle hotkeys
    print("\n🎛️ Registering toggle hotkeys...")
    
    success, message = hotkey_manager.register_toggle_hotkey(
        'ctrl+win+c',
        cancel_recording_callback,
        "Cancel Current Recording"
    )
    print(f"{'✅' if success else '❌'} Cancel hotkey: {message}")
    
    success, message = hotkey_manager.register_toggle_hotkey(
        'ctrl+win+z',
        undo_last_insertion_callback,
        "Undo Last Insertion"
    )
    print(f"{'✅' if success else '❌'} Undo hotkey: {message}")
    
    # Check for conflicts
    print("\n🔍 Checking for conflicts...")
    hotkeys_to_check = ['ctrl+win+space', 'ctrl+win+c', 'ctrl+win+z']
    conflicts = hotkey_manager.check_hotkey_conflicts(hotkeys_to_check)
    
    for hotkey, conflict_info in conflicts.items():
        if conflict_info.level.value != 'none':
            print(f"⚠️  {hotkey}: {conflict_info.description}")
        else:
            print(f"✅ {hotkey}: No conflicts")
    
    # Get safe hotkey suggestions
    print("\n💡 Safe hotkey suggestions:")
    safe_hotkeys = hotkey_manager.get_safe_hotkeys(5)
    for hotkey in safe_hotkeys:
        print(f"   - {hotkey}")
    
    # Start listening for hotkeys
    print("\n🎧 Starting hotkey listener...")
    hotkey_manager.start_listening()
    
    # Demonstrate feedback system
    print("\n🔊 Testing feedback system...")
    feedback_system = hotkey_manager.get_feedback_system()
    
    # Test different feedback types
    feedback_system.provide_feedback('recording_start', FeedbackType.AUDIO)
    time.sleep(0.5)
    feedback_system.provide_feedback('recording_stop', FeedbackType.AUDIO)
    time.sleep(0.5)
    feedback_system.provide_feedback('success', FeedbackType.BOTH)
    
    # Show current state
    print(f"\n📊 Current visual state: {feedback_system.get_current_visual_state()}")
    
    # Interactive demonstration
    print("\n🎯 Interactive demonstration:")
    print("Press the registered hotkeys to test them:")
    print("   - Ctrl+Win+Space: Start/Stop recording (push-to-talk)")
    print("   - Ctrl+Win+C: Cancel recording")
    print("   - Ctrl+Win+Z: Undo last insertion")
    print("\nPress Ctrl+C to exit...")
    
    try:
        # Keep the program running to test hotkeys
        while True:
            time.sleep(1)
            
            # Check if any hotkey is currently recording
            if hotkey_manager.is_recording():
                print("🎤 Currently recording...")
            
    except KeyboardInterrupt:
        print("\n⏹️ Stopping hotkey system...")
    
    finally:
        # Clean up
        print("🧹 Cleaning up...")
        hotkey_manager.cleanup()
        print("✅ Hotkey system stopped successfully")


def test_conflict_detection():
    """Test the conflict detection system."""
    print("\n🔍 Testing conflict detection...")
    
    from .conflict_detector import HotkeyConflictDetector
    
    detector = HotkeyConflictDetector()
    
    # Test various hotkeys
    test_hotkeys = [
        'ctrl+win+space',
        'win+r',  # Should conflict with Run dialog
        'ctrl+c',  # Should conflict with Copy
        'alt+tab',  # Should conflict with Switch Windows
        'ctrl+win+x'  # Should be safe
    ]
    
    for hotkey in test_hotkeys:
        conflict_info = detector.check_conflict(hotkey)
        print(f"{hotkey}: {conflict_info.description}")
        if conflict_info.suggested_alternatives:
            print(f"   Alternatives: {', '.join(conflict_info.suggested_alternatives[:2])}")


def test_security_compatibility():
    """Test the security compatibility system."""
    print("\n🔒 Testing security compatibility...")
    
    from .security_compatibility import WindowsSecurityCompatibility
    
    security = WindowsSecurityCompatibility()
    
    # Check current permissions
    current_perms = security.check_current_permissions()
    print(f"Current security level: {current_perms.level.value}")
    print(f"Description: {current_perms.description}")
    print(f"Requires elevation: {current_perms.requires_elevation}")
    
    # Check operation permissions
    operations = ['global_hotkey_registration', 'system_tray_access', 'audio_device_access']
    
    for operation in operations:
        has_perms, security_info = security.check_operation_permissions(operation)
        print(f"{operation}: {'✅' if has_perms else '❌'} {security_info.description}")
    
    # Get recommendations
    print("\n📋 Security recommendations:")
    recommendations = security.get_security_recommendations()
    for rec in recommendations[:3]:
        print(f"   - {rec}")


if __name__ == "__main__":
    print("🎯 Hotkey System Example")
    print("=" * 40)
    
    # Run tests
    test_conflict_detection()
    test_security_compatibility()
    
    # Run main example
    main() 
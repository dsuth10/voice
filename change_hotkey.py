#!/usr/bin/env python3
"""
Change Hotkey Script
Modifies only the hotkey configuration to Windows key + Alt key
"""

import yaml
from pathlib import Path

def change_hotkey():
    """Change the hotkey to Windows key + Alt key"""
    print("🔧 Changing hotkey to Windows key + Alt key...")
    
    # Configuration file path
    config_file = Path.home() / "AppData" / "Roaming" / "VoiceDictationAssistant" / "config.yaml"
    
    if not config_file.exists():
        print("❌ Configuration file not found. Please run the application first to create it.")
        return
    
    try:
        # Load current configuration
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f) or {}
        
        # Update only the hotkey
        if 'hotkeys' not in config_data:
            config_data['hotkeys'] = {}
        
        config_data['hotkeys']['primary'] = 'win+alt'
        
        # Save the updated configuration
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f, default_flow_style=False, indent=2)
        
        print("✅ Hotkey changed successfully!")
        print("📋 New hotkey: Windows key + Alt key")
        print("🎯 Restart the application for changes to take effect.")
        
    except Exception as e:
        print(f"❌ Error changing hotkey: {e}")

if __name__ == "__main__":
    change_hotkey() 
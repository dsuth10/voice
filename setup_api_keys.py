#!/usr/bin/env python3
"""
Simple API Key Setup Script
Bypasses secure storage issues and sets up API keys directly
"""

import os
import yaml
from pathlib import Path

def setup_api_keys():
    """Setup API keys with a simple approach"""
    print("🔑 Voice Dictation Assistant - API Key Setup")
    print("=" * 50)
    
    # Get API keys from user
    print("\n📝 Please enter your API keys:")
    print("\n--- OpenAI API Key ---")
    print("Get your key from: https://platform.openai.com/api-keys")
    openai_key = input("Enter your OpenAI API key: ").strip()
    
    print("\n--- AssemblyAI API Key ---")
    print("Get your key from: https://www.assemblyai.com/app/account")
    assemblyai_key = input("Enter your AssemblyAI API key: ").strip()
    
    # Create configuration directory
    config_dir = Path.home() / "AppData" / "Roaming" / "VoiceDictationAssistant"
    config_dir.mkdir(parents=True, exist_ok=True)
    
    # Create basic configuration
    config_data = {
        'audio': {
            'sample_rate': 16000,
            'channels': 1,
            'chunk_size': 1024,
            'silence_threshold': 0.01,
            'silence_duration': 1.0
        },
        'ai': {
            'model': 'gpt-4o-mini',
            'remove_fillers': True,
            'improve_grammar': True,
            'context_aware': True
        },
        'hotkeys': {
            'primary': 'ctrl+win+space',
            'cancel': 'ctrl+win+c',
            'undo': 'ctrl+win+z',
            'push_to_talk': True
        },
        'ui': {
            'feedback_type': 'both',
            'show_notifications': True
        },
        'performance': {
            'monitoring_interval': 1.0
        },
        'api_keys': {
            'openai': openai_key if openai_key else None,
            'assemblyai': assemblyai_key if assemblyai_key else None
        }
    }
    
    # Save configuration
    config_file = config_dir / "config.yaml"
    with open(config_file, 'w', encoding='utf-8') as f:
        yaml.dump(config_data, f, default_flow_style=False, indent=2)
    
    print(f"\n✅ Configuration saved to: {config_file}")
    print("\n📋 API Key Status:")
    print(f"OpenAI: {'✅ Configured' if openai_key else '❌ Missing'}")
    print(f"AssemblyAI: {'✅ Configured' if assemblyai_key else '❌ Missing'}")
    
    if openai_key and assemblyai_key:
        print("\n🎉 Setup complete! You can now run the application.")
        print("Run: python run_voice_assistant.py")
    else:
        print("\n⚠️  Some API keys are missing. The application may not work fully.")
        print("You can run this script again to add missing keys.")

if __name__ == "__main__":
    setup_api_keys() 
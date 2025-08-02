#!/usr/bin/env python3
"""
Setup Test Configuration
Creates a basic configuration for testing the voice dictation assistant
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def setup_test_config():
    """Setup basic test configuration"""
    print("🔧 Setting up test configuration...")
    
    try:
        from config.config_manager import ConfigManager
        
        # Create a basic configuration
        config_data = {
            'audio': {
                'sample_rate': 16000,
                'channels': 1,
                'chunk_size': 1024,
                'silence_threshold': 0.01
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
            'api_keys': {
                'assemblyai': 'test_key_assemblyai',
                'openai': 'test_key_openai'
            }
        }
        
        # Initialize config manager
        config = ConfigManager()
        
        # Set test configuration
        for key, value in config_data.items():
            config.set(key, value)
        
        print("✅ Test configuration created successfully!")
        print("📝 Note: Using test API keys - replace with real keys for full functionality")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to setup test configuration: {e}")
        return False

if __name__ == "__main__":
    setup_test_config() 
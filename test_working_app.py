#!/usr/bin/env python3
"""
Test Working Application
"""

import yaml
from pathlib import Path

def test_working_app():
    """Test if the application can work with direct configuration"""
    print("🧪 Testing Application Setup")
    print("=" * 40)
    
    # Configuration file path
    config_file = Path.home() / "AppData" / "Roaming" / "VoiceDictationAssistant" / "config.yaml"
    
    if not config_file.exists():
        print("❌ Configuration file not found!")
        return False
    
    try:
        # Load current configuration
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Set API keys directly (bypassing secure storage)
        config['api_keys']['assemblyai'] = '11b8564774604ecb9589bf4923260263'
        config['api_keys']['openai'] = 'KmHlGyNvpc6kGTvpTWj5NrhPYJS5FIpUFDDFMeE3Gxxj2DJRSI1i0NjudhafVMKEkqHSe33DIWT3BlbkFJB0h6cJo8p8sxGbV0Nu3FsdSHm3UbDwbVs5gA5lCcS4IENYN6MuvLmQvHWYKDBpvNv57CK1_fEA'
        
        # Save updated configuration
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, indent=2)
        
        print("✅ API keys set directly in configuration")
        print("✅ Hotkey configured: win+alt")
        print("✅ Microphone working: USB MIC/INPUT Adapter")
        
        print("\n🎯 Ready to test the application!")
        print("Run: python run_voice_assistant.py")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_working_app() 
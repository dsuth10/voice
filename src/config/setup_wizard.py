"""
Setup wizard for Voice Dictation Assistant.
Guides users through initial configuration and API key setup.
"""

import logging
import getpass
from typing import Optional, Dict, Any
from pathlib import Path

from .config_manager import ConfigManager
from .secure_storage import SecureStorage


class SetupWizard:
    """Setup wizard for first-time configuration."""
    
    def __init__(self, config_manager: ConfigManager):
        """
        Initialize setup wizard.
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config_manager = config_manager
        self.secure_storage = SecureStorage()
        self.logger = logging.getLogger(__name__)
    
    def run_setup(self) -> bool:
        """
        Run the complete setup wizard.
        
        Returns:
            True if setup completed successfully, False otherwise
        """
        try:
            print("\n" + "="*60)
            print("Voice Dictation Assistant - Setup Wizard")
            print("="*60)
            
            # Test secure storage
            if not self._test_secure_storage():
                print("❌ Secure storage test failed. Setup cannot continue.")
                return False
            
            # API Keys setup
            if not self._setup_api_keys():
                print("❌ API key setup failed.")
                return False
            
            # Audio settings
            if not self._setup_audio_settings():
                print("❌ Audio settings setup failed.")
                return False
            
            # Hotkey settings
            if not self._setup_hotkey_settings():
                print("❌ Hotkey settings setup failed.")
                return False
            
            # AI settings
            if not self._setup_ai_settings():
                print("❌ AI settings setup failed.")
                return False
            
            # UI settings
            if not self._setup_ui_settings():
                print("❌ UI settings setup failed.")
                return False
            
            # Save configuration
            if self.config_manager._save_config():
                print("\n✅ Setup completed successfully!")
                print(f"Configuration saved to: {self.config_manager.config_file}")
                return True
            else:
                print("❌ Failed to save configuration.")
                return False
                
        except Exception as e:
            self.logger.error(f"Setup wizard failed: {e}")
            print(f"❌ Setup failed: {e}")
            return False
    
    def _test_secure_storage(self) -> bool:
        """
        Test secure storage functionality.
        
        Returns:
            True if test passes, False otherwise
        """
        print("\n🔐 Testing secure storage...")
        
        try:
            if not self.secure_storage.is_dpapi_available():
                print("❌ Windows DPAPI not available on this system.")
                return False
            
            if not self.secure_storage.test_encryption():
                print("❌ Secure storage encryption test failed.")
                return False
            
            print("✅ Secure storage test passed.")
            return True
            
        except Exception as e:
            self.logger.error(f"Secure storage test failed: {e}")
            print(f"❌ Secure storage test failed: {e}")
            return False
    
    def _setup_api_keys(self) -> bool:
        """
        Setup API keys for external services.
        
        Returns:
            True if setup successful, False otherwise
        """
        print("\n🔑 Setting up API Keys...")
        print("You'll need API keys for speech recognition and AI enhancement.")
        
        # OpenAI API Key
        print("\n--- OpenAI API Key ---")
        print("Required for AI text enhancement.")
        print("Get your key from: https://platform.openai.com/api-keys")
        
        openai_key = self._get_api_key_input("OpenAI")
        if openai_key:
            if not self.config_manager.set_api_key("openai", openai_key):
                print("❌ Failed to save OpenAI API key.")
                return False
            print("✅ OpenAI API key saved securely.")
        else:
            print("⚠️  OpenAI API key not provided. AI enhancement will be disabled.")
        
        # AssemblyAI API Key
        print("\n--- AssemblyAI API Key ---")
        print("Required for speech recognition.")
        print("Get your key from: https://www.assemblyai.com/app/account")
        
        assemblyai_key = self._get_api_key_input("AssemblyAI")
        if assemblyai_key:
            if not self.config_manager.set_api_key("assemblyai", assemblyai_key):
                print("❌ Failed to save AssemblyAI API key.")
                return False
            print("✅ AssemblyAI API key saved securely.")
        else:
            print("⚠️  AssemblyAI API key not provided. Speech recognition will be disabled.")
        
        return True
    
    def _setup_audio_settings(self) -> bool:
        """
        Setup audio capture settings.
        
        Returns:
            True if setup successful, False otherwise
        """
        print("\n🎤 Setting up Audio Settings...")
        
        # Sample rate
        print("\n--- Sample Rate ---")
        print("Higher sample rates provide better quality but use more bandwidth.")
        sample_rate = self._get_choice_input(
            "Select sample rate:",
            ["16000 Hz (Recommended)", "8000 Hz (Low bandwidth)", "44100 Hz (High quality)"],
            default=0
        )
        
        sample_rates = [16000, 8000, 44100]
        self.config_manager.set("audio.sample_rate", sample_rates[sample_rate])
        
        # Channels
        print("\n--- Audio Channels ---")
        channels = self._get_choice_input(
            "Select audio channels:",
            ["Mono (Recommended)", "Stereo"],
            default=0
        )
        
        channel_counts = [1, 2]
        self.config_manager.set("audio.channels", channel_counts[channels])
        
        # Silence detection
        print("\n--- Silence Detection ---")
        print("Configure when to stop recording during silence.")
        
        silence_threshold = self._get_float_input(
            "Silence threshold (0.0-1.0, default 0.01):",
            default=0.01,
            min_val=0.0,
            max_val=1.0
        )
        self.config_manager.set("audio.silence_threshold", silence_threshold)
        
        silence_duration = self._get_float_input(
            "Silence duration to stop recording (seconds, default 1.0):",
            default=1.0,
            min_val=0.1,
            max_val=10.0
        )
        self.config_manager.set("audio.silence_duration", silence_duration)
        
        print("✅ Audio settings configured.")
        return True
    
    def _setup_hotkey_settings(self) -> bool:
        """
        Setup hotkey settings.
        
        Returns:
            True if setup successful, False otherwise
        """
        print("\n⌨️  Setting up Hotkey Settings...")
        
        # Primary hotkey
        print("\n--- Primary Hotkey ---")
        print("This hotkey will activate voice recording.")
        print("Format: ctrl+alt+key or ctrl+win+key")
        
        hotkey = self._get_input(
            "Primary hotkey (default: ctrl+win+space):",
            default="ctrl+win+space"
        )
        self.config_manager.set("hotkey.primary_hotkey", hotkey)
        
        # Push to talk
        print("\n--- Push to Talk ---")
        push_to_talk = self._get_yes_no_input(
            "Enable push-to-talk mode (hold hotkey to record)?",
            default=True
        )
        self.config_manager.set("hotkey.push_to_talk", push_to_talk)
        
        # Global hotkeys
        print("\n--- Global Hotkeys ---")
        global_hotkeys = self._get_yes_no_input(
            "Enable global hotkey detection (works in all applications)?",
            default=True
        )
        self.config_manager.set("hotkey.global_hotkeys_enabled", global_hotkeys)
        
        print("✅ Hotkey settings configured.")
        return True
    
    def _setup_ai_settings(self) -> bool:
        """
        Setup AI enhancement settings.
        
        Returns:
            True if setup successful, False otherwise
        """
        print("\n🤖 Setting up AI Enhancement Settings...")
        
        # AI model
        print("\n--- AI Model ---")
        model = self._get_choice_input(
            "Select AI model for text enhancement:",
            ["gpt-4o-mini (Recommended)", "gpt-3.5-turbo (Faster)", "gpt-4o (Best quality)"],
            default=0
        )
        
        models = ["gpt-4o-mini", "gpt-3.5-turbo", "gpt-4o"]
        self.config_manager.set("ai.model", models[model])
        
        # Enhancement options
        print("\n--- Enhancement Options ---")
        
        remove_fillers = self._get_yes_no_input(
            "Remove filler words (um, uh, like)?",
            default=True
        )
        self.config_manager.set("ai.remove_fillers", remove_fillers)
        
        improve_grammar = self._get_yes_no_input(
            "Improve grammar and punctuation?",
            default=True
        )
        self.config_manager.set("ai.improve_grammar", improve_grammar)
        
        enhance_clarity = self._get_yes_no_input(
            "Enhance text clarity and flow?",
            default=True
        )
        self.config_manager.set("ai.enhance_clarity", enhance_clarity)
        
        # Temperature
        print("\n--- AI Creativity ---")
        temperature = self._get_float_input(
            "AI creativity level (0.0-2.0, default 0.3):",
            default=0.3,
            min_val=0.0,
            max_val=2.0
        )
        self.config_manager.set("ai.temperature", temperature)
        
        print("✅ AI settings configured.")
        return True
    
    def _setup_ui_settings(self) -> bool:
        """
        Setup user interface settings.
        
        Returns:
            True if setup successful, False otherwise
        """
        print("\n🖥️  Setting up UI Settings...")
        
        # Notifications
        print("\n--- Notifications ---")
        show_notifications = self._get_yes_no_input(
            "Show system notifications?",
            default=True
        )
        self.config_manager.set("ui.show_notifications", show_notifications)
        
        if show_notifications:
            duration = self._get_int_input(
                "Notification duration (seconds, default 3):",
                default=3,
                min_val=1,
                max_val=10
            )
            self.config_manager.set("ui.notification_duration", duration)
        
        # Dark mode
        print("\n--- Appearance ---")
        dark_mode = self._get_yes_no_input(
            "Enable dark mode interface?",
            default=False
        )
        self.config_manager.set("ui.dark_mode", dark_mode)
        
        # Auto-start
        print("\n--- Auto-start ---")
        auto_start = self._get_yes_no_input(
            "Start application on Windows startup?",
            default=False
        )
        self.config_manager.set("ui.auto_start", auto_start)
        
        print("✅ UI settings configured.")
        return True
    
    def _get_api_key_input(self, service: str) -> Optional[str]:
        """
        Get API key input from user.
        
        Args:
            service: Service name
            
        Returns:
            API key or None if skipped
        """
        while True:
            choice = input(f"\nEnter {service} API key (or press Enter to skip): ").strip()
            
            if not choice:
                return None
            
            # Basic validation
            if len(choice) < 10:
                print("❌ API key appears to be too short. Please check and try again.")
                continue
            
            if service.lower() == "openai" and not choice.startswith("sk-"):
                print("❌ OpenAI API key should start with 'sk-'. Please check and try again.")
                continue
            
            # Confirm the key
            confirm = input("Please confirm the API key (enter again): ").strip()
            if choice == confirm:
                return choice
            else:
                print("❌ Keys don't match. Please try again.")
    
    def _get_choice_input(self, prompt: str, options: list, default: int = 0) -> int:
        """
        Get choice input from user.
        
        Args:
            prompt: Prompt text
            options: List of options
            default: Default choice index
            
        Returns:
            Selected choice index
        """
        print(f"\n{prompt}")
        for i, option in enumerate(options):
            marker = "→" if i == default else " "
            print(f"  {marker} {i+1}. {option}")
        
        while True:
            try:
                choice = input(f"\nEnter choice (1-{len(options)}, default {default+1}): ").strip()
                
                if not choice:
                    return default
                
                choice_idx = int(choice) - 1
                if 0 <= choice_idx < len(options):
                    return choice_idx
                else:
                    print(f"❌ Please enter a number between 1 and {len(options)}.")
                    
            except ValueError:
                print("❌ Please enter a valid number.")
    
    def _get_yes_no_input(self, prompt: str, default: bool = True) -> bool:
        """
        Get yes/no input from user.
        
        Args:
            prompt: Prompt text
            default: Default value
            
        Returns:
            True for yes, False for no
        """
        default_text = "Y/n" if default else "y/N"
        while True:
            choice = input(f"{prompt} ({default_text}): ").strip().lower()
            
            if not choice:
                return default
            
            if choice in ['y', 'yes']:
                return True
            elif choice in ['n', 'no']:
                return False
            else:
                print("❌ Please enter 'y' or 'n'.")
    
    def _get_input(self, prompt: str, default: str = "") -> str:
        """
        Get text input from user.
        
        Args:
            prompt: Prompt text
            default: Default value
            
        Returns:
            User input or default
        """
        if default:
            choice = input(f"{prompt} (default: {default}): ").strip()
            return choice if choice else default
        else:
            return input(f"{prompt}: ").strip()
    
    def _get_int_input(self, prompt: str, default: int, min_val: int = None, max_val: int = None) -> int:
        """
        Get integer input from user.
        
        Args:
            prompt: Prompt text
            default: Default value
            min_val: Minimum allowed value
            max_val: Maximum allowed value
            
        Returns:
            Integer value
        """
        while True:
            try:
                choice = input(f"{prompt} (default: {default}): ").strip()
                
                if not choice:
                    return default
                
                value = int(choice)
                
                if min_val is not None and value < min_val:
                    print(f"❌ Value must be at least {min_val}.")
                    continue
                
                if max_val is not None and value > max_val:
                    print(f"❌ Value must be at most {max_val}.")
                    continue
                
                return value
                
            except ValueError:
                print("❌ Please enter a valid number.")
    
    def _get_float_input(self, prompt: str, default: float, min_val: float = None, max_val: float = None) -> float:
        """
        Get float input from user.
        
        Args:
            prompt: Prompt text
            default: Default value
            min_val: Minimum allowed value
            max_val: Maximum allowed value
            
        Returns:
            Float value
        """
        while True:
            try:
                choice = input(f"{prompt} (default: {default}): ").strip()
                
                if not choice:
                    return default
                
                value = float(choice)
                
                if min_val is not None and value < min_val:
                    print(f"❌ Value must be at least {min_val}.")
                    continue
                
                if max_val is not None and value > max_val:
                    print(f"❌ Value must be at most {max_val}.")
                    continue
                
                return value
                
            except ValueError:
                print("❌ Please enter a valid number.")
    
    def validate_setup(self) -> Dict[str, Any]:
        """
        Validate the current setup configuration.
        
        Returns:
            Dictionary with validation results
        """
        results = {
            "secure_storage": self.secure_storage.test_encryption(),
            "api_keys": {
                "openai": bool(self.config_manager.get_api_key("openai")),
                "assemblyai": bool(self.config_manager.get_api_key("assemblyai"))
            },
            "configuration": self.config_manager.validate_configuration()
        }
        
        return results 
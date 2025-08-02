"""
Configuration schema and validation for Voice Dictation Assistant.
Defines the structure and validation rules for all configuration options.
"""

from typing import Dict, Optional, List
from pydantic import BaseModel, Field, validator
import os


class AudioConfig(BaseModel):
    """Audio capture and processing settings."""
    sample_rate: int = Field(default=16000, ge=8000, le=48000, description="Audio sample rate in Hz")
    channels: int = Field(default=1, ge=1, le=2, description="Number of audio channels")
    chunk_size: int = Field(default=1024, ge=512, le=8192, description="Audio chunk size for processing")
    device_name: Optional[str] = Field(default=None, description="Preferred audio input device")
    silence_threshold: float = Field(default=0.01, ge=0.0, le=1.0, description="Silence detection threshold")
    silence_duration: float = Field(default=1.0, ge=0.1, le=10.0, description="Silence duration to stop recording (seconds)")


class AIConfig(BaseModel):
    """AI processing and enhancement settings."""
    model: str = Field(default="gpt-4o-mini", description="OpenAI model for text enhancement")
    remove_fillers: bool = Field(default=True, description="Remove filler words from speech")
    improve_grammar: bool = Field(default=True, description="Improve grammar and punctuation")
    enhance_clarity: bool = Field(default=True, description="Enhance text clarity and flow")
    max_tokens: int = Field(default=1000, ge=100, le=4000, description="Maximum tokens for AI processing")
    temperature: float = Field(default=0.3, ge=0.0, le=2.0, description="AI response creativity (0=deterministic, 2=creative)")


class HotkeyConfig(BaseModel):
    """Hotkey and input settings."""
    primary_hotkey: str = Field(default="ctrl+win+space", description="Primary hotkey for voice activation")
    push_to_talk: bool = Field(default=True, description="Enable push-to-talk mode")
    secondary_hotkey: Optional[str] = Field(default=None, description="Secondary hotkey for alternative functions")
    global_hotkeys_enabled: bool = Field(default=True, description="Enable global hotkey detection")


class APIKeysConfig(BaseModel):
    """API keys for external services (encrypted storage)."""
    assemblyai: str = Field(default="", description="AssemblyAI API key")
    openai: str = Field(default="", description="OpenAI API key")
    
    @validator('assemblyai', 'openai')
    def validate_api_key_format(cls, v):
        """Validate API key format (basic check for non-empty and reasonable length)."""
        if v and len(v) < 10:
            raise ValueError("API key appears to be too short")
        return v


class UIConfig(BaseModel):
    """User interface and display settings."""
    show_notifications: bool = Field(default=True, description="Show system notifications")
    notification_duration: int = Field(default=3, ge=1, le=10, description="Notification display duration (seconds)")
    dark_mode: bool = Field(default=False, description="Enable dark mode interface")
    minimize_to_tray: bool = Field(default=True, description="Minimize to system tray")
    auto_start: bool = Field(default=False, description="Start application on Windows startup")


class LoggingConfig(BaseModel):
    """Logging and debugging settings."""
    log_level: str = Field(default="INFO", description="Logging level")
    log_file: Optional[str] = Field(default=None, description="Log file path")
    enable_debug: bool = Field(default=False, description="Enable debug mode")
    max_log_size: int = Field(default=10, ge=1, le=100, description="Maximum log file size in MB")


class ProfileConfig(BaseModel):
    """Configuration profile settings."""
    name: str = Field(description="Profile name")
    description: Optional[str] = Field(default=None, description="Profile description")
    is_default: bool = Field(default=False, description="Whether this is the default profile")
    created_at: Optional[str] = Field(default=None, description="Profile creation timestamp")


class MainConfig(BaseModel):
    """Main configuration structure."""
    version: str = Field(default="1.0.0", description="Configuration version")
    audio: AudioConfig = Field(default_factory=AudioConfig, description="Audio settings")
    ai: AIConfig = Field(default_factory=AIConfig, description="AI processing settings")
    hotkey: HotkeyConfig = Field(default_factory=HotkeyConfig, description="Hotkey settings")
    api_keys: APIKeysConfig = Field(default_factory=APIKeysConfig, description="API keys")
    ui: UIConfig = Field(default_factory=UIConfig, description="User interface settings")
    logging: LoggingConfig = Field(default_factory=LoggingConfig, description="Logging settings")
    current_profile: str = Field(default="default", description="Current active profile")
    profiles: Dict[str, ProfileConfig] = Field(default_factory=dict, description="Available profiles")
    
    class Config:
        """Pydantic configuration."""
        validate_assignment = True
        extra = "forbid"  # Prevent additional fields
    
    @validator('current_profile')
    def validate_current_profile(cls, v, values):
        """Ensure current profile exists in profiles list."""
        profiles = values.get('profiles', {})
        if v not in profiles and profiles:
            raise ValueError(f"Current profile '{v}' not found in available profiles")
        return v
    
    def get_nested_value(self, key: str, default=None):
        """Get a nested configuration value using dot notation."""
        keys = key.split('.')
        value = self.model_dump()
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
    
    def set_nested_value(self, key: str, value):
        """Set a nested configuration value using dot notation."""
        keys = key.split('.')
        config_dict = self.model_dump()
        
        # Navigate to the parent of the target key
        current = config_dict
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        # Set the value
        current[keys[-1]] = value
        
        # Create new instance with updated values
        return MainConfig(**config_dict)


def create_default_config() -> MainConfig:
    """Create a default configuration with sensible defaults."""
    default_profile = ProfileConfig(
        name="default",
        description="Default configuration profile",
        is_default=True,
        created_at="2024-01-01T00:00:00Z"
    )
    
    return MainConfig(
        profiles={"default": default_profile},
        current_profile="default"
    )


def validate_config_file(config_data: dict) -> MainConfig:
    """Validate and create a MainConfig instance from dictionary data."""
    try:
        return MainConfig(**config_data)
    except Exception as e:
        raise ValueError(f"Invalid configuration data: {e}")


def get_config_schema() -> dict:
    """Get the JSON schema for the configuration."""
    return MainConfig.schema() 
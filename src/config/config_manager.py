"""
Configuration manager for Voice Dictation Assistant.
Handles loading, saving, and managing configuration files with secure storage.
"""

import os
import logging
from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime

# PyYAML is an optional dependency.  The execution environment for the kata does
# not provide it which previously resulted in a ``ModuleNotFoundError`` during
# import.  For the purposes of these tests we fall back to the standard library
# ``json`` module which supports the subset of YAML used by the configuration
# files.  The wrapper exposes ``safe_load`` and ``dump`` with a compatible
# interface.
try:  # pragma: no cover - real library used in production
    import yaml  # type: ignore
except Exception:  # pragma: no cover - triggered when PyYAML is unavailable
    import json

    class _YamlStub:
        @staticmethod
        def safe_load(stream):
            return json.load(stream)

        @staticmethod
        def dump(data, stream, default_flow_style=False, indent=2):
            json.dump(data, stream, indent=indent)

    yaml = _YamlStub()  # type: ignore

from .schema import MainConfig, create_default_config, validate_config_file
from .secure_storage import SecureStorage, APIKeyManager


class ConfigManager:
    """Main configuration manager for the application."""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_file: Optional path to configuration file
        """
        self.logger = logging.getLogger(__name__)
        
        # Set up configuration file path
        if config_file:
            self.config_file = Path(config_file)
        else:
            app_data_dir = Path(os.environ.get('APPDATA', os.path.expanduser('~')))
            self.config_file = app_data_dir / 'VoiceDictationAssistant' / 'config.yaml'
        
        # Initialize secure storage
        self.secure_storage = SecureStorage()
        self.api_key_manager = APIKeyManager()
        
        # Load configuration
        self.config = self._load_config()
        
        # Ensure configuration directory exists
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
    
    def _load_config(self) -> MainConfig:
        """
        Load configuration from file or create default.
        
        Returns:
            MainConfig instance
        """
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f) or {}
                
                # Validate configuration data
                config = validate_config_file(config_data)
                self.logger.info(f"Configuration loaded from {self.config_file}")
                return config
                
            except Exception as e:
                self.logger.error(f"Failed to load configuration: {e}")
                self.logger.info("Creating default configuration")
                return self._create_default_config()
        else:
            self.logger.info("No configuration file found, creating default")
            return self._create_default_config()
    
    def _create_default_config(self) -> MainConfig:
        """
        Create and save default configuration.
        
        Returns:
            Default MainConfig instance
        """
        config = create_default_config()
        self._save_config(config)
        return config
    
    def _save_config(self, config: Optional[MainConfig] = None) -> bool:
        """
        Save configuration to file.
        
        Args:
            config: Configuration to save (uses current if None)
            
        Returns:
            True if successful, False otherwise
        """
        if config is not None:
            self.config = config
        
        try:
            # Ensure directory exists
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert to dictionary for YAML serialization
            config_dict = self.config.model_dump()
            
            # Save to file
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config_dict, f, default_flow_style=False, indent=2)
            
            self.logger.info(f"Configuration saved to {self.config_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")
            return False
    
    def get(self, key: str, default=None):
        """
        Get a configuration value using dot notation.
        
        Args:
            key: Configuration key (e.g., 'audio.sample_rate')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        return self.config.get_nested_value(key, default)
    
    def set(self, key: str, value) -> bool:
        """
        Set a configuration value using dot notation.
        
        Args:
            key: Configuration key (e.g., 'audio.sample_rate')
            value: Value to set
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Update configuration
            self.config = self.config.set_nested_value(key, value)
            
            # Save to file
            return self._save_config()
            
        except Exception as e:
            self.logger.error(f"Failed to set configuration key '{key}': {e}")
            return False
    
    def get_api_key(self, service: str) -> str:
        """
        Get an API key securely.
        
        Args:
            service: Service name (e.g., 'openai', 'assemblyai')
            
        Returns:
            Decrypted API key or empty string
        """
        try:
            # Get encrypted key from configuration
            encrypted_key = self.get(f'api_keys.{service}', '')
            
            # Handle empty or None values
            if not encrypted_key:
                self.logger.debug(f"No API key found for service: {service}")
                return ""
            
            # Check if the data appears to be encrypted
            if not self.secure_storage._is_encrypted_data(encrypted_key):
                # If it's not encrypted, it might be stored in plain text
                # (for backward compatibility or if encryption failed)
                self.logger.warning(f"API key for {service} is not encrypted, returning as-is")
                return encrypted_key
            
            # Attempt to decrypt the key
            decrypted_key = self.secure_storage.decrypt_data(encrypted_key)
            
            # Validate the decrypted key
            if decrypted_key and self.api_key_manager.validate_api_key(service, decrypted_key):
                return decrypted_key
            else:
                self.logger.warning(f"Invalid or empty API key for service: {service}")
                return ""
            
        except Exception as e:
            self.logger.error(f"Failed to get API key for {service}: {e}")
            return ""
    
    def set_api_key(self, service: str, api_key: str) -> bool:
        """
        Set an API key securely.
        
        Args:
            service: Service name (e.g., 'openai', 'assemblyai')
            api_key: API key to store
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Handle empty API keys
            if not api_key:
                self.logger.warning(f"Empty API key provided for service: {service}")
                # Remove the key from configuration
                return self.set(f'api_keys.{service}', '')
            
            # Validate API key format
            if not self.api_key_manager.validate_api_key(service, api_key):
                self.logger.error(f"Invalid API key format for {service}")
                return False
            
            # Encrypt the key
            encrypted_key = self.secure_storage.encrypt_data(api_key)
            
            # Store in configuration
            return self.set(f'api_keys.{service}', encrypted_key)
            
        except Exception as e:
            self.logger.error(f"Failed to set API key for {service}: {e}")
            return False
    
    def get_profile(self, profile_name: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific profile configuration.
        
        Args:
            profile_name: Name of the profile
            
        Returns:
            Profile configuration or None if not found
        """
        profiles = self.config.profiles
        if profile_name in profiles:
            return profiles[profile_name].model_dump()
        return None
    
    def create_profile(self, name: str, description: Optional[str] = None) -> bool:
        """
        Create a new configuration profile.
        
        Args:
            name: Profile name
            description: Optional profile description
            
        Returns:
            True if successful, False otherwise
        """
        try:
            from .schema import ProfileConfig
            
            # Check if profile already exists
            if name in self.config.profiles:
                self.logger.warning(f"Profile '{name}' already exists")
                return False
            
            # Create new profile
            profile = ProfileConfig(
                name=name,
                description=description,
                created_at=datetime.now().isoformat()
            )
            
            # Add to profiles
            self.config.profiles[name] = profile
            
            # Save configuration
            return self._save_config()
            
        except Exception as e:
            self.logger.error(f"Failed to create profile '{name}': {e}")
            return False
    
    def delete_profile(self, name: str) -> bool:
        """
        Delete a configuration profile.
        
        Args:
            name: Profile name to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if profile exists
            if name not in self.config.profiles:
                self.logger.warning(f"Profile '{name}' not found")
                return False
            
            # Don't allow deletion of default profile
            if self.config.profiles[name].is_default:
                self.logger.error("Cannot delete default profile")
                return False
            
            # Remove profile
            del self.config.profiles[name]
            
            # If this was the current profile, switch to default
            if self.config.current_profile == name:
                self.config.current_profile = "default"
            
            # Save configuration
            return self._save_config()
            
        except Exception as e:
            self.logger.error(f"Failed to delete profile '{name}': {e}")
            return False
    
    def switch_profile(self, name: str) -> bool:
        """
        Switch to a different configuration profile.
        
        Args:
            name: Profile name to switch to
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if profile exists
            if name not in self.config.profiles:
                self.logger.error(f"Profile '{name}' not found")
                return False
            
            # Switch profile
            self.config.current_profile = name
            
            # Save configuration
            return self._save_config()
            
        except Exception as e:
            self.logger.error(f"Failed to switch to profile '{name}': {e}")
            return False
    
    def get_current_profile_name(self) -> str:
        """
        Get the name of the current profile.
        
        Returns:
            Current profile name
        """
        return self.config.current_profile
    
    def list_profiles(self) -> Dict[str, Dict[str, Any]]:
        """
        List all available profiles.
        
        Returns:
            Dictionary of profile names to profile data
        """
        return {
            name: profile.model_dump() 
            for name, profile in self.config.profiles.items()
        }
    
    def validate_configuration(self) -> bool:
        """
        Validate the current configuration.
        
        Returns:
            True if valid, False otherwise
        """
        try:
            # Validate using Pydantic.  ``BaseModel`` in Pydantic v2 exposes the
            # class method ``model_validate`` which expects a dictionary of
            # values.  The previous implementation attempted to call a
            # non‑existent ``validate`` method on the instance which always
            # raised an ``AttributeError``.  By validating against the dumped
            # configuration we ensure that any schema issues surface
            # appropriately.
            self.config.__class__.model_validate(self.config.model_dump())
            return True

        except Exception as e:
            self.logger.error(f"Configuration validation failed: {e}")
            return False
    
    def test_secure_storage(self) -> bool:
        """
        Test the secure storage functionality.
        
        Returns:
            True if tests pass, False otherwise
        """
        return self.secure_storage.test_encryption()
    
    def backup_configuration(self, backup_path: str) -> bool:
        """
        Create a backup of the current configuration.
        
        Args:
            backup_path: Path to save backup
            
        Returns:
            True if successful, False otherwise
        """
        try:
            backup_file = Path(backup_path)
            backup_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Save current configuration to backup location
            config_dict = self.config.model_dump()
            
            with open(backup_file, 'w', encoding='utf-8') as f:
                yaml.dump(config_dict, f, default_flow_style=False, indent=2)
            
            self.logger.info(f"Configuration backed up to {backup_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to backup configuration: {e}")
            return False
    
    def restore_configuration(self, backup_path: str) -> bool:
        """
        Restore configuration from backup.
        
        Args:
            backup_path: Path to backup file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            backup_file = Path(backup_path)
            
            if not backup_file.exists():
                self.logger.error(f"Backup file not found: {backup_file}")
                return False
            
            # Load backup configuration
            with open(backup_file, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f) or {}
            
            # Validate backup configuration
            config = validate_config_file(config_data)
            
            # Replace current configuration
            self.config = config
            
            # Save to current location
            return self._save_config()
            
        except Exception as e:
            self.logger.error(f"Failed to restore configuration: {e}")
            return False
    
    def diagnose_api_key_issues(self, service: str) -> dict:
        """
        Diagnose issues with API key configuration for a specific service.
        
        Args:
            service: Service name to diagnose
            
        Returns:
            Dictionary with diagnosis results
        """
        diagnosis = {
            "service": service,
            "has_stored_key": False,
            "is_encrypted": False,
            "is_valid": False,
            "issues": [],
            "recommendations": []
        }
        
        try:
            # Check if key exists in configuration
            stored_key = self.get(f'api_keys.{service}', '')
            
            if not stored_key:
                diagnosis["issues"].append("No API key configured")
                diagnosis["recommendations"].append(f"Use set_api_key('{service}', 'your_key') to configure")
                return diagnosis
            
            diagnosis["has_stored_key"] = True
            
            # Check if it's encrypted
            if self.secure_storage._is_encrypted_data(stored_key):
                diagnosis["is_encrypted"] = True
                
                # Try to decrypt
                try:
                    decrypted_key = self.secure_storage.decrypt_data(stored_key)
                    if decrypted_key:
                        diagnosis["is_valid"] = self.api_key_manager.validate_api_key(service, decrypted_key)
                        if not diagnosis["is_valid"]:
                            diagnosis["issues"].append("Decrypted key is invalid format")
                            diagnosis["recommendations"].append("Reconfigure with a valid API key")
                    else:
                        diagnosis["issues"].append("Failed to decrypt key")
                        diagnosis["recommendations"].append("Reconfigure the API key")
                except Exception as e:
                    diagnosis["issues"].append(f"Decryption failed: {e}")
                    diagnosis["recommendations"].append("Reconfigure the API key")
            else:
                # Key is not encrypted (might be plain text)
                diagnosis["issues"].append("API key is not encrypted")
                diagnosis["recommendations"].append("Reconfigure the API key to enable encryption")
                
                # Check if it's a valid plain text key
                if self.api_key_manager.validate_api_key(service, stored_key):
                    diagnosis["is_valid"] = True
                else:
                    diagnosis["issues"].append("Plain text key is invalid format")
                    diagnosis["recommendations"].append("Reconfigure with a valid API key")
            
        except Exception as e:
            diagnosis["issues"].append(f"Diagnosis failed: {e}")
            diagnosis["recommendations"].append("Check configuration file permissions")
        
        return diagnosis
    
    def fix_api_key_issues(self, service: str, new_api_key: str = None) -> bool:
        """
        Attempt to fix API key issues for a service.
        
        Args:
            service: Service name to fix
            new_api_key: New API key to set (if provided)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Diagnose current issues
            diagnosis = self.diagnose_api_key_issues(service)
            
            if diagnosis["is_valid"] and not new_api_key:
                self.logger.info(f"API key for {service} is already valid")
                return True
            
            # If new key provided, set it
            if new_api_key:
                return self.set_api_key(service, new_api_key)
            
            # Otherwise, clear the invalid key
            self.logger.info(f"Clearing invalid API key for {service}")
            return self.set(f'api_keys.{service}', '')
            
        except Exception as e:
            self.logger.error(f"Failed to fix API key issues for {service}: {e}")
            return False
    
    def list_api_key_status(self) -> dict:
        """
        List the status of all configured API keys.
        
        Returns:
            Dictionary with service names and their status
        """
        status = {}
        
        # Common services to check
        services = ["openai", "assemblyai", "google", "azure"]
        
        for service in services:
            diagnosis = self.diagnose_api_key_issues(service)
            status[service] = {
                "configured": diagnosis["has_stored_key"],
                "encrypted": diagnosis["is_encrypted"],
                "valid": diagnosis["is_valid"],
                "issues": diagnosis["issues"]
            }
        
        return status 
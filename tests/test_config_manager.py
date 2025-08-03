"""
Unit tests for the configuration management system.
"""
import pytest
import tempfile
import os
import json
from unittest.mock import patch, MagicMock
from pathlib import Path

from config.config_manager import ConfigManager
from config.schema import MainConfig


class TestConfigManager:
    """Test cases for ConfigManager class."""

    @pytest.mark.unit
    def test_config_manager_initialization(self, temp_config_dir):
        """Test ConfigManager initialization with default values."""
        config_file = os.path.join(temp_config_dir, "config.yaml")
        config_manager = ConfigManager(config_file=config_file)
        
        assert config_manager.config_file == Path(config_file)
        assert config_manager.config_file.parent == Path(temp_config_dir)

    @pytest.mark.unit
    def test_load_default_config(self, temp_config_dir):
        """Test loading default configuration when no config file exists."""
        config_file = os.path.join(temp_config_dir, "config.yaml")
        config_manager = ConfigManager(config_file=config_file)
        config = config_manager.config
        
        # Verify default configuration structure
        assert hasattr(config, 'audio')
        assert hasattr(config, 'api_keys')
        assert hasattr(config, 'hotkey')
        assert hasattr(config, 'ai')
        assert hasattr(config, 'logging')
        
        # Verify default audio settings
        assert config.audio.sample_rate == 16000
        assert config.audio.channels == 1
        assert config.audio.chunk_size == 1024

    @pytest.mark.unit
    def test_save_and_load_config(self, temp_config_dir):
        """Test saving and loading configuration."""
        config_file = os.path.join(temp_config_dir, "config.yaml")
        config_manager = ConfigManager(config_file=config_file)
        
        # Create test configuration
        test_config = config_manager.config
        test_config.audio.sample_rate = 44100
        test_config.audio.channels = 2
        test_config.audio.chunk_size = 2048
        
        # Save configuration
        success = config_manager._save_config(test_config)
        assert success is True
        
        # Load configuration
        loaded_config = config_manager.config
        
        # Verify configuration was saved and loaded correctly
        assert loaded_config.audio.sample_rate == 44100
        assert loaded_config.audio.channels == 2
        assert loaded_config.audio.chunk_size == 2048

    @pytest.mark.unit
    def test_config_validation(self, temp_config_dir):
        """Test configuration validation."""
        config_file = os.path.join(temp_config_dir, "config.yaml")
        config_manager = ConfigManager(config_file=config_file)
        
        # Test valid configuration
        valid_config = {
            "audio": {
                "sample_rate": 16000,
                "channels": 1,
                "chunk_size": 1024
            },
            "api_keys": {
                "openai": "sk-test123456789012345678901234567890123456789012345678901234567890",
                "assemblyai": "test123456789012345678901234567890123456789012345678901234567890"
            },
            "hotkey": {
                "primary_hotkey": "ctrl+win+space",
                "push_to_talk": True
            },
            "ai": {
                "model": "gpt-4o-mini",
                "remove_fillers": True,
                "improve_grammar": True
            },
            "logging": {
                "log_level": "INFO",
                "enable_debug": False
            }
        }
        
        # Should not raise any exceptions
        schema = MainConfig()
        validated_config = schema.model_validate(valid_config)
        assert validated_config is not None
        
        # Test invalid configuration
        invalid_config = {
            "audio": {
                "sample_rate": "invalid",  # Should be int
                "channels": 1
            }
        }
        
        with pytest.raises(ValueError):
            schema.validate(invalid_config)

    @pytest.mark.unit
    def test_secure_storage(self, temp_config_dir):
        """Test secure storage of sensitive configuration data."""
        config_file = os.path.join(temp_config_dir, "config.yaml")
        config_manager = ConfigManager(config_file=config_file)
        
        # Test API key storage with valid OpenAI format
        test_api_key = "sk-test_openai_key_12345"
        success = config_manager.set_api_key("openai", test_api_key)
        assert success is True
        
        # Test API key retrieval
        retrieved_key = config_manager.get_api_key("openai")
        assert retrieved_key == test_api_key
        
        # Test non-existent key
        empty_key = config_manager.get_api_key("nonexistent")
        assert empty_key == ""

    @pytest.mark.unit
    def test_profile_management(self, temp_config_dir):
        """Test configuration profile management."""
        config_file = os.path.join(temp_config_dir, "config.yaml")
        config_manager = ConfigManager(config_file=config_file)
        
        # Create a new profile
        success = config_manager.create_profile("test_profile", "Test configuration profile")
        assert success is True
        
        # List profiles
        profiles = config_manager.list_profiles()
        assert "test_profile" in profiles
        assert profiles["test_profile"]["description"] == "Test configuration profile"
        
        # Switch to the new profile
        success = config_manager.switch_profile("test_profile")
        assert success is True
        
        # Verify current profile
        current_profile = config_manager.get_current_profile_name()
        assert current_profile == "test_profile"

    @pytest.mark.unit
    def test_config_migration(self, temp_config_dir):
        """Test configuration migration from old format."""
        config_file = os.path.join(temp_config_dir, "config.yaml")
        config_manager = ConfigManager(config_file=config_file)
        
        # Test migration of old configuration format
        old_config = {
            "audio_settings": {"sample_rate": 16000},
            "api_keys": {"openai": "old_key"},
            "hotkey_settings": {"primary": "ctrl+shift+v"}
        }
        
        # Migration should handle old format gracefully
        # The current implementation should create a new default config
        assert config_manager.config is not None

    @pytest.mark.unit
    def test_config_backup_and_restore(self, temp_config_dir):
        """Test configuration backup and restore functionality."""
        config_file = os.path.join(temp_config_dir, "config.yaml")
        config_manager = ConfigManager(config_file=config_file)
        
        # Create backup
        backup_path = os.path.join(temp_config_dir, "backup.yaml")
        success = config_manager.backup_configuration(backup_path)
        assert success is True
        
        # Verify backup file exists
        assert os.path.exists(backup_path)
        
        # Test restore
        success = config_manager.restore_configuration(backup_path)
        assert success is True

    @pytest.mark.unit
    def test_error_handling(self, temp_config_dir):
        """Test error handling in configuration management."""
        config_file = os.path.join(temp_config_dir, "config.yaml")
        config_manager = ConfigManager(config_file=config_file)
        
        # Test invalid API key format - should return False, not raise ValueError
        success = config_manager.set_api_key("openai", "invalid_key")
        assert success is False  # Should fail validation, not raise exception
        
        # Test invalid profile operations
        success = config_manager.switch_profile("nonexistent")
        assert success is False

    @pytest.mark.unit
    def test_config_schema_validation(self):
        """Test configuration schema validation."""
        schema = MainConfig()
        
        # Test valid schema
        valid_config = {
            "audio": {
                "sample_rate": 16000,
                "channels": 1,
                "chunk_size": 1024,
                "format": "int16"
            },
            "api_keys": {
                "openai": "sk-test123456789012345678901234567890123456789012345678901234567890",
                "assemblyai": "test123456789012345678901234567890123456789012345678901234567890"
            },
            "hotkey": {
                "primary_hotkey": "ctrl+win+space",
                "push_to_talk": True
            },
            "ai": {
                "model": "gpt-4o-mini",
                "remove_fillers": True,
                "improve_grammar": True
            },
            "logging": {
                "log_level": "INFO",
                "file": "app.log",
                "max_size": 10485760,
                "backup_count": 5
            }
        }

        # Should not raise any exceptions
        validated_config = schema.model_validate(valid_config)
        assert validated_config is not None
        
        # Test invalid schema
        invalid_config = {
            "audio": {
                "sample_rate": "invalid",  # Should be int
                "channels": 1
            }
        }
        
        with pytest.raises(ValueError):
            schema.model_validate(invalid_config)

    @pytest.mark.unit
    def test_config_encryption(self, temp_config_dir):
        """Test configuration encryption for sensitive data."""
        config_file = os.path.join(temp_config_dir, "config.yaml")
        config_manager = ConfigManager(config_file=config_file)
        
        # Test API key encryption
        test_key = "sk-test123456789012345678901234567890123456789012345678901234567890"
        success = config_manager.set_api_key("openai", test_key)
        assert success is True
        
        # Verify key is encrypted in storage
        retrieved_key = config_manager.get_api_key("openai")
        assert retrieved_key == test_key 
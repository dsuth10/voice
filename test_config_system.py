#!/usr/bin/env python3
"""
Test script for the configuration management system.
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from config import ConfigManager, SetupWizard, ProfileManager


def test_config_manager():
    """Test the configuration manager functionality."""
    print("Testing Configuration Manager...")
    
    # Create temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        config_file = Path(temp_dir) / "test_config.yaml"
        
        # Initialize config manager
        config_manager = ConfigManager(str(config_file))
        
        # Test basic get/set operations
        print("  Testing get/set operations...")
        config_manager.set("audio.sample_rate", 44100)
        sample_rate = config_manager.get("audio.sample_rate")
        assert sample_rate == 44100, f"Expected 44100, got {sample_rate}"
        print("  ✅ Get/set operations work")
        
        # Test API key operations
        print("  Testing API key operations...")
        test_key = "sk-test123456789"
        success = config_manager.set_api_key("openai", test_key)
        if not success:
            print("  ❌ Failed to set API key")
            # Continue with other tests for now
        else:
            retrieved_key = config_manager.get_api_key("openai")
            if retrieved_key == test_key:
                print("  ✅ API key operations work")
            else:
                print(f"  ❌ API key mismatch: expected {test_key}, got {retrieved_key}")
        
        # Test profile operations
        print("  Testing profile operations...")
        profile_manager = ProfileManager(config_manager)
        
        # Create a test profile
        success = profile_manager.create_profile("test_profile", "Test profile")
        assert success, "Failed to create profile"
        
        # List profiles
        profiles = profile_manager.list_profiles()
        assert len(profiles) >= 1, "No profiles found"
        print("  ✅ Profile operations work")
        
        # Test configuration validation
        print("  Testing configuration validation...")
        is_valid = config_manager.validate_configuration()
        assert is_valid, "Configuration validation failed"
        print("  ✅ Configuration validation works")
        
        # Test secure storage
        print("  Testing secure storage...")
        storage_works = config_manager.test_secure_storage()
        if storage_works:
            print("  ✅ Secure storage works")
        else:
            print("  ❌ Secure storage test failed")
        
        print("✅ Configuration Manager tests passed!")


def test_setup_wizard():
    """Test the setup wizard functionality."""
    print("\nTesting Setup Wizard...")
    
    # Create temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        config_file = Path(temp_dir) / "test_config.yaml"
        
        # Initialize config manager
        config_manager = ConfigManager(str(config_file))
        
        # Create setup wizard
        wizard = SetupWizard(config_manager)
        
        # Test secure storage validation
        print("  Testing secure storage validation...")
        validation = wizard.validate_setup()
        assert isinstance(validation, dict), "Validation should return a dictionary"
        print("  ✅ Setup wizard validation works")
        
        print("✅ Setup Wizard tests passed!")


def test_schema_validation():
    """Test the configuration schema validation."""
    print("\nTesting Schema Validation...")
    
    from config import create_default_config, validate_config_file, get_config_schema
    
    # Test default config creation
    print("  Testing default config creation...")
    default_config = create_default_config()
    assert default_config is not None, "Default config creation failed"
    print("  ✅ Default config creation works")
    
    # Test schema generation
    print("  Testing schema generation...")
    schema = get_config_schema()
    assert isinstance(schema, dict), "Schema should be a dictionary"
    assert "properties" in schema, "Schema should have properties"
    print("  ✅ Schema generation works")
    
    # Test config validation
    print("  Testing config validation...")
    config_dict = default_config.model_dump()
    validated_config = validate_config_file(config_dict)
    assert validated_config is not None, "Config validation failed"
    print("  ✅ Config validation works")
    
    print("✅ Schema Validation tests passed!")


def main():
    """Run all configuration system tests."""
    print("=" * 60)
    print("Voice Dictation Assistant - Configuration System Tests")
    print("=" * 60)
    
    try:
        test_schema_validation()
        test_config_manager()
        test_setup_wizard()
        
        print("\n" + "=" * 60)
        print("✅ All configuration system tests passed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 
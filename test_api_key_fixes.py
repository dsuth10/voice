#!/usr/bin/env python3
"""
Test script to diagnose and fix API key configuration issues.
This script helps identify and resolve the Windows DPAPI decryption errors.
"""

import sys
import logging
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from config.config_manager import ConfigManager

def setup_logging():
    """Set up logging for the test script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def test_secure_storage():
    """Test the secure storage functionality."""
    print("🔐 Testing Secure Storage...")
    
    try:
        from config.secure_storage import SecureStorage
        
        storage = SecureStorage()
        
        # Test if DPAPI is available
        if not storage.is_dpapi_available():
            print("❌ Windows DPAPI is not available")
            return False
        
        print("✅ Windows DPAPI is available")
        
        # Test encryption/decryption
        if storage.test_encryption():
            print("✅ Encryption/decryption test passed")
            return True
        else:
            print("❌ Encryption/decryption test failed")
            return False
            
    except Exception as e:
        print(f"❌ Secure storage test failed: {e}")
        return False

def diagnose_api_keys():
    """Diagnose API key configuration issues."""
    print("\n🔍 Diagnosing API Key Issues...")
    
    try:
        config = ConfigManager()
        
        # Test secure storage first
        if not config.test_secure_storage():
            print("❌ Secure storage test failed - cannot proceed")
            return
        
        # List status of all API keys
        status = config.list_api_key_status()
        
        print("\n📊 API Key Status:")
        print("-" * 60)
        
        for service, info in status.items():
            status_icon = "✅" if info["valid"] else "❌"
            encrypted_icon = "🔒" if info["encrypted"] else "📝"
            configured_icon = "✓" if info["configured"] else "✗"
            
            print(f"{status_icon} {service.upper():<12} | "
                  f"Configured: {configured_icon} | "
                  f"Encrypted: {encrypted_icon} | "
                  f"Valid: {status_icon}")
            
            if info["issues"]:
                print(f"   Issues: {', '.join(info['issues'])}")
        
        # Detailed diagnosis for each service
        print("\n🔍 Detailed Diagnosis:")
        print("-" * 60)
        
        for service in ["openai", "assemblyai"]:
            diagnosis = config.diagnose_api_key_issues(service)
            
            print(f"\n{service.upper()}:")
            print(f"  Has stored key: {diagnosis['has_stored_key']}")
            print(f"  Is encrypted: {diagnosis['is_encrypted']}")
            print(f"  Is valid: {diagnosis['is_valid']}")
            
            if diagnosis["issues"]:
                print("  Issues:")
                for issue in diagnosis["issues"]:
                    print(f"    - {issue}")
            
            if diagnosis["recommendations"]:
                print("  Recommendations:")
                for rec in diagnosis["recommendations"]:
                    print(f"    - {rec}")
        
        return config
        
    except Exception as e:
        print(f"❌ Diagnosis failed: {e}")
        return None

def fix_api_key_issues(config):
    """Offer to fix API key issues."""
    print("\n🔧 API Key Fix Options:")
    print("-" * 60)
    
    services = ["openai", "assemblyai"]
    
    for service in services:
        diagnosis = config.diagnose_api_key_issues(service)
        
        if not diagnosis["is_valid"]:
            print(f"\n{service.upper()} needs attention:")
            
            if diagnosis["issues"]:
                for issue in diagnosis["issues"]:
                    print(f"  - {issue}")
            
            # Offer to clear invalid keys
            response = input(f"\nClear invalid {service} API key? (y/n): ").lower().strip()
            if response == 'y':
                if config.fix_api_key_issues(service):
                    print(f"✅ Cleared invalid {service} API key")
                else:
                    print(f"❌ Failed to clear {service} API key")
            
            # Offer to set new key
            response = input(f"Set new {service} API key? (y/n): ").lower().strip()
            if response == 'y':
                new_key = input(f"Enter {service} API key: ").strip()
                if new_key:
                    if config.set_api_key(service, new_key):
                        print(f"✅ Successfully set {service} API key")
                    else:
                        print(f"❌ Failed to set {service} API key")
                else:
                    print("❌ No API key provided")

def main():
    """Main test function."""
    print("🚀 API Key Configuration Test")
    print("=" * 60)
    
    setup_logging()
    
    # Test secure storage
    if not test_secure_storage():
        print("\n❌ Secure storage test failed. Cannot proceed with API key diagnosis.")
        return
    
    # Diagnose API keys
    config = diagnose_api_keys()
    
    if config:
        # Offer to fix issues
        response = input("\nWould you like to fix API key issues? (y/n): ").lower().strip()
        if response == 'y':
            fix_api_key_issues(config)
    
    print("\n✅ Test completed!")

if __name__ == "__main__":
    main() 
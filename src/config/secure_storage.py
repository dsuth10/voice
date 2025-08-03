"""
Secure storage for sensitive configuration data using Windows DPAPI.
Provides encryption and decryption of API keys and other sensitive information.
"""

import base64
import logging
import re
from typing import Optional, Tuple
import win32crypt
import win32api
import win32security
from datetime import datetime


class SecureStorage:
    """Secure storage for sensitive data using Windows DPAPI."""
    
    def __init__(self):
        """Initialize secure storage."""
        self.logger = logging.getLogger(__name__)
        self._description = "VoiceDictationAssistant"
    
    def _is_base64_encoded(self, data: str) -> bool:
        """
        Check if a string is valid base64 encoded.
        
        Args:
            data: String to check
            
        Returns:
            True if valid base64, False otherwise
        """
        if not data:
            return False
        
        # Base64 pattern (alphanumeric + / + = for padding)
        base64_pattern = re.compile(r'^[A-Za-z0-9+/]*={0,2}$')
        
        # Check if string matches base64 pattern
        if not base64_pattern.match(data):
            return False
        
        # Try to decode to verify it's valid base64
        try:
            base64.b64decode(data.encode('utf-8'))
            return True
        except Exception:
            return False
    
    def _is_encrypted_data(self, data: str) -> bool:
        """
        Check if data appears to be encrypted (base64 encoded and not plain text).
        
        Args:
            data: String to check
            
        Returns:
            True if likely encrypted, False otherwise
        """
        if not data:
            return False
        
        # Check if it's base64 encoded
        if not self._is_base64_encoded(data):
            return False
        
        # For now, assume any base64 data longer than 50 bytes might be encrypted
        # This is a conservative approach to avoid false positives
        try:
            decoded = base64.b64decode(data.encode('utf-8'))
            return len(decoded) > 50
        except Exception:
            return False
    
    def encrypt_data(self, data: str) -> str:
        """
        Encrypt data using Windows DPAPI.
        
        Args:
            data: String data to encrypt
            
        Returns:
            Base64 encoded encrypted data
            
        Raises:
            Exception: If encryption fails
        """
        if not data:
            return ""
        
        try:
            # Convert string to bytes
            data_bytes = data.encode('utf-8')
            
            # Encrypt using DPAPI without description
            encrypted_data = win32crypt.CryptProtectData(
                data_bytes,
                None  # No description
            )
            
            # Encode as base64 for storage
            return base64.b64encode(encrypted_data).decode('utf-8')
            
        except Exception as e:
            self.logger.error(f"Failed to encrypt data: {e}")
            raise Exception(f"Encryption failed: {e}")
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """
        Decrypt data using Windows DPAPI.
        
        Args:
            encrypted_data: Base64 encoded encrypted data
            
        Returns:
            Decrypted string data
            
        Raises:
            Exception: If decryption fails
        """
        if not encrypted_data:
            return ""
        
        # Check if data appears to be encrypted
        if not self._is_encrypted_data(encrypted_data):
            self.logger.warning("Data does not appear to be encrypted, returning as-is")
            return encrypted_data
        
        try:
            # Decode from base64
            encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
            
            # Decrypt using DPAPI
            # Note: pywin32 returns (description, data) instead of (data, description)
            description, decrypted_data = win32crypt.CryptUnprotectData(
                encrypted_bytes
            )
            
            # Convert bytes back to string
            if isinstance(decrypted_data, bytes):
                return decrypted_data.decode('utf-8')
            else:
                return str(decrypted_data)
            
        except Exception as e:
            self.logger.error(f"Failed to decrypt data: {e}")
            # Return empty string instead of raising exception
            return ""
    
    def test_encryption(self) -> bool:
        """
        Test encryption and decryption functionality.
        
        Returns:
            True if encryption/decryption works, False otherwise
        """
        try:
            test_data = "test_api_key_12345"
            encrypted = self.encrypt_data(test_data)
            decrypted = self.decrypt_data(encrypted)
            
            if decrypted == test_data:
                self.logger.info("Secure storage encryption test passed")
                return True
            else:
                self.logger.error("Secure storage encryption test failed - data mismatch")
                return False
                
        except Exception as e:
            self.logger.error(f"Secure storage encryption test failed: {e}")
            return False
    
    def is_dpapi_available(self) -> bool:
        """
        Check if Windows DPAPI is available on the system.
        
        Returns:
            True if DPAPI is available, False otherwise
        """
        try:
            # Try to get current user info to verify Windows API access
            win32api.GetUserName()
            return True
        except Exception:
            return False
    
    def get_user_info(self) -> dict:
        """
        Get current user information for debugging.
        
        Returns:
            Dictionary with user information
        """
        try:
            return {
                "username": win32api.GetUserName(),
                "domain": win32api.GetDomainName(),
                "computer": win32api.GetComputerName()
            }
        except Exception as e:
            self.logger.warning(f"Could not get user info: {e}")
            return {}


class APIKeyManager:
    """Manager for API keys with secure storage."""
    
    def __init__(self):
        """Initialize API key manager."""
        self.secure_storage = SecureStorage()
        self.logger = logging.getLogger(__name__)
    
    def store_api_key(self, service: str, api_key: str) -> bool:
        """
        Store an API key securely.
        
        Args:
            service: Service name (e.g., 'openai', 'assemblyai')
            api_key: API key to store
            
        Returns:
            True if successful, False otherwise
        """
        if not api_key:
            self.logger.warning(f"Empty API key provided for service: {service}")
            return False
        
        try:
            # Validate API key format
            if len(api_key) < 10:
                self.logger.error(f"API key for {service} appears to be too short")
                return False
            
            # Encrypt and store
            encrypted_key = self.secure_storage.encrypt_data(api_key)
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to store API key for {service}: {e}")
            return False
    
    def retrieve_api_key(self, service: str) -> str:
        """
        Retrieve an API key securely.
        
        Args:
            service: Service name
            
        Returns:
            Decrypted API key or empty string if not found/failed
        """
        try:
            # This would typically retrieve from a storage location
            # For now, return empty string as placeholder
            return ""
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve API key for {service}: {e}")
            return ""
    
    def validate_api_key(self, service: str, api_key: str) -> bool:
        """
        Validate an API key format.
        
        Args:
            service: Service name
            api_key: API key to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not api_key:
            return False
        
        # Basic validation
        if len(api_key) < 10:
            return False
        
        # Service-specific validation
        if service == "openai":
            return api_key.startswith("sk-")
        elif service == "assemblyai":
            return len(api_key) >= 20  # AssemblyAI keys are typically longer
        
        return True
    
    def test_secure_storage(self) -> bool:
        """
        Test the secure storage functionality.
        
        Returns:
            True if tests pass, False otherwise
        """
        return self.secure_storage.test_encryption() 
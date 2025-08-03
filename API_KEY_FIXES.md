# API Key Configuration Fixes

This document explains the fixes implemented for the Windows DPAPI decryption errors and how to resolve API key configuration issues.

## 🚨 Issues Fixed

### Issue 1: Premature Decryption Attempts
**Problem**: The system was attempting to decrypt empty or invalid data, causing Windows DPAPI errors.

**Solution**: Added validation before decryption attempts:
- Check if data is empty before attempting decryption
- Validate if data appears to be encrypted (base64 encoded)
- Return empty string instead of raising exceptions

### Issue 2: Missing API Key Validation
**Problem**: No distinction between empty, plain text, and encrypted API keys.

**Solution**: Added comprehensive validation:
- Check if stored data is base64 encoded
- Validate if data appears to be encrypted
- Handle plain text keys for backward compatibility
- Validate decrypted keys before returning them

### Issue 3: Windows DPAPI Limitations
**Problem**: Windows DPAPI requires specific conditions that weren't being checked.

**Solution**: Added proper error handling:
- Check if DPAPI is available before use
- Handle decryption failures gracefully
- Provide clear error messages and recommendations

## 🔧 How to Use the Fixes

### Option 1: Run the Diagnostic Script (Recommended)

Use the PowerShell script to automatically diagnose and fix issues:

```powershell
# Run the diagnostic script
.\test_api_keys.ps1
```

This script will:
1. Check if Python and required packages are installed
2. Test the secure storage functionality
3. Diagnose all API key configurations
4. Offer to fix issues interactively

### Option 2: Run the Python Script Directly

```powershell
# Run the Python diagnostic script
python test_api_key_fixes.py
```

### Option 3: Use the ConfigManager Methods

You can also use the new methods programmatically:

```python
from src.config.config_manager import ConfigManager

# Initialize config manager
config = ConfigManager()

# Diagnose a specific service
diagnosis = config.diagnose_api_key_issues("openai")
print(diagnosis)

# List status of all API keys
status = config.list_api_key_status()
print(status)

# Fix issues for a service
config.fix_api_key_issues("openai")

# Set a new API key
config.set_api_key("openai", "sk-your-api-key-here")
```

## 📊 Understanding the Diagnosis

The diagnostic output shows:

- **✅/❌ Status**: Whether the API key is valid
- **🔒/📝 Encryption**: Whether the key is encrypted
- **✓/✗ Configured**: Whether a key is stored

### Common Issues and Solutions

#### Issue: "No API key configured"
**Solution**: Use `config.set_api_key("service", "your_key")` to configure

#### Issue: "API key is not encrypted"
**Solution**: Reconfigure the key to enable encryption

#### Issue: "Failed to decrypt key"
**Solution**: Clear the invalid key and set a new one

#### Issue: "Decrypted key is invalid format"
**Solution**: Check the API key format and reconfigure

## 🔐 Secure Storage Improvements

### New Validation Methods

The `SecureStorage` class now includes:

```python
# Check if data is base64 encoded
storage._is_base64_encoded(data)

# Check if data appears to be encrypted
storage._is_encrypted_data(data)

# Test encryption/decryption
storage.test_encryption()

# Check DPAPI availability
storage.is_dpapi_available()
```

### Graceful Error Handling

- Empty data returns empty string instead of raising exceptions
- Invalid base64 data is handled gracefully
- Decryption failures return empty string instead of crashing
- Clear logging for debugging

## 🛠️ Configuration Manager Enhancements

### New Methods Added

```python
# Diagnose issues for a specific service
config.diagnose_api_key_issues("openai")

# Fix issues for a service
config.fix_api_key_issues("openai", new_key="optional")

# List status of all API keys
config.list_api_key_status()

# Enhanced API key getter with validation
config.get_api_key("openai")

# Enhanced API key setter with validation
config.set_api_key("openai", "sk-your-key")
```

## 🔍 Troubleshooting

### If You Still See Errors

1. **Check Windows User Context**: Ensure you're running as the same user who encrypted the data
2. **Verify DPAPI Availability**: Run `storage.is_dpapi_available()` to check
3. **Clear Invalid Keys**: Use `config.fix_api_key_issues("service")` to clear problematic keys
4. **Reconfigure Keys**: Set new API keys using `config.set_api_key()`

### Common Error Messages

- **"The parameter is incorrect"**: Usually means trying to decrypt non-encrypted data
- **"Incorrect padding"**: Invalid base64 data
- **"Failed to decrypt data"**: DPAPI context mismatch or corrupted data

### PowerShell Commands for Quick Fixes

```powershell
# Run the diagnostic script
.\test_api_keys.ps1

# Or run Python directly
python test_api_key_fixes.py

# Check if Python packages are installed
python -c "import pywin32, pydantic, yaml; print('All packages available')"
```

## 📝 Best Practices

1. **Always validate before decryption**: Check if data appears to be encrypted
2. **Handle empty data gracefully**: Return empty string instead of crashing
3. **Provide clear error messages**: Help users understand what went wrong
4. **Offer automatic fixes**: Let users easily resolve common issues
5. **Log everything**: Enable debugging when issues occur

## 🔄 Migration from Old System

If you have existing API keys that are causing issues:

1. Run the diagnostic script to identify problems
2. Clear invalid keys using the interactive prompts
3. Reconfigure valid API keys
4. Test the new configuration

The system is backward compatible and will handle both encrypted and plain text keys during the transition period. 
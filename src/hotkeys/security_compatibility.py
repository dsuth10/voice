"""
Windows Security and UAC Compatibility

This module handles Windows security permissions and User Account Control (UAC)
requirements for global hotkey registration and system-wide functionality.
"""

import logging
import ctypes
import sys
import os
import subprocess
from typing import Tuple, Optional, List
from dataclasses import dataclass
from enum import Enum


class SecurityLevel(Enum):
    """Enumeration for security levels."""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    ADMIN = "admin"


@dataclass
class SecurityInfo:
    """Information about security requirements and permissions."""
    level: SecurityLevel
    description: str
    requires_elevation: bool = False
    permission_required: str = ""
    mitigation_strategy: str = ""


class WindowsSecurityCompatibility:
    """
    Handles Windows security and UAC compatibility for global hotkeys.
    
    Provides methods to check permissions, request elevation when needed,
    and handle security-related issues for system-wide hotkey registration.
    """
    
    def __init__(self):
        """Initialize the security compatibility checker."""
        self.logger = logging.getLogger(__name__)
        
        # Windows API constants
        self.SE_PRIVILEGE_DISABLED = 0x00000000
        self.SE_PRIVILEGE_ENABLED_BY_DEFAULT = 0x00000001
        self.SE_PRIVILEGE_ENABLED = 0x00000002
        self.SE_PRIVILEGE_REMOVED = 0x00000004
        self.SE_PRIVILEGE_USED_FOR_ACCESS = 0x80000000
        
        # Security requirements for different operations
        self.security_requirements = {
            'global_hotkey_registration': SecurityInfo(
                level=SecurityLevel.MEDIUM,
                description="Global hotkey registration requires medium integrity level",
                requires_elevation=False,
                permission_required="INPUT_SYNCHRONIZE",
                mitigation_strategy="Run as normal user, request elevation only if needed"
            ),
            'system_tray_access': SecurityInfo(
                level=SecurityLevel.LOW,
                description="System tray access requires low integrity level",
                requires_elevation=False,
                permission_required="None",
                mitigation_strategy="Standard user permissions sufficient"
            ),
            'audio_device_access': SecurityInfo(
                level=SecurityLevel.MEDIUM,
                description="Audio device access may require medium integrity level",
                requires_elevation=False,
                permission_required="AUDIO_DEVICE_ACCESS",
                mitigation_strategy="Request audio permissions at runtime"
            ),
            'file_system_access': SecurityInfo(
                level=SecurityLevel.LOW,
                description="File system access for configuration files",
                requires_elevation=False,
                permission_required="FILE_READ_DATA, FILE_WRITE_DATA",
                mitigation_strategy="Use user profile directory for configuration"
            )
        }
    
    def check_current_permissions(self) -> SecurityInfo:
        """
        Check the current process permissions and security level.
        
        Returns:
            SecurityInfo: Information about current security level and permissions
        """
        try:
            # Check if running with admin privileges
            is_admin = self._is_running_as_admin()
            
            # Check process integrity level
            integrity_level = self._get_process_integrity_level()
            
            # Determine security level
            if is_admin:
                level = SecurityLevel.ADMIN
                description = "Running with administrator privileges"
                requires_elevation = False
            elif integrity_level == "high":
                level = SecurityLevel.HIGH
                description = "Running with high integrity level"
                requires_elevation = False
            elif integrity_level == "medium":
                level = SecurityLevel.MEDIUM
                description = "Running with medium integrity level (normal user)"
                requires_elevation = False
            elif integrity_level == "low":
                level = SecurityLevel.LOW
                description = "Running with low integrity level (restricted)"
                requires_elevation = True
            else:
                level = SecurityLevel.NONE
                description = "Unknown integrity level"
                requires_elevation = True
            
            return SecurityInfo(
                level=level,
                description=description,
                requires_elevation=requires_elevation,
                permission_required="",
                mitigation_strategy=""
            )
            
        except Exception as e:
            self.logger.error(f"Failed to check current permissions: {e}")
            return SecurityInfo(
                level=SecurityLevel.NONE,
                description=f"Error checking permissions: {e}",
                requires_elevation=True,
                permission_required="",
                mitigation_strategy=""
            )
    
    def _is_running_as_admin(self) -> bool:
        """
        Check if the current process is running with administrator privileges.
        
        Returns:
            bool: True if running as admin, False otherwise
        """
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except Exception:
            return False
    
    def _get_process_integrity_level(self) -> str:
        """
        Get the integrity level of the current process.
        
        Returns:
            str: Integrity level (high, medium, low, or unknown)
        """
        try:
            # This is a simplified check - in a real implementation,
            # you would use Windows API calls to get the actual integrity level
            if self._is_running_as_admin():
                return "high"
            else:
                return "medium"
        except Exception:
            return "unknown"
    
    def check_operation_permissions(self, operation: str) -> Tuple[bool, SecurityInfo]:
        """
        Check if the current process has sufficient permissions for an operation.
        
        Args:
            operation: The operation to check (e.g., 'global_hotkey_registration')
            
        Returns:
            Tuple[bool, SecurityInfo]: (has_permissions, security_info)
        """
        if operation not in self.security_requirements:
            self.logger.warning(f"Unknown operation: {operation}")
            return False, SecurityInfo(
                level=SecurityLevel.NONE,
                description=f"Unknown operation: {operation}",
                requires_elevation=True
            )
        
        current_perms = self.check_current_permissions()
        required_perms = self.security_requirements[operation]
        
        # Check if current level meets requirements
        has_permissions = self._compare_security_levels(
            current_perms.level, required_perms.level
        )
        
        return has_permissions, required_perms
    
    def _compare_security_levels(self, current: SecurityLevel, required: SecurityLevel) -> bool:
        """
        Compare security levels to determine if current level meets requirements.
        
        Args:
            current: Current security level
            required: Required security level
            
        Returns:
            bool: True if current level meets or exceeds required level
        """
        level_hierarchy = {
            SecurityLevel.NONE: 0,
            SecurityLevel.LOW: 1,
            SecurityLevel.MEDIUM: 2,
            SecurityLevel.HIGH: 3,
            SecurityLevel.ADMIN: 4
        }
        
        current_value = level_hierarchy.get(current, 0)
        required_value = level_hierarchy.get(required, 0)
        
        return current_value >= required_value
    
    def request_elevation(self, reason: str = "Global hotkey registration") -> bool:
        """
        Request elevation of privileges if needed.
        
        Args:
            reason: Reason for requesting elevation
            
        Returns:
            bool: True if elevation was successful or not needed
        """
        try:
            current_perms = self.check_current_permissions()
            
            if not current_perms.requires_elevation:
                self.logger.info("Elevation not required")
                return True
            
            self.logger.warning(f"Elevation required: {reason}")
            
            # In a real implementation, you would show a UAC prompt here
            # For now, we'll just log the requirement
            self.logger.info("UAC elevation would be requested here")
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to request elevation: {e}")
            return False
    
    def get_mitigation_strategies(self, operation: str) -> List[str]:
        """
        Get mitigation strategies for security issues.
        
        Args:
            operation: The operation that needs mitigation
            
        Returns:
            List[str]: List of mitigation strategies
        """
        strategies = []
        
        if operation not in self.security_requirements:
            return ["Unknown operation - consult documentation"]
        
        required_perms = self.security_requirements[operation]
        current_perms = self.check_current_permissions()
        
        if not self._compare_security_levels(current_perms.level, required_perms.level):
            strategies.append(f"Request elevation for {operation}")
            strategies.append("Run application as administrator")
            strategies.append("Check Windows security policies")
        
        if required_perms.mitigation_strategy:
            strategies.append(required_perms.mitigation_strategy)
        
        # Add general strategies
        strategies.extend([
            "Use user profile directory for configuration files",
            "Request permissions at runtime when possible",
            "Provide clear error messages for permission issues",
            "Implement graceful degradation for restricted environments"
        ])
        
        return strategies
    
    def validate_installation_requirements(self) -> Tuple[bool, List[str]]:
        """
        Validate that the system meets installation requirements.
        
        Returns:
            Tuple[bool, List[str]]: (meets_requirements, issues)
        """
        issues = []
        
        # Check Windows version
        if not self._is_windows_version_supported():
            issues.append("Windows version not supported")
        
        # Check Python version
        if not self._is_python_version_supported():
            issues.append("Python version not supported")
        
        # Check required permissions
        for operation in self.security_requirements:
            has_perms, _ = self.check_operation_permissions(operation)
            if not has_perms:
                issues.append(f"Insufficient permissions for {operation}")
        
        # Check for required Windows features
        if not self._check_windows_features():
            issues.append("Required Windows features not available")
        
        meets_requirements = len(issues) == 0
        
        return meets_requirements, issues
    
    def _is_windows_version_supported(self) -> bool:
        """
        Check if the Windows version is supported.
        
        Returns:
            bool: True if supported, False otherwise
        """
        try:
            import platform
            version = platform.version()
            # Simplified check - in reality, you'd check specific version numbers
            return "Windows" in platform.system()
        except Exception:
            return False
    
    def _is_python_version_supported(self) -> bool:
        """
        Check if the Python version is supported.
        
        Returns:
            bool: True if supported, False otherwise
        """
        try:
            version = sys.version_info
            return version.major == 3 and version.minor >= 8
        except Exception:
            return False
    
    def _check_windows_features(self) -> bool:
        """
        Check if required Windows features are available.
        
        Returns:
            bool: True if features are available, False otherwise
        """
        try:
            # Check for required DLLs
            required_dlls = ['user32.dll', 'kernel32.dll', 'shell32.dll']
            
            for dll in required_dlls:
                try:
                    ctypes.windll.LoadLibrary(dll)
                except Exception:
                    return False
            
            return True
            
        except Exception:
            return False
    
    def get_security_recommendations(self) -> List[str]:
        """
        Get security recommendations for the application.
        
        Returns:
            List[str]: List of security recommendations
        """
        recommendations = [
            "Run the application as a normal user when possible",
            "Only request elevation when absolutely necessary",
            "Store configuration files in user profile directory",
            "Implement proper error handling for permission issues",
            "Use Windows security APIs for permission checks",
            "Provide clear feedback when permissions are insufficient",
            "Consider using Windows App Certification Kit for validation",
            "Implement proper cleanup on application exit"
        ]
        
        return recommendations
    
    def create_manifest_file(self, output_path: str) -> bool:
        """
        Create a Windows manifest file for the application.
        
        Args:
            output_path: Path where the manifest file should be created
            
        Returns:
            bool: True if manifest was created successfully
        """
        try:
            manifest_content = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
  <assemblyIdentity
    version="1.0.0.0"
    processorArchitecture="*"
    name="Voice.Dictation.Assistant"
    type="win32"
  />
  <description>Voice Dictation Assistant</description>
  <trustInfo xmlns="urn:schemas-microsoft-com:asm.v3">
    <security>
      <requestedPrivileges>
        <requestedExecutionLevel level="asInvoker" uiAccess="false"/>
      </requestedPrivileges>
    </security>
  </trustInfo>
  <compatibility xmlns="urn:schemas-microsoft-com:compatibility.v1">
    <application>
      <supportedOS Id="{8e0f7a12-bfb3-4fe8-b9a5-48fd50a15a9a}"/>
    </application>
  </compatibility>
</assembly>'''
            
            with open(output_path, 'w') as f:
                f.write(manifest_content)
            
            self.logger.info(f"Created manifest file: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create manifest file: {e}")
            return False 
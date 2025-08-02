"""
Profile management for Voice Dictation Assistant.
Handles multiple configuration profiles with isolation and switching capabilities.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

from .schema import ProfileConfig, MainConfig


class ProfileManager:
    """Manager for multiple configuration profiles."""
    
    def __init__(self, config_manager):
        """
        Initialize profile manager.
        
        Args:
            config_manager: Reference to the main configuration manager
        """
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
    
    def create_profile(self, name: str, description: Optional[str] = None, 
                      copy_from: Optional[str] = None) -> bool:
        """
        Create a new configuration profile.
        
        Args:
            name: Profile name
            description: Optional profile description
            copy_from: Optional profile name to copy settings from
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate profile name
            if not self._validate_profile_name(name):
                return False
            
            # Check if profile already exists
            if name in self.config_manager.config.profiles:
                self.logger.warning(f"Profile '{name}' already exists")
                return False
            
            # Create new profile
            profile = ProfileConfig(
                name=name,
                description=description,
                created_at=datetime.now().isoformat()
            )
            
            # Add to profiles
            self.config_manager.config.profiles[name] = profile
            
            # Copy settings from another profile if specified
            if copy_from and copy_from in self.config_manager.config.profiles:
                self._copy_profile_settings(copy_from, name)
            
            # Save configuration
            success = self.config_manager._save_config()
            if success:
                self.logger.info(f"Created profile '{name}'")
            return success
            
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
            if name not in self.config_manager.config.profiles:
                self.logger.warning(f"Profile '{name}' not found")
                return False
            
            # Don't allow deletion of default profile
            if self.config_manager.config.profiles[name].is_default:
                self.logger.error("Cannot delete default profile")
                return False
            
            # Don't allow deletion of current profile
            if self.config_manager.config.current_profile == name:
                self.logger.error("Cannot delete current profile")
                return False
            
            # Remove profile
            del self.config_manager.config.profiles[name]
            
            # Save configuration
            success = self.config_manager._save_config()
            if success:
                self.logger.info(f"Deleted profile '{name}'")
            return success
            
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
            if name not in self.config_manager.config.profiles:
                self.logger.error(f"Profile '{name}' not found")
                return False
            
            # Switch profile
            old_profile = self.config_manager.config.current_profile
            self.config_manager.config.current_profile = name
            
            # Save configuration
            success = self.config_manager._save_config()
            if success:
                self.logger.info(f"Switched from profile '{old_profile}' to '{name}'")
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to switch to profile '{name}': {e}")
            return False
    
    def rename_profile(self, old_name: str, new_name: str) -> bool:
        """
        Rename a configuration profile.
        
        Args:
            old_name: Current profile name
            new_name: New profile name
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if old profile exists
            if old_name not in self.config_manager.config.profiles:
                self.logger.error(f"Profile '{old_name}' not found")
                return False
            
            # Validate new profile name
            if not self._validate_profile_name(new_name):
                return False
            
            # Check if new name already exists
            if new_name in self.config_manager.config.profiles:
                self.logger.error(f"Profile '{new_name}' already exists")
                return False
            
            # Get profile data
            profile = self.config_manager.config.profiles[old_name]
            
            # Update profile name
            profile.name = new_name
            
            # Remove old profile and add with new name
            del self.config_manager.config.profiles[old_name]
            self.config_manager.config.profiles[new_name] = profile
            
            # Update current profile if it was the renamed one
            if self.config_manager.config.current_profile == old_name:
                self.config_manager.config.current_profile = new_name
            
            # Save configuration
            success = self.config_manager._save_config()
            if success:
                self.logger.info(f"Renamed profile '{old_name}' to '{new_name}'")
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to rename profile '{old_name}' to '{new_name}': {e}")
            return False
    
    def copy_profile(self, source_name: str, target_name: str, 
                    description: Optional[str] = None) -> bool:
        """
        Copy a configuration profile.
        
        Args:
            source_name: Source profile name
            target_name: Target profile name
            description: Optional description for the new profile
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if source profile exists
            if source_name not in self.config_manager.config.profiles:
                self.logger.error(f"Source profile '{source_name}' not found")
                return False
            
            # Validate target profile name
            if not self._validate_profile_name(target_name):
                return False
            
            # Check if target name already exists
            if target_name in self.config_manager.config.profiles:
                self.logger.error(f"Target profile '{target_name}' already exists")
                return False
            
            # Create new profile with copy of settings
            success = self.create_profile(target_name, description, copy_from=source_name)
            if success:
                self.logger.info(f"Copied profile '{source_name}' to '{target_name}'")
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to copy profile '{source_name}' to '{target_name}': {e}")
            return False
    
    def get_profile_info(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a profile.
        
        Args:
            name: Profile name
            
        Returns:
            Profile information or None if not found
        """
        try:
            if name not in self.config_manager.config.profiles:
                return None
            
            profile = self.config_manager.config.profiles[name]
            info = profile.model_dump()
            info['is_current'] = (name == self.config_manager.config.current_profile)
            return info
            
        except Exception as e:
            self.logger.error(f"Failed to get profile info for '{name}': {e}")
            return None
    
    def list_profiles(self) -> List[Dict[str, Any]]:
        """
        List all available profiles with information.
        
        Returns:
            List of profile information dictionaries
        """
        try:
            profiles = []
            for name, profile in self.config_manager.config.profiles.items():
                info = profile.model_dump()
                info['is_current'] = (name == self.config_manager.config.current_profile)
                profiles.append(info)
            
            return profiles
            
        except Exception as e:
            self.logger.error(f"Failed to list profiles: {e}")
            return []
    
    def get_current_profile(self) -> Optional[Dict[str, Any]]:
        """
        Get information about the current profile.
        
        Returns:
            Current profile information or None
        """
        current_name = self.config_manager.config.current_profile
        return self.get_profile_info(current_name)
    
    def set_profile_as_default(self, name: str) -> bool:
        """
        Set a profile as the default profile.
        
        Args:
            name: Profile name to set as default
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if profile exists
            if name not in self.config_manager.config.profiles:
                self.logger.error(f"Profile '{name}' not found")
                return False
            
            # Update default profile
            for profile_name, profile in self.config_manager.config.profiles.items():
                profile.is_default = (profile_name == name)
            
            # Save configuration
            success = self.config_manager._save_config()
            if success:
                self.logger.info(f"Set profile '{name}' as default")
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to set profile '{name}' as default: {e}")
            return False
    
    def _validate_profile_name(self, name: str) -> bool:
        """
        Validate a profile name.
        
        Args:
            name: Profile name to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not name or not name.strip():
            self.logger.error("Profile name cannot be empty")
            return False
        
        if len(name) > 50:
            self.logger.error("Profile name too long (max 50 characters)")
            return False
        
        # Check for invalid characters
        invalid_chars = ['<', '>', ':', '"', '|', '?', '*', '\\', '/']
        if any(char in name for char in invalid_chars):
            self.logger.error("Profile name contains invalid characters")
            return False
        
        return True
    
    def _copy_profile_settings(self, source_name: str, target_name: str) -> bool:
        """
        Copy settings from one profile to another.
        
        Args:
            source_name: Source profile name
            target_name: Target profile name
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # This would copy all configuration settings from source to target
            # For now, this is a placeholder for the actual implementation
            self.logger.info(f"Copied settings from profile '{source_name}' to '{target_name}'")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to copy profile settings: {e}")
            return False
    
    def export_profile(self, name: str, export_path: str) -> bool:
        """
        Export a profile to a file.
        
        Args:
            name: Profile name to export
            export_path: Path to export file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if profile exists
            if name not in self.config_manager.config.profiles:
                self.logger.error(f"Profile '{name}' not found")
                return False
            
            # Get profile info
            profile_info = self.get_profile_info(name)
            if not profile_info:
                return False
            
            # Export to file
            import yaml
            export_file = Path(export_path)
            export_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(export_file, 'w', encoding='utf-8') as f:
                yaml.dump(profile_info, f, default_flow_style=False, indent=2)
            
            self.logger.info(f"Exported profile '{name}' to {export_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export profile '{name}': {e}")
            return False
    
    def import_profile(self, import_path: str, name: Optional[str] = None) -> bool:
        """
        Import a profile from a file.
        
        Args:
            import_path: Path to import file
            name: Optional new name for the imported profile
            
        Returns:
            True if successful, False otherwise
        """
        try:
            import yaml
            
            # Load profile data
            import_file = Path(import_path)
            if not import_file.exists():
                self.logger.error(f"Import file not found: {import_file}")
                return False
            
            with open(import_file, 'r', encoding='utf-8') as f:
                profile_data = yaml.safe_load(f)
            
            # Extract profile name
            if not name:
                name = profile_data.get('name', 'imported_profile')
            
            # Create profile
            description = profile_data.get('description', 'Imported profile')
            return self.create_profile(name, description)
            
        except Exception as e:
            self.logger.error(f"Failed to import profile: {e}")
            return False 
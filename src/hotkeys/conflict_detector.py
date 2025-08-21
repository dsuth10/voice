"""
Hotkey Conflict Detection and Error Handling

This module provides conflict detection for system-wide hotkeys,
identifying potential conflicts with Windows system shortcuts and
other applications, and offering fallback solutions.
"""

import logging
import subprocess
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# ``winreg`` is only available on Windows.  The conflict detector mainly uses
# predefined dictionaries and does not rely on the module directly, so we import
# it defensively to keep the module importable on other platforms.
try:  # pragma: no cover - depends on platform
    import winreg  # type: ignore
except Exception:  # pragma: no cover
    winreg = None  # type: ignore


class ConflictLevel(Enum):
    """Enumeration for conflict severity levels."""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ConflictInfo:
    """Information about a detected conflict."""
    hotkey: str
    conflict_type: str
    description: str
    level: ConflictLevel
    suggested_alternatives: List[str] = None


class HotkeyConflictDetector:
    """
    Detects potential conflicts with system and application hotkeys.
    
    Analyzes Windows system shortcuts, common application hotkeys,
    and provides fallback suggestions for conflicting combinations.
    """
    
    def __init__(self):
        """Initialize the conflict detector."""
        self.logger = logging.getLogger(__name__)
        
        # Common Windows system shortcuts that should be avoided
        self.system_shortcuts = {
            'ctrl+alt+delete': 'System Security',
            'ctrl+shift+esc': 'Task Manager',
            'win+r': 'Run Dialog',
            'win+e': 'File Explorer',
            'win+d': 'Show Desktop',
            'win+l': 'Lock Computer',
            'win+tab': 'Task View',
            'alt+tab': 'Switch Windows',
            'ctrl+alt+tab': 'Switch Windows (Extended)',
            'win+space': 'Switch Input Language',
            'win+shift+s': 'Snipping Tool',
            'win+v': 'Clipboard History',
            'win+period': 'Emoji Panel',
            'win+shift+c': 'Cortana',
            'win+a': 'Action Center',
            'win+i': 'Settings',
            'win+x': 'Power User Menu',
            'win+u': 'Ease of Access',
            'win+p': 'Project',
            'win+k': 'Connect',
            'win+comma': 'Peek at Desktop',
            'win+home': 'Minimize All',
            'win+shift+m': 'Restore All',
            'win+shift+arrow': 'Move Window',
            'win+arrow': 'Snap Window',
            'ctrl+win+arrow': 'Move Virtual Desktop',
            'win+ctrl+d': 'New Virtual Desktop',
            'win+ctrl+f4': 'Close Virtual Desktop',
            'win+ctrl+shift+arrow': 'Move Window to Virtual Desktop'
        }
        
        # Common application shortcuts that might conflict
        self.application_shortcuts = {
            'ctrl+c': 'Copy',
            'ctrl+v': 'Paste',
            'ctrl+x': 'Cut',
            'ctrl+z': 'Undo',
            'ctrl+y': 'Redo',
            'ctrl+a': 'Select All',
            'ctrl+f': 'Find',
            'ctrl+s': 'Save',
            'ctrl+o': 'Open',
            'ctrl+n': 'New',
            'ctrl+p': 'Print',
            'ctrl+w': 'Close',
            'ctrl+q': 'Quit',
            'ctrl+t': 'New Tab',
            'ctrl+shift+t': 'Reopen Tab',
            'ctrl+tab': 'Next Tab',
            'ctrl+shift+tab': 'Previous Tab',
            'f5': 'Refresh',
            'f11': 'Full Screen',
            'alt+f4': 'Close Window',
            'alt+enter': 'Properties',
            'shift+delete': 'Delete Permanently'
        }
        
        # Fallback hotkey suggestions
        self.fallback_suggestions = [
            'ctrl+win+space',
            'ctrl+win+r',
            'ctrl+win+v',
            'ctrl+win+x',
            'ctrl+win+z',
            'ctrl+win+c',
            'ctrl+win+f',
            'ctrl+win+g',
            'ctrl+win+h',
            'ctrl+win+j',
            'ctrl+win+k',
            'ctrl+win+l',
            'ctrl+win+m',
            'ctrl+win+n',
            'ctrl+win+o',
            'ctrl+win+p',
            'ctrl+win+q',
            'ctrl+win+s',
            'ctrl+win+t',
            'ctrl+win+u',
            'ctrl+win+w',
            'ctrl+win+y',
            'alt+win+space',
            'shift+win+space',
            'ctrl+alt+space',
            'ctrl+shift+space'
        ]
    
    def check_conflict(self, hotkey: str) -> ConflictInfo:
        """
        Check if a hotkey combination conflicts with system or application shortcuts.
        
        Args:
            hotkey: The hotkey combination to check (e.g., "ctrl+win+space")
            
        Returns:
            ConflictInfo: Information about any detected conflicts
        """
        normalized_hotkey = self._normalize_hotkey(hotkey)
        
        # Check system shortcuts
        if normalized_hotkey in self.system_shortcuts:
            return ConflictInfo(
                hotkey=hotkey,
                conflict_type="system_shortcut",
                description=f"Conflicts with Windows system shortcut: {self.system_shortcuts[normalized_hotkey]}",
                level=ConflictLevel.HIGH,
                suggested_alternatives=self._get_alternatives(hotkey)
            )
        
        # Check application shortcuts
        if normalized_hotkey in self.application_shortcuts:
            return ConflictInfo(
                hotkey=hotkey,
                conflict_type="application_shortcut",
                description=f"Conflicts with common application shortcut: {self.application_shortcuts[normalized_hotkey]}",
                level=ConflictLevel.MEDIUM,
                suggested_alternatives=self._get_alternatives(hotkey)
            )
        
        # Check for partial conflicts
        partial_conflict = self._check_partial_conflicts(normalized_hotkey)
        if partial_conflict:
            return partial_conflict
        
        # No conflicts detected
        return ConflictInfo(
            hotkey=hotkey,
            conflict_type="none",
            description="No conflicts detected",
            level=ConflictLevel.NONE,
            suggested_alternatives=[]
        )
    
    def _check_partial_conflicts(self, hotkey: str) -> Optional[ConflictInfo]:
        """
        Check for partial conflicts with existing shortcuts.
        
        Args:
            hotkey: The normalized hotkey combination
            
        Returns:
            ConflictInfo: Information about partial conflicts, or None if none found
        """
        hotkey_parts = set(hotkey.split('+'))
        
        for existing_hotkey, description in self.system_shortcuts.items():
            existing_parts = set(existing_hotkey.split('+'))
            
            # Check if there's significant overlap
            overlap = hotkey_parts.intersection(existing_parts)
            if len(overlap) >= 2 and len(hotkey_parts) <= len(existing_parts):
                return ConflictInfo(
                    hotkey=hotkey,
                    conflict_type="partial_system_conflict",
                    description=f"Partially conflicts with system shortcut: {description} ({existing_hotkey})",
                    level=ConflictLevel.LOW,
                    suggested_alternatives=self._get_alternatives(hotkey)
                )
        
        return None
    
    def _get_alternatives(self, hotkey: str) -> List[str]:
        """
        Get alternative hotkey suggestions for a conflicting combination.
        
        Args:
            hotkey: The conflicting hotkey combination
            
        Returns:
            List[str]: List of alternative hotkey combinations
        """
        # Filter out the conflicting hotkey and similar ones
        alternatives = []
        conflicting_parts = set(hotkey.split('+'))
        
        for suggestion in self.fallback_suggestions:
            suggestion_parts = set(suggestion.split('+'))
            
            # Avoid suggestions that are too similar to the conflicting hotkey
            if len(conflicting_parts.intersection(suggestion_parts)) < 2:
                alternatives.append(suggestion)
            
            if len(alternatives) >= 5:  # Limit to 5 suggestions
                break
        
        return alternatives
    
    def _normalize_hotkey(self, hotkey: str) -> str:
        """
        Normalize a hotkey string for consistent comparison.
        
        Args:
            hotkey: Raw hotkey string
            
        Returns:
            str: Normalized hotkey string
        """
        # Convert to lowercase and remove extra spaces
        normalized = hotkey.lower().strip()
        
        # Sort the parts for consistent comparison
        parts = normalized.split('+')
        parts.sort()
        
        return '+'.join(parts)
    
    def get_safe_hotkeys(self, count: int = 5) -> List[str]:
        """
        Get a list of safe hotkey combinations that are unlikely to conflict.
        
        Args:
            count: Number of safe hotkeys to return
            
        Returns:
            List[str]: List of safe hotkey combinations
        """
        safe_hotkeys = []
        
        for suggestion in self.fallback_suggestions:
            conflict_info = self.check_conflict(suggestion)
            if conflict_info.level == ConflictLevel.NONE:
                safe_hotkeys.append(suggestion)
            
            if len(safe_hotkeys) >= count:
                break
        
        return safe_hotkeys
    
    def validate_hotkey(self, hotkey: str) -> Tuple[bool, str]:
        """
        Validate a hotkey combination and provide feedback.
        
        Args:
            hotkey: The hotkey combination to validate
            
        Returns:
            Tuple[bool, str]: (is_valid, feedback_message)
        """
        conflict_info = self.check_conflict(hotkey)
        
        if conflict_info.level == ConflictLevel.NONE:
            return True, "Hotkey is safe to use"
        elif conflict_info.level == ConflictLevel.LOW:
            return True, f"Warning: {conflict_info.description}"
        elif conflict_info.level == ConflictLevel.MEDIUM:
            return False, f"Conflict detected: {conflict_info.description}"
        else:  # HIGH or CRITICAL
            return False, f"Critical conflict: {conflict_info.description}"
    
    def get_conflict_report(self, hotkeys: List[str]) -> Dict[str, ConflictInfo]:
        """
        Generate a conflict report for multiple hotkeys.
        
        Args:
            hotkeys: List of hotkey combinations to check
            
        Returns:
            Dict[str, ConflictInfo]: Dictionary mapping hotkeys to conflict information
        """
        report = {}
        
        for hotkey in hotkeys:
            conflict_info = self.check_conflict(hotkey)
            report[hotkey] = conflict_info
        
        return report 
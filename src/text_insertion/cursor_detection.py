"""
Cursor Position Detection Module

This module provides functionality to detect the current cursor position
and active application window using pywin32 and pygetwindow.
"""

import logging
import pygetwindow as gw
import win32gui
import win32api
import win32con
from typing import Optional, Tuple, Dict, Any

logger = logging.getLogger(__name__)


class CursorDetector:
    """Detects cursor position and active application window."""
    
    def __init__(self):
        self.last_active_window = None
        self.window_cache = {}
    
    def get_cursor_position(self) -> Tuple[int, int]:
        """
        Get the current cursor position in screen coordinates.
        
        Returns:
            Tuple[int, int]: (x, y) coordinates of the cursor
        """
        try:
            cursor_pos = win32api.GetCursorPos()
            logger.debug(f"Cursor position detected: {cursor_pos}")
            return cursor_pos
        except Exception as e:
            logger.error(f"Failed to get cursor position: {e}")
            return (0, 0)
    
    def get_active_window(self) -> Optional[gw.Window]:
        """
        Get the currently active window.
        
        Returns:
            Optional[gw.Window]: Active window object or None if not found
        """
        try:
            active_window = gw.getActiveWindow()
            if active_window:
                self.last_active_window = active_window
                logger.debug(f"Active window detected: {active_window.title}")
            return active_window
        except Exception as e:
            logger.error(f"Failed to get active window: {e}")
            return None
    
    def get_window_info(self, window: Optional[gw.Window] = None) -> Dict[str, Any]:
        """
        Get detailed information about a window.
        
        Args:
            window: Window object to analyze. If None, uses active window.
            
        Returns:
            Dict containing window information
        """
        if window is None:
            window = self.get_active_window()
        
        if not window:
            return {}
        
        try:
            # Get window handle
            hwnd = win32gui.FindWindow(None, window.title)
            
            info = {
                'title': window.title,
                'app_name': self._extract_app_name(window.title),
                'hwnd': hwnd,
                'rect': window.rect,
                'is_active': window.isActive,
                'is_minimized': window.isMinimized,
                'is_maximized': window.isMaximized
            }
            
            # Get process information
            if hwnd:
                try:
                    _, pid = win32gui.GetWindowThreadProcessId(hwnd)
                    info['process_id'] = pid
                except:
                    info['process_id'] = None
            
            logger.debug(f"Window info: {info}")
            return info
            
        except Exception as e:
            logger.error(f"Failed to get window info: {e}")
            return {}
    
    def _extract_app_name(self, window_title: str) -> str:
        """
        Extract application name from window title.
        
        Args:
            window_title: Full window title
            
        Returns:
            Extracted application name
        """
        # Common application patterns
        app_patterns = {
            'Microsoft Word': ['Word', 'Document'],
            'Microsoft Excel': ['Excel', 'Workbook'],
            'Microsoft PowerPoint': ['PowerPoint', 'Presentation'],
            'Notepad': ['Notepad'],
            'Visual Studio Code': ['Visual Studio Code', 'Code'],
            'Google Chrome': ['Chrome'],
            'Mozilla Firefox': ['Firefox'],
            'Microsoft Edge': ['Edge'],
            'Outlook': ['Outlook'],
            'Teams': ['Teams'],
            'Slack': ['Slack']
        }
        
        title_lower = window_title.lower()
        
        for app_name, patterns in app_patterns.items():
            for pattern in patterns:
                if pattern.lower() in title_lower:
                    return app_name
        
        # Fallback: extract from title
        if ' - ' in window_title:
            return window_title.split(' - ')[-1]
        
        return window_title
    
    def is_cursor_in_window(self, window: Optional[gw.Window] = None) -> bool:
        """
        Check if cursor is within the bounds of a window.
        
        Args:
            window: Window to check. If None, uses active window.
            
        Returns:
            True if cursor is in window bounds
        """
        if window is None:
            window = self.get_active_window()
        
        if not window:
            return False
        
        try:
            cursor_pos = self.get_cursor_position()
            window_rect = window.rect
            
            return (window_rect.left <= cursor_pos[0] <= window_rect.right and
                   window_rect.top <= cursor_pos[1] <= window_rect.bottom)
        except Exception as e:
            logger.error(f"Failed to check cursor in window: {e}")
            return False
    
    def get_cursor_position_in_window(self, window: Optional[gw.Window] = None) -> Tuple[int, int]:
        """
        Get cursor position relative to window coordinates.
        
        Args:
            window: Window to get relative position for. If None, uses active window.
            
        Returns:
            Tuple[int, int]: (x, y) coordinates relative to window
        """
        if window is None:
            window = self.get_active_window()
        
        if not window:
            return (0, 0)
        
        try:
            cursor_pos = self.get_cursor_position()
            window_rect = window.rect
            
            relative_x = cursor_pos[0] - window_rect.left
            relative_y = cursor_pos[1] - window_rect.top
            
            return (relative_x, relative_y)
        except Exception as e:
            logger.error(f"Failed to get cursor position in window: {e}")
            return (0, 0)
    
    def get_supported_applications(self) -> Dict[str, bool]:
        """
        Get list of applications and their support status.
        
        Returns:
            Dict mapping app names to support status
        """
        supported_apps = {
            'Microsoft Word': True,
            'Microsoft Excel': True,
            'Microsoft PowerPoint': True,
            'Notepad': True,
            'Visual Studio Code': True,
            'Google Chrome': True,
            'Mozilla Firefox': True,
            'Microsoft Edge': True,
            'Outlook': True,
            'Teams': True,
            'Slack': True,
            'Notepad++': True,
            'Sublime Text': True,
            'Atom': True,
            'Discord': True,
            'WhatsApp': True,
            'Telegram': True
        }
        
        return supported_apps
    
    def is_application_supported(self, app_name: str) -> bool:
        """
        Check if an application is supported for text insertion.
        
        Args:
            app_name: Name of the application to check
            
        Returns:
            True if application is supported
        """
        supported_apps = self.get_supported_applications()
        return supported_apps.get(app_name, False) 
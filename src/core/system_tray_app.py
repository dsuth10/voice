"""
System Tray Application for Voice Dictation Assistant

This module provides a Windows system tray application with visual feedback,
status indicators, and quick access to settings and controls.
"""

import os
import sys
import threading
import logging
from typing import Optional, Dict, Callable
from pathlib import Path

try:
    from pystray import Icon, Menu, MenuItem
    from PIL import Image, ImageDraw
    import win10toast
    PYSYSTRAY_AVAILABLE = True
except ImportError:
    PYSYSTRAY_AVAILABLE = False
    Icon = Menu = MenuItem = None
    Image = ImageDraw = None
    win10toast = None

from .types import ApplicationState
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .application_controller import ApplicationController


class SystemTrayApp:
    """
    System tray application with visual feedback and menu controls.
    
    Provides a Windows system tray icon with:
    - Visual status indicators (idle, recording, processing, error)
    - Quick access menu for common functions
    - Settings and about dialogs
    - Notifications for important events
    """
    
    def __init__(self, toggle_recording_callback: Callable,
                 show_analytics_callback: Callable,
                 show_config_callback: Callable,
                 shutdown_callback: Callable):
        """
        Initialize the system tray application.
        
        Args:
            toggle_recording_callback: Callback for toggling recording
            show_analytics_callback: Callback for showing analytics dashboard
            show_config_callback: Callback for showing configuration
            shutdown_callback: Callback for shutting down the application
        """
        self.logger = logging.getLogger(__name__)
        
        # Store callbacks
        self.toggle_recording_callback = toggle_recording_callback
        self.show_analytics_callback = show_analytics_callback
        self.show_config_callback = show_config_callback
        self.shutdown_callback = shutdown_callback
        
        self.icon = None
        self.current_state = ApplicationState.IDLE
        self.notifier = None
        
        # Initialize icon images
        self.icons = {}
        self._load_icons()
        
        # Setup notification system
        if win10toast:
            self.notifier = win10toast.ToastNotifier()
        
        self.logger.info("System tray application initialized")
    
    def _load_icons(self):
        """Load or create system tray icons for different states."""
        try:
            # Try to load icons from resources directory
            resources_dir = Path(__file__).parent.parent.parent / "resources" / "icons"
            if resources_dir.exists():
                self.icons = {
                    ApplicationState.IDLE: Image.open(resources_dir / "icon_idle.png"),
                    ApplicationState.RECORDING: Image.open(resources_dir / "icon_recording.png"),
                    ApplicationState.PROCESSING: Image.open(resources_dir / "icon_processing.png"),
                    ApplicationState.ERROR: Image.open(resources_dir / "icon_error.png"),
                    ApplicationState.CONFIGURING: Image.open(resources_dir / "icon_configuring.png")
                }
                self.logger.info("Loaded system tray icons from resources")
            else:
                # Create default icons if resources don't exist
                self._create_default_icons()
                self.logger.info("Created default system tray icons")
        except Exception as e:
            self.logger.warning(f"Failed to load icons: {e}. Creating default icons.")
            self._create_default_icons()
    
    def _create_default_icons(self):
        """Create default system tray icons using PIL."""
        if not Image or not ImageDraw:
            self.logger.error("PIL not available, cannot create icons")
            return
        
        # Create 32x32 icons with different colors
        icon_size = (32, 32)
        
        # Idle icon (gray)
        idle_img = Image.new('RGBA', icon_size, (128, 128, 128, 255))
        draw = ImageDraw.Draw(idle_img)
        draw.ellipse([8, 8, 24, 24], fill=(200, 200, 200, 255))
        self.icons[ApplicationState.IDLE] = idle_img
        
        # Recording icon (red)
        recording_img = Image.new('RGBA', icon_size, (255, 0, 0, 255))
        draw = ImageDraw.Draw(recording_img)
        draw.ellipse([8, 8, 24, 24], fill=(255, 100, 100, 255))
        self.icons[ApplicationState.RECORDING] = recording_img
        
        # Processing icon (blue)
        processing_img = Image.new('RGBA', icon_size, (0, 0, 255, 255))
        draw = ImageDraw.Draw(processing_img)
        draw.ellipse([8, 8, 24, 24], fill=(100, 100, 255, 255))
        self.icons[ApplicationState.PROCESSING] = processing_img
        
        # Error icon (orange)
        error_img = Image.new('RGBA', icon_size, (255, 165, 0, 255))
        draw = ImageDraw.Draw(error_img)
        draw.ellipse([8, 8, 24, 24], fill=(255, 200, 100, 255))
        self.icons[ApplicationState.ERROR] = error_img
        
        # Configuring icon (yellow)
        configuring_img = Image.new('RGBA', icon_size, (255, 255, 0, 255))
        draw = ImageDraw.Draw(configuring_img)
        draw.ellipse([8, 8, 24, 24], fill=(255, 255, 100, 255))
        self.icons[ApplicationState.CONFIGURING] = configuring_img
    
    def setup(self):
        """Setup the system tray icon and menu."""
        if not PYSYSTRAY_AVAILABLE:
            self.logger.error("pystray not available, system tray disabled")
            return False
        
        try:
            # Create menu
            menu = self._create_menu()
            
            # Create icon
            self.icon = Icon(
                "Voice Dictation Assistant",
                self.icons[ApplicationState.IDLE],
                "Voice Dictation Assistant",
                menu
            )
            
            self.logger.info("System tray setup completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to setup system tray: {e}")
            return False
    
    def _create_menu(self):
        """Create the system tray menu."""
        return Menu(
            MenuItem("Status", self._status_item, enabled=False),
            MenuItem("Toggle Recording", self._toggle_recording),
            MenuItem("Analytics Dashboard", self._show_analytics),
            MenuItem("Settings", self._open_settings),
            MenuItem("About", self._show_about),
            MenuItem("Exit", self._exit_app)
        )
    
    def run(self):
        """Run the system tray application."""
        if not self.icon:
            self.logger.error("System tray icon not initialized")
            return
        
        try:
            self.icon.run()
        except Exception as e:
            self.logger.error(f"System tray run error: {e}")
    
    def update_state(self, state: ApplicationState):
        """Update the system tray icon based on application state."""
        if not self.icon or state not in self.icons:
            return
        
        try:
            self.current_state = state
            self.icon.icon = self.icons[state]
            self.icon.title = f"Voice Dictation Assistant - {state.value.title()}"
            
            # Update menu status item
            if hasattr(self, '_status_item'):
                self._status_item.text = f"Status: {state.value.title()}"
            
        except Exception as e:
            self.logger.error(f"Failed to update system tray state: {e}")
    
    def show_notification(self, title: str, message: str, duration: int = 3):
        """Show a system notification."""
        if not self.notifier:
            return
        
        try:
            self.notifier.show_toast(
                title,
                message,
                duration=duration,
                threaded=True
            )
        except Exception as e:
            self.logger.error(f"Failed to show notification: {e}")
    
    def _on_state_change(self, new_state: ApplicationState):
        """Handle application state changes."""
        self.update_state(new_state)
        
        # Show notifications for important state changes
        if new_state == ApplicationState.ERROR:
            self.show_notification(
                "Voice Dictation Assistant",
                "An error occurred. Check the logs for details.",
                duration=5
            )
        elif new_state == ApplicationState.RECORDING:
            self.show_notification(
                "Voice Dictation Assistant",
                "Recording started. Press the hotkey again to stop.",
                duration=3
            )
    
    def _on_error(self, error_message: str):
        """Handle error notifications."""
        self.show_notification(
            "Voice Dictation Assistant - Error",
            error_message,
            duration=5
        )
    
    def _status_item(self, icon, item):
        """Status menu item (read-only)."""
        pass
    
    def _toggle_recording(self, icon, item):
        """Toggle recording state."""
        try:
            self.toggle_recording_callback()
            self.logger.info("Recording toggled via system tray")
        except Exception as e:
            self.logger.error(f"Failed to toggle recording: {e}")
    
    def _show_analytics(self, icon, item):
        """Show analytics dashboard."""
        try:
            self.show_analytics_callback()
            self.logger.info("Analytics dashboard requested via system tray")
        except Exception as e:
            self.logger.error(f"Failed to show analytics dashboard: {e}")
    
    def _open_settings(self, icon, item):
        """Open settings dialog."""
        try:
            self.show_config_callback()
            self.logger.info("Settings requested via system tray")
        except Exception as e:
            self.logger.error(f"Failed to open settings: {e}")
    
    def _show_about(self, icon, item):
        """Show about dialog."""
        try:
            about_text = """
Voice Dictation Assistant
Version 1.0.0

A powerful voice dictation tool that uses AI to enhance your speech-to-text experience.

Features:
• Real-time speech recognition
• AI-powered text enhancement
• Context-aware formatting
• Performance monitoring and analytics
• Privacy-focused design

For support and updates, visit the project repository.
            """
            
            self.show_notification(
                "About Voice Dictation Assistant",
                about_text.strip(),
                duration=10
            )
            
        except Exception as e:
            self.logger.error(f"Failed to show about dialog: {e}")
    
    def _exit_app(self, icon, item):
        """Exit the application."""
        try:
            self.logger.info("Exit requested via system tray")
            self.shutdown_callback()
        except Exception as e:
            self.logger.error(f"Failed to exit application: {e}")
    
    def stop(self):
        """Stop the system tray application."""
        if self.icon:
            try:
                self.icon.stop()
                self.logger.info("System tray stopped")
            except Exception as e:
                self.logger.error(f"Failed to stop system tray: {e}")
    
    def shutdown(self):
        """Shutdown the system tray application."""
        self.stop()


def create_system_tray_app(toggle_recording_callback: Callable,
                          show_analytics_callback: Callable,
                          show_config_callback: Callable,
                          shutdown_callback: Callable) -> Optional[SystemTrayApp]:
    """
    Create a system tray application.
    
    Args:
        toggle_recording_callback: Callback for toggling recording
        show_analytics_callback: Callback for showing analytics dashboard
        show_config_callback: Callback for showing configuration
        shutdown_callback: Callback for shutting down the application
    
    Returns:
        SystemTrayApp instance or None if not available
    """
    if not PYSYSTRAY_AVAILABLE:
        logging.getLogger(__name__).warning("pystray not available, system tray disabled")
        return None
    
    try:
        app = SystemTrayApp(
            toggle_recording_callback,
            show_analytics_callback,
            show_config_callback,
            shutdown_callback
        )
        
        if app.setup():
            return app
        else:
            return None
            
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to create system tray app: {e}")
        return None 
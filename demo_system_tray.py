#!/usr/bin/env python3
"""
System Tray Demonstration Script

This script demonstrates the system tray functionality
by creating a simple application with system tray integration.
"""

import sys
import time
import logging
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.application_controller import ApplicationController
from src.core.system_tray_app import create_system_tray_app


def setup_logging():
    """Setup logging for the demonstration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def main():
    """Main demonstration function."""
    print("=== System Tray Demonstration ===")
    print("This will create a system tray icon that you can interact with.")
    print("Right-click the icon to see the menu options.")
    print("Press Ctrl+C to exit.")
    print()
    
    setup_logging()
    
    try:
        # Create application controller
        app_controller = ApplicationController()
        
        # Initialize the controller
        if not app_controller.initialize():
            print("❌ Failed to initialize application controller")
            return
        
        # Create system tray app
        tray_app = create_system_tray_app(app_controller)
        
        if not tray_app:
            print("❌ Failed to create system tray application")
            return
        
        print("✅ System tray application created successfully")
        print("Look for the system tray icon in your Windows taskbar")
        print("Right-click the icon to access the menu")
        print()
        
        # Run the system tray application
        print("Starting system tray application...")
        print("The application will run until you exit via the system tray menu")
        print("or press Ctrl+C in this terminal.")
        print()
        
        tray_app.run()
        
    except KeyboardInterrupt:
        print("\nReceived interrupt signal, shutting down...")
    except Exception as e:
        print(f"❌ Error during demonstration: {e}")
    finally:
        if 'app_controller' in locals():
            app_controller.shutdown()
        print("Demonstration completed.")


if __name__ == "__main__":
    main() 
#!/usr/bin/env python3
"""
Test script for the System Tray Application

This script tests the system tray functionality independently
to ensure it works correctly before integration.
"""

import sys
import os
import time
import logging
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.system_tray_app import create_system_tray_app
from src.core.application_controller import ApplicationController
from src.core.types import ApplicationState


def setup_logging():
    """Setup logging for the test."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def test_system_tray_creation():
    """Test creating the system tray application."""
    print("Testing system tray application creation...")
    
    try:
        # Create a mock application controller
        app_controller = ApplicationController()
        
        # Create system tray app
        tray_app = create_system_tray_app(app_controller)
        
        if tray_app:
            print("✅ System tray application created successfully")
            return tray_app
        else:
            print("❌ Failed to create system tray application")
            return None
            
    except Exception as e:
        print(f"❌ Error creating system tray application: {e}")
        return None


def test_system_tray_functionality(tray_app):
    """Test basic system tray functionality."""
    if not tray_app:
        print("❌ No tray app to test")
        return
    
    print("Testing system tray functionality...")
    
    try:
        # Test state updates
        print("Testing state updates...")
        tray_app.update_state(ApplicationState.RECORDING)
        time.sleep(1)
        
        tray_app.update_state(ApplicationState.PROCESSING)
        time.sleep(1)
        
        tray_app.update_state(ApplicationState.IDLE)
        time.sleep(1)
        
        # Test notifications
        print("Testing notifications...")
        tray_app.show_notification("Test", "This is a test notification")
        time.sleep(2)
        
        print("✅ System tray functionality tests completed")
        
    except Exception as e:
        print(f"❌ Error testing system tray functionality: {e}")


def test_system_tray_integration():
    """Test system tray integration with application controller."""
    print("Testing system tray integration...")
    
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
        
        print("✅ System tray integration test completed")
        
        # Cleanup
        app_controller.shutdown()
        
    except Exception as e:
        print(f"❌ Error testing system tray integration: {e}")


def main():
    """Main test function."""
    print("=== System Tray Application Test ===")
    
    setup_logging()
    
    # Test 1: Basic creation
    tray_app = test_system_tray_creation()
    
    # Test 2: Functionality (if creation succeeded)
    if tray_app:
        test_system_tray_functionality(tray_app)
    
    # Test 3: Integration
    test_system_tray_integration()
    
    print("\n=== Test Summary ===")
    print("System tray application tests completed.")
    print("Check the logs above for any errors or warnings.")


if __name__ == "__main__":
    main() 
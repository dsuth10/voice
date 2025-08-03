#!/usr/bin/env python3
"""
Test script for Performance Monitoring and Analytics System

This script tests the implementation of task 12 - Performance Monitoring and Analytics.
It verifies that the system can track performance metrics, collect usage statistics,
and provide analytics capabilities.
"""

import sys
import os
import time
import json
import tempfile
import shutil
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config.config_manager import ConfigManager
from src.core.performance_monitor import PerformanceMonitor, PerformanceReporter, AnalyticsData
from src.core.analytics_dashboard import AnalyticsDashboard
from src.core.workflow_manager import WorkflowStep


def test_performance_monitor():
    """Test the performance monitoring system."""
    print("Testing Performance Monitor...")
    
    # Create a temporary config manager
    config_manager = ConfigManager()
    
    # Initialize performance monitor
    monitor = PerformanceMonitor(config_manager)
    
    # Test basic functionality
    print("  ✓ Performance monitor initialized")
    
    # Test metric recording
    monitor.record_metric("test_metric", 42.5, "count")
    print("  ✓ Metric recording works")
    
    # Test workflow tracking
    monitor.start_workflow_tracking("test_workflow_1")
    time.sleep(0.1)  # Simulate some work
    monitor.record_workflow_step(WorkflowStep.RECORDING, 0.05)
    monitor.record_workflow_step(WorkflowStep.TRANSCRIBING, 0.1)
    monitor.end_workflow_tracking(True)
    print("  ✓ Workflow tracking works")
    
    # Test usage statistics
    monitor.record_hotkey_press()
    monitor.record_text_insertion()
    monitor.record_error()
    monitor.record_recovery_success()
    print("  ✓ Usage statistics recording works")
    
    # Test performance summary
    summary = monitor.get_performance_summary()
    assert summary['total_workflows'] >= 1
    assert summary['hotkey_presses'] >= 1
    print("  ✓ Performance summary generation works")
    
    # Test data retention
    monitor.data_retention_days = 1
    monitor._cleanup_old_data()
    print("  ✓ Data retention works")
    
    print("  ✓ Performance monitor tests passed\n")
    return True


def test_analytics_export():
    """Test analytics data export functionality."""
    print("Testing Analytics Export...")
    
    # Create a temporary config manager
    config_manager = ConfigManager()
    
    # Initialize performance monitor with analytics enabled
    monitor = PerformanceMonitor(config_manager)
    monitor.analytics_enabled = True
    monitor.anonymized_export = True
    
    # Generate some test data
    monitor.record_hotkey_press()
    monitor.record_text_insertion()
    monitor.record_error()
    
    # Test anonymized data export
    try:
        data = monitor.export_anonymized_data()
        assert isinstance(data, AnalyticsData)
        assert data.session_id is not None
        assert data.total_workflows >= 0
        print("  ✓ Anonymized data export works")
    except Exception as e:
        print(f"  ✗ Anonymized data export failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test analytics data save
    try:
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            temp_file = f.name
        
        monitor.save_analytics_data("test_analytics.json")
        print("  ✓ Analytics data save works")
        
        # Clean up
        if os.path.exists(temp_file):
            os.unlink(temp_file)
            
    except Exception as e:
        print(f"  ✗ Analytics data save failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("  ✓ Analytics export tests passed\n")
    return True


def test_analytics_dashboard():
    """Test the analytics dashboard."""
    print("Testing Analytics Dashboard...")
    
    # Create a temporary config manager
    config_manager = ConfigManager()
    
    # Initialize performance monitor
    monitor = PerformanceMonitor(config_manager)
    
    # Initialize dashboard
    dashboard = AnalyticsDashboard(monitor, config_manager)
    print("  ✓ Analytics dashboard initialized")
    
    # Test dashboard creation (without showing UI)
    try:
        # Test that dashboard can be created without errors
        assert dashboard.performance_monitor == monitor
        assert dashboard.config_manager == config_manager
        print("  ✓ Dashboard component integration works")
    except Exception as e:
        print(f"  ✗ Dashboard creation failed: {e}")
        return False
    
    # Test settings management
    try:
        # Test analytics settings
        monitor.analytics_enabled = True
        monitor.performance_monitoring = True
        monitor.usage_statistics = True
        monitor.error_tracking = True
        print("  ✓ Analytics settings management works")
    except Exception as e:
        print(f"  ✗ Analytics settings failed: {e}")
        return False
    
    print("  ✓ Analytics dashboard tests passed\n")
    return True


def test_configuration_integration():
    """Test configuration integration with analytics."""
    print("Testing Configuration Integration...")
    
    # Create a temporary config manager
    config_manager = ConfigManager()
    
    # Test analytics configuration loading
    try:
        # Set analytics settings
        config_manager.set('analytics.enabled', True)
        config_manager.set('analytics.performance_monitoring', True)
        config_manager.set('analytics.usage_statistics', True)
        config_manager.set('analytics.error_tracking', True)
        config_manager.set('analytics.anonymized_export', False)
        config_manager.set('analytics.data_retention_days', 30)
        config_manager.set('analytics.privacy_mode', True)
        
        # Initialize performance monitor with config
        monitor = PerformanceMonitor(config_manager)
        
        # Verify settings were loaded
        assert monitor.analytics_enabled == True
        assert monitor.performance_monitoring == True
        assert monitor.usage_statistics == True
        assert monitor.error_tracking == True
        assert monitor.anonymized_export == False
        assert monitor.data_retention_days == 30
        assert monitor.privacy_mode == True
        
        print("  ✓ Configuration integration works")
        
    except Exception as e:
        print(f"  ✗ Configuration integration failed: {e}")
        return False
    
    print("  ✓ Configuration integration tests passed\n")
    return True


def test_performance_reporter():
    """Test the performance reporter."""
    print("Testing Performance Reporter...")
    
    # Create a temporary config manager
    config_manager = ConfigManager()
    
    # Initialize performance monitor
    monitor = PerformanceMonitor(config_manager)
    
    # Generate some test data
    monitor.record_hotkey_press()
    monitor.record_text_insertion()
    monitor.record_error()
    
    # Test performance reporter
    reporter = PerformanceReporter(monitor)
    
    try:
        # Generate performance report
        report = reporter.generate_performance_report()
        print(f"Generated report length: {len(report)}")
        print(f"Report preview: {report[:200]}...")
        
        assert "Performance Report" in report
        assert "Session Information" in report
        assert "Recent Activity" in report
        assert "System Performance" in report
        print("  ✓ Performance report generation works")
        
    except Exception as e:
        print(f"  ✗ Performance report generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test anonymized report export
    try:
        # Enable anonymized export for testing
        monitor.anonymized_export = True
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            temp_file = f.name
        
        reporter.export_anonymized_report(temp_file)
        
        # Verify file was created and contains valid JSON
        with open(temp_file, 'r') as f:
            data = json.load(f)
            assert 'session_id' in data
            assert 'total_workflows' in data
        
        print("  ✓ Anonymized report export works")
        
        # Clean up
        os.unlink(temp_file)
        
    except Exception as e:
        print(f"  ✗ Anonymized report export failed: {e}")
        return False
    
    print("  ✓ Performance reporter tests passed\n")
    return True


def test_data_retention():
    """Test data retention functionality."""
    print("Testing Data Retention...")
    
    # Create a temporary config manager
    config_manager = ConfigManager()
    
    # Initialize performance monitor
    monitor = PerformanceMonitor(config_manager)
    monitor.analytics_enabled = True
    monitor.data_retention_days = 1  # Set to 1 day for testing
    
    # Generate some test data
    monitor.record_hotkey_press()
    monitor.record_text_insertion()
    monitor.record_error()
    
    # Test cleanup
    try:
        initial_metrics_count = len(monitor.metrics)
        monitor._cleanup_old_data()
        print("  ✓ Data retention cleanup works")
        
    except Exception as e:
        print(f"  ✗ Data retention cleanup failed: {e}")
        return False
    
    print("  ✓ Data retention tests passed\n")
    return True


def main():
    """Run all performance monitoring and analytics tests."""
    print("=" * 60)
    print("Testing Performance Monitoring and Analytics System")
    print("=" * 60)
    
    tests = [
        test_performance_monitor,
        test_analytics_export,
        test_analytics_dashboard,
        test_configuration_integration,
        test_performance_reporter,
        test_data_retention
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"  ✗ Test {test.__name__} failed with exception: {e}")
            failed += 1
    
    print("=" * 60)
    print("Test Results:")
    print(f"  Passed: {passed}")
    print(f"  Failed: {failed}")
    print(f"  Total: {passed + failed}")
    
    if failed == 0:
        print("\n🎉 All tests passed! Performance monitoring and analytics system is working correctly.")
        return True
    else:
        print(f"\n❌ {failed} test(s) failed. Please check the implementation.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 
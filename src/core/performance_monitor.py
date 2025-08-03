"""
Performance Monitoring and Usage Statistics for Voice Dictation Assistant

This module provides comprehensive performance measurement, resource monitoring,
and anonymized usage statistics collection to support optimization and troubleshooting.
"""

import threading
import time
import psutil
import json
import hashlib
import os
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta
import logging

from .application_controller import ApplicationState
from .workflow_manager import WorkflowStep


class MetricType(Enum):
    """Types of performance metrics."""
    TIMING = "timing"
    RESOURCE = "resource"
    USAGE = "usage"
    ERROR = "error"


@dataclass
class PerformanceMetric:
    """Performance metric data structure."""
    timestamp: datetime
    metric_type: MetricType
    name: str
    value: float
    unit: str
    context: Optional[Dict[str, Any]] = None


@dataclass
class WorkflowPerformance:
    """Workflow performance data."""
    workflow_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    total_duration: Optional[float] = None
    step_durations: Dict[WorkflowStep, float] = None
    success: bool = False
    error_message: Optional[str] = None
    
    def __post_init__(self):
        if self.step_durations is None:
            self.step_durations = {}


@dataclass
class SystemResources:
    """System resource usage data."""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    disk_usage_percent: float
    network_io: Dict[str, float] = None
    
    def __post_init__(self):
        if self.network_io is None:
            self.network_io = {}


@dataclass
class UsageStatistics:
    """Usage statistics data."""
    session_start: datetime
    session_end: Optional[datetime] = None
    total_workflows: int = 0
    successful_workflows: int = 0
    failed_workflows: int = 0
    total_recording_time: float = 0.0
    total_processing_time: float = 0.0
    average_workflow_duration: float = 0.0
    error_count: int = 0
    recovery_success_count: int = 0
    hotkey_presses: int = 0
    text_insertions: int = 0


@dataclass
class AnalyticsData:
    """Analytics data structure for export."""
    session_id: str
    session_duration_hours: float
    total_workflows: int
    success_rate: float
    average_workflow_duration: float
    total_recording_time_hours: float
    total_processing_time_hours: float
    error_rate: float
    recovery_success_rate: float
    hotkey_presses: int
    text_insertions: int
    system_performance: Dict[str, float]
    export_timestamp: str


class PerformanceMonitor:
    """
    Performance monitoring system for tracking application performance.
    
    This class provides comprehensive performance measurement including
    workflow timing, system resource usage, and usage statistics.
    """
    
    def __init__(self, config_manager=None, monitoring_interval: float = 1.0):
        """
        Initialize the performance monitor.
        
        Args:
            config_manager: Configuration manager for analytics settings
            monitoring_interval: Interval in seconds for resource monitoring
        """
        self.logger = logging.getLogger(__name__)
        self.config_manager = config_manager
        
        # Configuration
        self.monitoring_interval = monitoring_interval
        self.enabled = True
        
        # Analytics settings
        self.analytics_enabled = False
        self.performance_monitoring = True
        self.usage_statistics = True
        self.error_tracking = True
        self.session_tracking = True
        self.anonymized_export = False
        self.data_retention_days = 30
        self.upload_interval_hours = 24
        self.include_system_resources = True
        self.include_workflow_timing = True
        self.privacy_mode = True
        
        # Load analytics settings from config
        if config_manager:
            self._load_analytics_settings()
        
        # Data storage
        self.metrics: List[PerformanceMetric] = []
        self.workflow_performance: List[WorkflowPerformance] = []
        self.system_resources: List[SystemResources] = []
        self.usage_stats = UsageStatistics(session_start=datetime.now())
        
        # Threading
        self.monitoring_thread = None
        self.stop_monitoring = threading.Event()
        self.data_lock = threading.Lock()
        
        # Callbacks
        self.metric_callbacks: List[Callable[[PerformanceMetric], None]] = []
        self.resource_callbacks: List[Callable[[SystemResources], None]] = []
        self.usage_callbacks: List[Callable[[UsageStatistics], None]] = []
        
        # Current workflow tracking
        self.current_workflow: Optional[WorkflowPerformance] = None
        
        # Analytics storage
        self.analytics_dir = self._get_analytics_directory()
        
        self.logger.info("PerformanceMonitor initialized")
    
    def _load_analytics_settings(self):
        """Load analytics settings from configuration."""
        try:
            self.analytics_enabled = self.config_manager.get('analytics.enabled', False)
            self.performance_monitoring = self.config_manager.get('analytics.performance_monitoring', True)
            self.usage_statistics = self.config_manager.get('analytics.usage_statistics', True)
            self.error_tracking = self.config_manager.get('analytics.error_tracking', True)
            self.session_tracking = self.config_manager.get('analytics.session_tracking', True)
            self.anonymized_export = self.config_manager.get('analytics.anonymized_export', False)
            self.data_retention_days = self.config_manager.get('analytics.data_retention_days', 30)
            self.upload_interval_hours = self.config_manager.get('analytics.upload_interval_hours', 24)
            self.include_system_resources = self.config_manager.get('analytics.include_system_resources', True)
            self.include_workflow_timing = self.config_manager.get('analytics.include_workflow_timing', True)
            self.privacy_mode = self.config_manager.get('analytics.privacy_mode', True)
            
            self.logger.info(f"Analytics settings loaded: enabled={self.analytics_enabled}")
            
        except Exception as e:
            self.logger.error(f"Failed to load analytics settings: {e}")
    
    def _get_analytics_directory(self) -> str:
        """Get the analytics data directory."""
        app_data_dir = os.environ.get('APPDATA', os.path.expanduser('~'))
        analytics_dir = os.path.join(app_data_dir, 'VoiceDictationAssistant', 'analytics')
        os.makedirs(analytics_dir, exist_ok=True)
        return analytics_dir
    
    def start_monitoring(self):
        """Start the performance monitoring thread."""
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.logger.warning("Monitoring already running")
            return
        
        self.stop_monitoring.clear()
        self.monitoring_thread = threading.Thread(target=self._monitor_resources, daemon=True)
        self.monitoring_thread.start()
        self.logger.info("Performance monitoring started")
    
    def stop_monitoring(self):
        """Stop the performance monitoring thread."""
        self.stop_monitoring.set()
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5.0)
        self.logger.info("Performance monitoring stopped")
    
    def _monitor_resources(self):
        """Monitor system resources in background thread."""
        while not self.stop_monitoring.is_set():
            try:
                # Only monitor if enabled and system resources are included
                if not self.performance_monitoring or not self.include_system_resources:
                    time.sleep(self.monitoring_interval)
                    continue
                
                # Get system resources
                cpu_percent = psutil.cpu_percent(interval=0.1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                network = psutil.net_io_counters()
                
                # Create resource data
                resources = SystemResources(
                    timestamp=datetime.now(),
                    cpu_percent=cpu_percent,
                    memory_percent=memory.percent,
                    memory_used_mb=memory.used / (1024 * 1024),
                    disk_usage_percent=disk.percent,
                    network_io={
                        'bytes_sent': network.bytes_sent,
                        'bytes_recv': network.bytes_recv,
                        'packets_sent': network.packets_sent,
                        'packets_recv': network.packets_recv
                    }
                )
                
                # Store and notify
                with self.data_lock:
                    self.system_resources.append(resources)
                
                # Notify callbacks
                for callback in self.resource_callbacks:
                    try:
                        callback(resources)
                    except Exception as e:
                        self.logger.error(f"Resource callback error: {e}")
                
                # Clean up old data based on retention settings
                self._cleanup_old_data()
                
                time.sleep(self.monitoring_interval)
                
            except Exception as e:
                self.logger.error(f"Error in resource monitoring: {e}")
                time.sleep(self.monitoring_interval)
    
    def _cleanup_old_data(self):
        """Clean up old data based on retention settings."""
        if not self.analytics_enabled:
            return
        
        cutoff_time = datetime.now() - timedelta(days=self.data_retention_days)
        
        with self.data_lock:
            # Clean up metrics
            self.metrics = [m for m in self.metrics if m.timestamp > cutoff_time]
            
            # Clean up workflow performance
            self.workflow_performance = [w for w in self.workflow_performance 
                                       if w.end_time and w.end_time > cutoff_time]
            
            # Clean up system resources (keep last 1000 entries regardless)
            if len(self.system_resources) > 1000:
                self.system_resources = self.system_resources[-1000:]
    
    def record_metric(self, name: str, value: float, unit: str, 
                     metric_type: MetricType = MetricType.TIMING,
                     context: Optional[Dict[str, Any]] = None):
        """Record a performance metric."""
        if not self.performance_monitoring:
            return
        
        metric = PerformanceMetric(
            timestamp=datetime.now(),
            metric_type=metric_type,
            name=name,
            value=value,
            unit=unit,
            context=context
        )
        
        with self.data_lock:
            self.metrics.append(metric)
        
        # Notify callbacks
        for callback in self.metric_callbacks:
            try:
                callback(metric)
            except Exception as e:
                self.logger.error(f"Metric callback error: {e}")
        
        self.logger.debug(f"Recorded metric: {name} = {value} {unit}")
    
    def start_workflow_tracking(self, workflow_id: str):
        """Start tracking a new workflow."""
        if not self.include_workflow_timing:
            return
        
        self.current_workflow = WorkflowPerformance(
            workflow_id=workflow_id,
            start_time=datetime.now()
        )
        
        self.logger.info(f"Started tracking workflow: {workflow_id}")
    
    def record_workflow_step(self, step: WorkflowStep, duration: float):
        """Record the duration of a workflow step."""
        if not self.include_workflow_timing or not self.current_workflow:
            return
        
        self.current_workflow.step_durations[step] = duration
        self.logger.debug(f"Workflow step {step.value}: {duration:.3f}s")
    
    def end_workflow_tracking(self, success: bool, error_message: Optional[str] = None):
        """End tracking the current workflow."""
        if not self.include_workflow_timing or not self.current_workflow:
            return
        
        self.current_workflow.end_time = datetime.now()
        self.current_workflow.total_duration = (
            self.current_workflow.end_time - self.current_workflow.start_time
        ).total_seconds()
        self.current_workflow.success = success
        self.current_workflow.error_message = error_message
        
        # Store workflow performance
        with self.data_lock:
            self.workflow_performance.append(self.current_workflow)
        
        # Update usage statistics
        if self.usage_statistics:
            self._update_usage_stats(self.current_workflow)
        
        self.logger.info(f"Ended workflow tracking: {self.current_workflow.workflow_id} "
                        f"({self.current_workflow.total_duration:.3f}s, success={success})")
        
        self.current_workflow = None
    
    def _update_usage_stats(self, workflow: WorkflowPerformance):
        """Update usage statistics with workflow data."""
        self.usage_stats.total_workflows += 1
        
        if workflow.success:
            self.usage_stats.successful_workflows += 1
        else:
            self.usage_stats.failed_workflows += 1
            if self.error_tracking:
                self.usage_stats.error_count += 1
        
        if workflow.total_duration:
            self.usage_stats.average_workflow_duration = (
                (self.usage_stats.average_workflow_duration * (self.usage_stats.total_workflows - 1) +
                 workflow.total_duration) / self.usage_stats.total_workflows
            )
        
        # Update step-specific times
        if WorkflowStep.RECORDING in workflow.step_durations:
            self.usage_stats.total_recording_time += workflow.step_durations[WorkflowStep.RECORDING]
        
        processing_steps = [WorkflowStep.TRANSCRIBING, WorkflowStep.ENHANCING, 
                          WorkflowStep.FORMATTING, WorkflowStep.INSERTING]
        for step in processing_steps:
            if step in workflow.step_durations:
                self.usage_stats.total_processing_time += workflow.step_durations[step]
    
    def record_hotkey_press(self):
        """Record a hotkey press event."""
        if not self.usage_statistics:
            return
        
        self.usage_stats.hotkey_presses += 1
        self.record_metric("hotkey_press", 1, "count", MetricType.USAGE)
    
    def record_text_insertion(self):
        """Record a text insertion event."""
        if not self.usage_statistics:
            return
        
        self.usage_stats.text_insertions += 1
        self.record_metric("text_insertion", 1, "count", MetricType.USAGE)
    
    def record_error(self):
        """Record an error event."""
        if not self.error_tracking:
            return
        
        self.usage_stats.error_count += 1
        self.record_metric("error", 1, "count", MetricType.ERROR)
    
    def record_recovery_success(self):
        """Record a successful recovery event."""
        if not self.error_tracking:
            return
        
        self.usage_stats.recovery_success_count += 1
        self.record_metric("recovery_success", 1, "count", MetricType.USAGE)
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get a summary of performance data."""
        with self.data_lock:
            recent_workflows = [w for w in self.workflow_performance 
                              if w.end_time and (datetime.now() - w.end_time).seconds < 3600]
            
            if recent_workflows:
                avg_duration = sum(w.total_duration for w in recent_workflows) / len(recent_workflows)
                success_rate = sum(1 for w in recent_workflows if w.success) / len(recent_workflows) * 100
            else:
                avg_duration = 0.0
                success_rate = 0.0
            
            # Get recent system resources
            recent_resources = self.system_resources[-10:] if self.system_resources else []
            avg_cpu = sum(r.cpu_percent for r in recent_resources) / len(recent_resources) if recent_resources else 0.0
            avg_memory = sum(r.memory_percent for r in recent_resources) / len(recent_resources) if recent_resources else 0.0
            
            return {
                'total_workflows': self.usage_stats.total_workflows,
                'success_rate': success_rate,
                'average_duration': avg_duration,
                'recent_workflows': len(recent_workflows),
                'average_cpu_usage': avg_cpu,
                'average_memory_usage': avg_memory,
                'session_duration': (datetime.now() - self.usage_stats.session_start).total_seconds(),
                'hotkey_presses': self.usage_stats.hotkey_presses,
                'text_insertions': self.usage_stats.text_insertions,
                'error_count': self.usage_stats.error_count,
                'recovery_success_count': self.usage_stats.recovery_success_count
            }
    
    def get_workflow_performance(self, hours: int = 24) -> List[WorkflowPerformance]:
        """Get workflow performance data for the specified time period."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with self.data_lock:
            return [w for w in self.workflow_performance 
                   if w.end_time and w.end_time > cutoff_time]
    
    def get_system_resources(self, minutes: int = 60) -> List[SystemResources]:
        """Get system resource data for the specified time period."""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        
        with self.data_lock:
            return [r for r in self.system_resources if r.timestamp > cutoff_time]
    
    def get_usage_statistics(self) -> UsageStatistics:
        """Get current usage statistics."""
        return self.usage_stats
    
    def add_metric_callback(self, callback: Callable[[PerformanceMetric], None]):
        """Add callback for metric notifications."""
        self.metric_callbacks.append(callback)
    
    def add_resource_callback(self, callback: Callable[[SystemResources], None]):
        """Add callback for resource notifications."""
        self.resource_callbacks.append(callback)
    
    def add_usage_callback(self, callback: Callable[[UsageStatistics], None]):
        """Add callback for usage statistics notifications."""
        self.usage_callbacks.append(callback)
    
    def export_anonymized_data(self) -> AnalyticsData:
        """Export anonymized usage data for analysis."""
        if not self.anonymized_export:
            raise ValueError("Anonymized export is not enabled")
        
        # Create anonymized session ID
        session_hash = hashlib.sha256(
            self.usage_stats.session_start.isoformat().encode()
        ).hexdigest()[:8]
        
        # Calculate system performance averages
        recent_resources = self.system_resources[-100:] if self.system_resources else []
        system_performance = {
            'avg_cpu_percent': sum(r.cpu_percent for r in recent_resources) / len(recent_resources) if recent_resources else 0.0,
            'avg_memory_percent': sum(r.memory_percent for r in recent_resources) / len(recent_resources) if recent_resources else 0.0,
            'avg_memory_used_mb': sum(r.memory_used_mb for r in recent_resources) / len(recent_resources) if recent_resources else 0.0,
            'avg_disk_usage_percent': sum(r.disk_usage_percent for r in recent_resources) / len(recent_resources) if recent_resources else 0.0
        }
        
        return AnalyticsData(
            session_id=session_hash,
            session_duration_hours=(datetime.now() - self.usage_stats.session_start).total_seconds() / 3600,
            total_workflows=self.usage_stats.total_workflows,
            success_rate=(self.usage_stats.successful_workflows / max(self.usage_stats.total_workflows, 1)) * 100,
            average_workflow_duration=self.usage_stats.average_workflow_duration,
            total_recording_time_hours=self.usage_stats.total_recording_time / 3600,
            total_processing_time_hours=self.usage_stats.total_processing_time / 3600,
            error_rate=(self.usage_stats.error_count / max(self.usage_stats.total_workflows, 1)) * 100,
            recovery_success_rate=(self.usage_stats.recovery_success_count / max(self.usage_stats.error_count, 1)) * 100,
            hotkey_presses=self.usage_stats.hotkey_presses,
            text_insertions=self.usage_stats.text_insertions,
            system_performance=system_performance,
            export_timestamp=datetime.now().isoformat()
        )
    
    def save_analytics_data(self, filename: Optional[str] = None) -> str:
        """Save analytics data to file."""
        if not self.analytics_enabled:
            raise ValueError("Analytics is not enabled")
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"analytics_{timestamp}.json"
        
        filepath = os.path.join(self.analytics_dir, filename)
        
        try:
            data = {
                'metrics': [asdict(m) for m in self.metrics],
                'workflow_performance': [asdict(w) for w in self.workflow_performance],
                'system_resources': [asdict(r) for r in self.system_resources],
                'usage_statistics': asdict(self.usage_stats),
                'export_timestamp': datetime.now().isoformat()
            }
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            self.logger.info(f"Analytics data saved to {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"Failed to save analytics data: {e}")
            raise
    
    def save_anonymized_report(self, filename: Optional[str] = None) -> str:
        """Save anonymized analytics report."""
        if not self.anonymized_export:
            raise ValueError("Anonymized export is not enabled")
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"anonymized_report_{timestamp}.json"
        
        filepath = os.path.join(self.analytics_dir, filename)
        
        try:
            data = self.export_anonymized_data()
            
            with open(filepath, 'w') as f:
                json.dump(asdict(data), f, indent=2)
            
            self.logger.info(f"Anonymized report saved to {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"Failed to save anonymized report: {e}")
            raise
    
    def clear_data(self):
        """Clear all performance data."""
        with self.data_lock:
            self.metrics.clear()
            self.workflow_performance.clear()
            self.system_resources.clear()
            self.usage_stats = UsageStatistics(session_start=datetime.now())
        
        self.logger.info("Performance data cleared")
    
    def shutdown(self):
        """Shutdown the performance monitor."""
        self.logger.info("Shutting down performance monitor")
        
        try:
            # Stop monitoring
            self.stop_monitoring()
            
            # End current session
            self.usage_stats.session_end = datetime.now()
            
            # Save final analytics data if enabled
            if self.analytics_enabled:
                try:
                    self.save_analytics_data("final_session_data.json")
                except Exception as e:
                    self.logger.error(f"Failed to save final analytics data: {e}")
            
            # Clear callbacks
            self.metric_callbacks.clear()
            self.resource_callbacks.clear()
            self.usage_callbacks.clear()
            
            self.logger.info("Performance monitor shutdown completed")
            
        except Exception as e:
            self.logger.error(f"Error during performance monitor shutdown: {e}")


class PerformanceReporter:
    """Performance reporting and analysis system."""
    
    def __init__(self, monitor: PerformanceMonitor):
        self.logger = logging.getLogger(__name__)
        self.monitor = monitor
    
    def generate_performance_report(self) -> str:
        """Generate a human-readable performance report."""
        summary = self.monitor.get_performance_summary()
        
        report = f"""
Performance Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'=' * 50}

Session Information:
- Session Duration: {summary['session_duration']:.1f} seconds
- Total Workflows: {summary['total_workflows']}
- Success Rate: {summary['success_rate']:.1f}%
- Average Workflow Duration: {summary['average_duration']:.3f} seconds

Recent Activity (Last Hour):
- Recent Workflows: {summary['recent_workflows']}
- Hotkey Presses: {summary['hotkey_presses']}
- Text Insertions: {summary['text_insertions']}

System Performance:
- Average CPU Usage: {summary['average_cpu_usage']:.1f}%
- Average Memory Usage: {summary['average_memory_usage']:.1f}%

Error Handling:
- Total Errors: {summary['error_count']}
- Recovery Successes: {summary['recovery_success_count']}

Analytics Settings:
- Analytics Enabled: {self.monitor.analytics_enabled}
- Performance Monitoring: {self.monitor.performance_monitoring}
- Usage Statistics: {self.monitor.usage_statistics}
- Error Tracking: {self.monitor.error_tracking}
- Privacy Mode: {self.monitor.privacy_mode}
"""
        
        return report
    
    def export_anonymized_report(self, filepath: str):
        """Export anonymized performance report."""
        try:
            data = self.monitor.export_anonymized_data()
            
            with open(filepath, 'w') as f:
                json.dump(asdict(data), f, indent=2)
            
            self.logger.info(f"Anonymized report exported to {filepath}")
            
        except Exception as e:
            self.logger.error(f"Failed to export anonymized report: {e}") 
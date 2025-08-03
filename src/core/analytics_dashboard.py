"""
Analytics Dashboard for Voice Dictation Assistant

This module provides a user interface for viewing performance metrics,
analytics data, and generating reports.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging

from .performance_monitor import PerformanceMonitor, PerformanceReporter, AnalyticsData


class AnalyticsDashboard:
    """
    Analytics dashboard for viewing performance metrics and analytics data.
    
    Provides a user interface for:
    - Viewing real-time performance metrics
    - Generating performance reports
    - Exporting analytics data
    - Configuring analytics settings
    """
    
    def __init__(self, performance_monitor: PerformanceMonitor, config_manager=None):
        """
        Initialize the analytics dashboard.
        
        Args:
            performance_monitor: Performance monitor instance
            config_manager: Configuration manager for settings
        """
        self.logger = logging.getLogger(__name__)
        self.performance_monitor = performance_monitor
        self.config_manager = config_manager
        self.reporter = PerformanceReporter(performance_monitor)
        
        # UI components
        self.root = None
        self.notebook = None
        self.metrics_frame = None
        self.reports_frame = None
        self.settings_frame = None
        
        # Data refresh
        self.refresh_interval = 5000  # 5 seconds
        self.refresh_timer = None
        
        self.logger.info("AnalyticsDashboard initialized")
    
    def show_dashboard(self):
        """Show the analytics dashboard."""
        if self.root:
            self.root.deiconify()
            self.root.lift()
            return
        
        self.root = tk.Tk()
        self.root.title("Voice Dictation Assistant - Analytics Dashboard")
        self.root.geometry("800x600")
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs
        self._create_metrics_tab()
        self._create_reports_tab()
        self._create_settings_tab()
        
        # Start auto-refresh
        self._schedule_refresh()
        
        self.logger.info("Analytics dashboard opened")
    
    def _create_metrics_tab(self):
        """Create the metrics tab."""
        self.metrics_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.metrics_frame, text="Performance Metrics")
        
        # Create scrollable frame
        canvas = tk.Canvas(self.metrics_frame)
        scrollbar = ttk.Scrollbar(self.metrics_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Session information
        session_frame = ttk.LabelFrame(scrollable_frame, text="Session Information", padding=10)
        session_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.session_duration_label = ttk.Label(session_frame, text="Session Duration: --")
        self.session_duration_label.pack(anchor=tk.W)
        
        self.total_workflows_label = ttk.Label(session_frame, text="Total Workflows: --")
        self.total_workflows_label.pack(anchor=tk.W)
        
        self.success_rate_label = ttk.Label(session_frame, text="Success Rate: --")
        self.success_rate_label.pack(anchor=tk.W)
        
        # Performance metrics
        perf_frame = ttk.LabelFrame(scrollable_frame, text="Performance Metrics", padding=10)
        perf_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.avg_duration_label = ttk.Label(perf_frame, text="Average Workflow Duration: --")
        self.avg_duration_label.pack(anchor=tk.W)
        
        self.recent_workflows_label = ttk.Label(perf_frame, text="Recent Workflows (1h): --")
        self.recent_workflows_label.pack(anchor=tk.W)
        
        self.avg_cpu_label = ttk.Label(perf_frame, text="Average CPU Usage: --")
        self.avg_cpu_label.pack(anchor=tk.W)
        
        self.avg_memory_label = ttk.Label(perf_frame, text="Average Memory Usage: --")
        self.avg_memory_label.pack(anchor=tk.W)
        
        # Usage statistics
        usage_frame = ttk.LabelFrame(scrollable_frame, text="Usage Statistics", padding=10)
        usage_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.hotkey_presses_label = ttk.Label(usage_frame, text="Hotkey Presses: --")
        self.hotkey_presses_label.pack(anchor=tk.W)
        
        self.text_insertions_label = ttk.Label(usage_frame, text="Text Insertions: --")
        self.text_insertions_label.pack(anchor=tk.W)
        
        self.error_count_label = ttk.Label(usage_frame, text="Error Count: --")
        self.error_count_label.pack(anchor=tk.W)
        
        self.recovery_success_label = ttk.Label(usage_frame, text="Recovery Successes: --")
        self.recovery_success_label.pack(anchor=tk.W)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def _create_reports_tab(self):
        """Create the reports tab."""
        self.reports_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.reports_frame, text="Reports & Export")
        
        # Report generation
        report_frame = ttk.LabelFrame(self.reports_frame, text="Generate Reports", padding=10)
        report_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(report_frame, text="Generate Performance Report", 
                  command=self._generate_performance_report).pack(pady=5)
        
        ttk.Button(report_frame, text="Export Analytics Data", 
                  command=self._export_analytics_data).pack(pady=5)
        
        ttk.Button(report_frame, text="Export Anonymized Report", 
                  command=self._export_anonymized_report).pack(pady=5)
        
        # Report display
        display_frame = ttk.LabelFrame(self.reports_frame, text="Latest Report", padding=10)
        display_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.report_text = tk.Text(display_frame, wrap=tk.WORD, height=15)
        scrollbar = ttk.Scrollbar(display_frame, orient="vertical", command=self.report_text.yview)
        self.report_text.configure(yscrollcommand=scrollbar.set)
        
        self.report_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Load initial report
        self._update_report_display()
    
    def _create_settings_tab(self):
        """Create the settings tab."""
        self.settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.settings_frame, text="Analytics Settings")
        
        # Analytics settings
        settings_frame = ttk.LabelFrame(self.settings_frame, text="Analytics Configuration", padding=10)
        settings_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Analytics enabled
        self.analytics_enabled_var = tk.BooleanVar(value=self.performance_monitor.analytics_enabled)
        ttk.Checkbutton(settings_frame, text="Enable Analytics Collection", 
                       variable=self.analytics_enabled_var,
                       command=self._update_analytics_enabled).pack(anchor=tk.W, pady=2)
        
        # Performance monitoring
        self.performance_monitoring_var = tk.BooleanVar(value=self.performance_monitor.performance_monitoring)
        ttk.Checkbutton(settings_frame, text="Enable Performance Monitoring", 
                       variable=self.performance_monitoring_var,
                       command=self._update_performance_monitoring).pack(anchor=tk.W, pady=2)
        
        # Usage statistics
        self.usage_statistics_var = tk.BooleanVar(value=self.performance_monitor.usage_statistics)
        ttk.Checkbutton(settings_frame, text="Collect Usage Statistics", 
                       variable=self.usage_statistics_var,
                       command=self._update_usage_statistics).pack(anchor=tk.W, pady=2)
        
        # Error tracking
        self.error_tracking_var = tk.BooleanVar(value=self.performance_monitor.error_tracking)
        ttk.Checkbutton(settings_frame, text="Track Error Rates", 
                       variable=self.error_tracking_var,
                       command=self._update_error_tracking).pack(anchor=tk.W, pady=2)
        
        # Anonymized export
        self.anonymized_export_var = tk.BooleanVar(value=self.performance_monitor.anonymized_export)
        ttk.Checkbutton(settings_frame, text="Allow Anonymized Export", 
                       variable=self.anonymized_export_var,
                       command=self._update_anonymized_export).pack(anchor=tk.W, pady=2)
        
        # Privacy mode
        self.privacy_mode_var = tk.BooleanVar(value=self.performance_monitor.privacy_mode)
        ttk.Checkbutton(settings_frame, text="Privacy Mode (No Personal Data)", 
                       variable=self.privacy_mode_var,
                       command=self._update_privacy_mode).pack(anchor=tk.W, pady=2)
        
        # Data retention
        retention_frame = ttk.LabelFrame(self.settings_frame, text="Data Retention", padding=10)
        retention_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(retention_frame, text="Data Retention (days):").pack(anchor=tk.W)
        self.retention_var = tk.StringVar(value=str(self.performance_monitor.data_retention_days))
        retention_entry = ttk.Entry(retention_frame, textvariable=self.retention_var, width=10)
        retention_entry.pack(anchor=tk.W, pady=2)
        
        ttk.Button(retention_frame, text="Update Retention", 
                  command=self._update_data_retention).pack(anchor=tk.W, pady=5)
        
        # Save settings
        ttk.Button(self.settings_frame, text="Save Settings", 
                  command=self._save_settings).pack(pady=10)
    
    def _schedule_refresh(self):
        """Schedule the next refresh of metrics."""
        if self.refresh_timer:
            self.root.after_cancel(self.refresh_timer)
        
        self._update_metrics_display()
        self.refresh_timer = self.root.after(self.refresh_interval, self._schedule_refresh)
    
    def _update_metrics_display(self):
        """Update the metrics display with current data."""
        try:
            summary = self.performance_monitor.get_performance_summary()
            
            # Update session information
            session_duration = summary['session_duration']
            hours = int(session_duration // 3600)
            minutes = int((session_duration % 3600) // 60)
            seconds = int(session_duration % 60)
            
            self.session_duration_label.config(
                text=f"Session Duration: {hours:02d}:{minutes:02d}:{seconds:02d}"
            )
            
            self.total_workflows_label.config(
                text=f"Total Workflows: {summary['total_workflows']}"
            )
            
            self.success_rate_label.config(
                text=f"Success Rate: {summary['success_rate']:.1f}%"
            )
            
            # Update performance metrics
            self.avg_duration_label.config(
                text=f"Average Workflow Duration: {summary['average_duration']:.3f}s"
            )
            
            self.recent_workflows_label.config(
                text=f"Recent Workflows (1h): {summary['recent_workflows']}"
            )
            
            self.avg_cpu_label.config(
                text=f"Average CPU Usage: {summary['average_cpu_usage']:.1f}%"
            )
            
            self.avg_memory_label.config(
                text=f"Average Memory Usage: {summary['average_memory_usage']:.1f}%"
            )
            
            # Update usage statistics
            self.hotkey_presses_label.config(
                text=f"Hotkey Presses: {summary['hotkey_presses']}"
            )
            
            self.text_insertions_label.config(
                text=f"Text Insertions: {summary['text_insertions']}"
            )
            
            self.error_count_label.config(
                text=f"Error Count: {summary['error_count']}"
            )
            
            self.recovery_success_label.config(
                text=f"Recovery Successes: {summary['recovery_success_count']}"
            )
            
        except Exception as e:
            self.logger.error(f"Error updating metrics display: {e}")
    
    def _update_report_display(self):
        """Update the report display."""
        try:
            report = self.reporter.generate_performance_report()
            self.report_text.delete(1.0, tk.END)
            self.report_text.insert(1.0, report)
        except Exception as e:
            self.logger.error(f"Error updating report display: {e}")
    
    def _generate_performance_report(self):
        """Generate and display a performance report."""
        try:
            report = self.reporter.generate_performance_report()
            self.report_text.delete(1.0, tk.END)
            self.report_text.insert(1.0, report)
            
            # Save report to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"performance_report_{timestamp}.txt"
            
            filepath = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                initialname=filename
            )
            
            if filepath:
                with open(filepath, 'w') as f:
                    f.write(report)
                
                messagebox.showinfo("Report Saved", f"Performance report saved to:\n{filepath}")
            
        except Exception as e:
            self.logger.error(f"Error generating performance report: {e}")
            messagebox.showerror("Error", f"Failed to generate performance report:\n{str(e)}")
    
    def _export_analytics_data(self):
        """Export analytics data."""
        try:
            if not self.performance_monitor.analytics_enabled:
                messagebox.showwarning("Analytics Disabled", 
                                    "Analytics collection is not enabled. Enable it in settings first.")
                return
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"analytics_data_{timestamp}.json"
            
            filepath = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                initialname=filename
            )
            
            if filepath:
                saved_path = self.performance_monitor.save_analytics_data(
                    os.path.basename(filepath)
                )
                
                # Copy to user-selected location
                import shutil
                shutil.copy2(saved_path, filepath)
                
                messagebox.showinfo("Data Exported", f"Analytics data exported to:\n{filepath}")
            
        except Exception as e:
            self.logger.error(f"Error exporting analytics data: {e}")
            messagebox.showerror("Error", f"Failed to export analytics data:\n{str(e)}")
    
    def _export_anonymized_report(self):
        """Export anonymized report."""
        try:
            if not self.performance_monitor.anonymized_export:
                messagebox.showwarning("Export Disabled", 
                                    "Anonymized export is not enabled. Enable it in settings first.")
                return
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"anonymized_report_{timestamp}.json"
            
            filepath = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                initialname=filename
            )
            
            if filepath:
                saved_path = self.performance_monitor.save_anonymized_report(
                    os.path.basename(filepath)
                )
                
                # Copy to user-selected location
                import shutil
                shutil.copy2(saved_path, filepath)
                
                messagebox.showinfo("Report Exported", f"Anonymized report exported to:\n{filepath}")
            
        except Exception as e:
            self.logger.error(f"Error exporting anonymized report: {e}")
            messagebox.showerror("Error", f"Failed to export anonymized report:\n{str(e)}")
    
    def _update_analytics_enabled(self):
        """Update analytics enabled setting."""
        self.performance_monitor.analytics_enabled = self.analytics_enabled_var.get()
        if self.config_manager:
            self.config_manager.set('analytics.enabled', self.analytics_enabled_var.get())
    
    def _update_performance_monitoring(self):
        """Update performance monitoring setting."""
        self.performance_monitor.performance_monitoring = self.performance_monitoring_var.get()
        if self.config_manager:
            self.config_manager.set('analytics.performance_monitoring', self.performance_monitoring_var.get())
    
    def _update_usage_statistics(self):
        """Update usage statistics setting."""
        self.performance_monitor.usage_statistics = self.usage_statistics_var.get()
        if self.config_manager:
            self.config_manager.set('analytics.usage_statistics', self.usage_statistics_var.get())
    
    def _update_error_tracking(self):
        """Update error tracking setting."""
        self.performance_monitor.error_tracking = self.error_tracking_var.get()
        if self.config_manager:
            self.config_manager.set('analytics.error_tracking', self.error_tracking_var.get())
    
    def _update_anonymized_export(self):
        """Update anonymized export setting."""
        self.performance_monitor.anonymized_export = self.anonymized_export_var.get()
        if self.config_manager:
            self.config_manager.set('analytics.anonymized_export', self.anonymized_export_var.get())
    
    def _update_privacy_mode(self):
        """Update privacy mode setting."""
        self.performance_monitor.privacy_mode = self.privacy_mode_var.get()
        if self.config_manager:
            self.config_manager.set('analytics.privacy_mode', self.privacy_mode_var.get())
    
    def _update_data_retention(self):
        """Update data retention setting."""
        try:
            retention_days = int(self.retention_var.get())
            if 1 <= retention_days <= 365:
                self.performance_monitor.data_retention_days = retention_days
                if self.config_manager:
                    self.config_manager.set('analytics.data_retention_days', retention_days)
                messagebox.showinfo("Updated", f"Data retention set to {retention_days} days")
            else:
                messagebox.showerror("Invalid Value", "Retention days must be between 1 and 365")
        except ValueError:
            messagebox.showerror("Invalid Value", "Please enter a valid number for retention days")
    
    def _save_settings(self):
        """Save all settings to configuration."""
        try:
            if self.config_manager:
                # Update all settings
                self._update_analytics_enabled()
                self._update_performance_monitoring()
                self._update_usage_statistics()
                self._update_error_tracking()
                self._update_anonymized_export()
                self._update_privacy_mode()
                self._update_data_retention()
                
                messagebox.showinfo("Settings Saved", "Analytics settings have been saved.")
            else:
                messagebox.showwarning("No Config Manager", 
                                    "Configuration manager not available. Settings will not be persisted.")
                
        except Exception as e:
            self.logger.error(f"Error saving settings: {e}")
            messagebox.showerror("Error", f"Failed to save settings:\n{str(e)}")
    
    def _on_closing(self):
        """Handle dashboard closing."""
        if self.refresh_timer:
            self.root.after_cancel(self.refresh_timer)
        
        self.root.withdraw()  # Hide instead of destroy
        self.root = None
        self.logger.info("Analytics dashboard closed")
    
    def close_dashboard(self):
        """Close the dashboard."""
        if self.root:
            self.root.destroy()
            self.root = None 
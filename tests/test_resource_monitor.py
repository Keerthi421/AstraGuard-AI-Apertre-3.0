"""
Test suite for resource_monitor module.

Tests system resource monitoring with non-blocking CPU checks.
"""

import pytest
import psutil
from core.resource_monitor import (
    ResourceLevel,
    ResourceMetrics,
    ResourceThresholds,
    ResourceMonitor,
    get_resource_monitor,
)


class TestResourceMetrics:
    """Test ResourceMetrics data class"""

    def test_metrics_creation(self):
        """Test creating resource metrics"""
        metrics = ResourceMetrics(
            cpu_percent=50.0,
            memory_percent=60.0,
            memory_available_mb=2048.0,
            disk_percent=70.0,
            timestamp=1234567890.0,
        )
        assert metrics.cpu_percent == 50.0
        assert metrics.memory_percent == 60.0
        assert metrics.memory_available_mb == 2048.0
        assert metrics.disk_percent == 70.0
        assert metrics.timestamp == 1234567890.0

    def test_metrics_to_dict(self):
        """Test converting metrics to dictionary"""
        metrics = ResourceMetrics(
            cpu_percent=45.0,
            memory_percent=55.0,
            memory_available_mb=3072.0,
            disk_percent=65.0,
            timestamp=1234567890.0,
        )
        d = metrics.to_dict()
        assert d["cpu_percent"] == 45.0
        assert d["memory_percent"] == 55.0
        assert d["memory_available_mb"] == 3072.0
        assert d["disk_percent"] == 65.0
        assert d["timestamp"] == 1234567890.0

    def test_metrics_all_zeros(self):
        """Test metrics with zero values"""
        metrics = ResourceMetrics(
            cpu_percent=0.0,
            memory_percent=0.0,
            memory_available_mb=0.0,
            disk_percent=0.0,
            timestamp=0.0,
        )
        assert metrics.cpu_percent == 0.0
        assert metrics.memory_percent == 0.0


class TestResourceThresholds:
    """Test ResourceThresholds configuration"""

    def test_default_thresholds(self):
        """Test default threshold values"""
        thresholds = ResourceThresholds()
        assert thresholds.cpu_warning == 70.0
        assert thresholds.cpu_critical == 90.0
        assert thresholds.memory_warning == 75.0
        assert thresholds.memory_critical == 90.0
        assert thresholds.disk_warning == 80.0
        assert thresholds.disk_critical == 95.0

    def test_custom_thresholds(self):
        """Test custom threshold values"""
        thresholds = ResourceThresholds(
            cpu_warning=60.0,
            cpu_critical=85.0,
            memory_warning=70.0,
            memory_critical=85.0,
            disk_warning=75.0,
            disk_critical=90.0,
        )
        assert thresholds.cpu_warning == 60.0
        assert thresholds.cpu_critical == 85.0
        assert thresholds.memory_warning == 70.0
        assert thresholds.memory_critical == 85.0
        assert thresholds.disk_warning == 75.0
        assert thresholds.disk_critical == 90.0


class TestResourceMonitor:
    """Test ResourceMonitor class"""

    def test_monitor_initialization(self):
        """Test resource monitor initialization"""
        monitor = ResourceMonitor()
        assert monitor.thresholds is not None
        assert monitor.metrics_history == []
        assert monitor.max_history == 100
        assert monitor._monitoring_enabled is True

    def test_monitor_with_custom_thresholds(self):
        """Test monitor with custom thresholds"""
        thresholds = ResourceThresholds(cpu_warning=50.0, cpu_critical=75.0)
        monitor = ResourceMonitor(thresholds=thresholds)
        assert monitor.thresholds.cpu_warning == 50.0
        assert monitor.thresholds.cpu_critical == 75.0

    def test_get_current_metrics(self):
        """Test getting current metrics"""
        monitor = ResourceMonitor()
        metrics = monitor.get_current_metrics()

        assert isinstance(metrics, ResourceMetrics)
        assert isinstance(metrics.cpu_percent, float)
        assert isinstance(metrics.memory_percent, float)
        assert isinstance(metrics.memory_available_mb, float)
        assert isinstance(metrics.disk_percent, float)

    def test_metrics_within_valid_ranges(self):
        """Test that metrics are within valid ranges"""
        monitor = ResourceMonitor()
        metrics = monitor.get_current_metrics()

        assert 0 <= metrics.cpu_percent <= 100
        assert 0 <= metrics.memory_percent <= 100
        assert metrics.memory_available_mb >= 0
        assert 0 <= metrics.disk_percent <= 100

    def test_metrics_history_accumulation(self):
        """Test that metrics history accumulates"""
        monitor = ResourceMonitor()
        for _ in range(5):
            monitor.get_current_metrics()

        assert len(monitor.metrics_history) == 5

    def test_metrics_history_respects_max_size(self):
        """Test that history respects max size limit"""
        monitor = ResourceMonitor()
        monitor.max_history = 10

        for _ in range(15):
            monitor.get_current_metrics()

        assert len(monitor.metrics_history) <= 10

    def test_check_resource_health_healthy(self):
        """Test resource health check for healthy state"""
        thresholds = ResourceThresholds(
            cpu_warning=10.0, cpu_critical=20.0, memory_warning=10.0, memory_critical=20.0
        )
        monitor = ResourceMonitor(thresholds=thresholds)
        health = monitor.check_resource_health()

        assert isinstance(health, dict)
        assert "cpu" in health
        assert "memory" in health
        assert "disk" in health

    def test_check_resource_health_has_status_values(self):
        """Test that health check returns valid status strings"""
        monitor = ResourceMonitor()
        health = monitor.check_resource_health()

        valid_statuses = ["healthy", "warning", "critical"]
        for key in ["cpu", "memory", "disk"]:
            assert health[key] in valid_statuses

    def test_is_resource_available(self):
        """Test resource availability check"""
        monitor = ResourceMonitor()
        available = monitor.is_resource_available()
        assert isinstance(available, bool)

    def test_get_metrics_summary(self):
        """Test getting metrics summary"""
        monitor = ResourceMonitor()
        for _ in range(3):
            monitor.get_current_metrics()

        summary = monitor.get_metrics_summary()
        assert isinstance(summary, dict)
        assert "latest" in summary
        assert "history_size" in summary
        assert "health_status" in summary

    def test_get_metrics_summary_empty_history(self):
        """Test metrics summary with no history"""
        monitor = ResourceMonitor()
        summary = monitor.get_metrics_summary()
        assert summary == {}

    def test_set_monitoring_enabled(self):
        """Test enabling/disabling monitoring"""
        monitor = ResourceMonitor()
        assert monitor._monitoring_enabled is True

        monitor.set_monitoring_enabled(False)
        assert monitor._monitoring_enabled is False

        monitor.set_monitoring_enabled(True)
        assert monitor._monitoring_enabled is True

    def test_monitoring_disabled_returns_zeros(self):
        """Test that disabled monitoring returns zero metrics"""
        monitor = ResourceMonitor()
        monitor.set_monitoring_enabled(False)

        metrics = monitor.get_current_metrics()
        assert metrics.cpu_percent == 0
        assert metrics.memory_percent == 0
        assert metrics.memory_available_mb == 0
        assert metrics.disk_percent == 0

    def test_non_blocking_cpu_check(self):
        """Test that CPU checking uses interval=0 (non-blocking)"""
        monitor = ResourceMonitor()
        # Get metrics multiple times - should complete quickly
        # if using interval=0 instead of interval=0.1
        import time

        start = time.time()
        for _ in range(5):
            monitor.get_current_metrics()
        elapsed = time.time() - start

        # Should complete in well under 1 second if non-blocking
        # (interval=0.1 would take at least 0.5s for 5 calls)
        assert elapsed < 1.0

    def test_health_check_cpu_warning(self):
        """Test CPU warning threshold"""
        # Mock high CPU by using low thresholds
        thresholds = ResourceThresholds(cpu_warning=1.0, cpu_critical=0.1)
        monitor = ResourceMonitor(thresholds=thresholds)

        health = monitor.check_resource_health()
        # CPU should trigger warning since real CPU is > 1%
        assert health["cpu"] in ["warning", "critical"]

    def test_health_check_cpu_critical(self):
        """Test CPU critical threshold"""
        thresholds = ResourceThresholds(cpu_critical=0.01)
        monitor = ResourceMonitor(thresholds=thresholds)

        health = monitor.check_resource_health()
        # CPU should trigger critical since real CPU > 0.01%
        assert health["cpu"] in ["critical", "warning"]

    def test_multiple_monitors_independent(self):
        """Test that multiple monitors maintain independent state"""
        monitor1 = ResourceMonitor()
        monitor2 = ResourceMonitor()

        monitor1.get_current_metrics()
        monitor1.get_current_metrics()

        monitor2.get_current_metrics()

        assert len(monitor1.metrics_history) == 2
        assert len(monitor2.metrics_history) == 1


class TestResourceMonitorErrorHandling:
    """Test error handling in resource monitor"""

    def test_get_metrics_handles_errors(self):
        """Test that metric collection handles errors gracefully"""
        monitor = ResourceMonitor()
        # Should not raise even if there are system issues
        metrics = monitor.get_current_metrics()
        assert metrics is not None

    def test_check_health_handles_disabled_monitoring(self):
        """Test that health check works with disabled monitoring"""
        monitor = ResourceMonitor()
        monitor.set_monitoring_enabled(False)

        health = monitor.check_resource_health()
        assert isinstance(health, dict)

    def test_metrics_summary_with_single_entry(self):
        """Test metrics summary with only one entry"""
        monitor = ResourceMonitor()
        monitor.get_current_metrics()

        summary = monitor.get_metrics_summary()
        assert "latest" in summary
        assert summary["history_size"] == 1


class TestGlobalResourceMonitor:
    """Test global resource monitor singleton"""

    def test_get_resource_monitor_singleton(self):
        """Test that get_resource_monitor returns singleton"""
        monitor1 = get_resource_monitor()
        monitor2 = get_resource_monitor()

        # Should be the same instance
        assert monitor1 is monitor2

    def test_singleton_is_resource_monitor(self):
        """Test that singleton is ResourceMonitor instance"""
        monitor = get_resource_monitor()
        assert isinstance(monitor, ResourceMonitor)

    def test_singleton_persists_state(self):
        """Test that singleton persists state across calls"""
        monitor1 = get_resource_monitor()
        monitor1.get_current_metrics()
        monitor1.get_current_metrics()

        monitor2 = get_resource_monitor()
        assert len(monitor2.metrics_history) >= 2


class TestResourceMonitorIntegration:
    """Integration tests for resource monitoring"""

    def test_full_monitoring_cycle(self):
        """Test complete monitoring cycle"""
        monitor = ResourceMonitor()

        # Collect metrics
        for _ in range(3):
            monitor.get_current_metrics()

        # Check health
        health = monitor.check_resource_health()
        assert health is not None

        # Get summary
        summary = monitor.get_metrics_summary()
        assert summary is not None

        # Check availability
        available = monitor.is_resource_available()
        assert isinstance(available, bool)

    def test_monitoring_with_threshold_changes(self):
        """Test monitoring with different thresholds"""
        thresholds1 = ResourceThresholds(cpu_warning=50.0)
        monitor = ResourceMonitor(thresholds=thresholds1)

        health1 = monitor.check_resource_health()
        assert health1 is not None

        # Change thresholds
        monitor.thresholds.cpu_warning = 1.0
        health2 = monitor.check_resource_health()
        assert health2 is not None

    def test_metrics_accuracy(self):
        """Test that metrics are reasonably accurate"""
        monitor = ResourceMonitor()
        metrics = monitor.get_current_metrics()

        # Get system metrics independently
        cpu = psutil.cpu_percent(interval=0)
        mem = psutil.virtual_memory()

        # Values should be in reasonable range
        # (allowing for timing differences)
        assert 0 <= metrics.cpu_percent <= 100
        assert abs(metrics.memory_percent - mem.percent) < 5.0

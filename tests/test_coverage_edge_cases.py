"""
Additional tests to achieve 100% coverage for timeout and resource monitoring modules.
"""

import pytest
import time
from unittest.mock import patch, Mock
from core.resource_monitor import ResourceMonitor, ResourceThresholds, ResourceMetrics
from core.timeout_handler import TimeoutContext, TimeoutError as CustomTimeoutError


class TestResourceMonitorEdgeCases:
    """Additional tests for resource monitor edge cases"""
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    def test_error_handling_in_metrics_collection(self, mock_disk, mock_memory, mock_cpu):
        """Test that metrics collection handles psutil errors gracefully"""
        # Make psutil raise an exception
        mock_cpu.side_effect = Exception("psutil error")
        
        monitor = ResourceMonitor()
        metrics = monitor.get_current_metrics()
        
        # Should return zero metrics on error
        assert metrics.cpu_percent == 0.0
        assert metrics.memory_percent == 0.0
        assert metrics.disk_usage_percent == 0.0
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    def test_cpu_critical_logging(self, mock_disk, mock_memory, mock_cpu):
        """Test CPU critical status triggers warning log"""
        # Set CPU to critical level
        mock_cpu.return_value = 95.0
        mock_memory.return_value = Mock(percent=50.0, available=2048*1024*1024)
        mock_disk.return_value = Mock(percent=50.0)
        
        monitor = ResourceMonitor()
        status = monitor.check_resource_health()
        
        assert status['cpu'] == 'critical'
        assert status['overall'] == 'critical'
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    def test_memory_warning_logging(self, mock_disk, mock_memory, mock_cpu):
        """Test memory warning status triggers info log"""
        # Set memory to warning level
        mock_cpu.return_value = 50.0
        mock_memory.return_value = Mock(percent=80.0, available=500*1024*1024)
        mock_disk.return_value = Mock(percent=50.0)
        
        monitor = ResourceMonitor()
        status = monitor.check_resource_health()
        
        assert status['memory'] == 'warning'
        assert status['overall'] == 'warning'
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    def test_disk_critical_logging(self, mock_disk, mock_memory, mock_cpu):
        """Test disk critical status triggers warning log"""
        # Set disk to critical level
        mock_cpu.return_value = 50.0
        mock_memory.return_value = Mock(percent=50.0, available=2048*1024*1024)
        mock_disk.return_value = Mock(percent=96.0)  # Above 95% critical threshold
        
        monitor = ResourceMonitor()
        status = monitor.check_resource_health()
        
        assert status['disk'] == 'critical'
        assert status['overall'] == 'critical'
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    def test_disk_warning_logging(self, mock_disk, mock_memory, mock_cpu):
        """Test disk warning status"""
        # Set disk to warning level
        mock_cpu.return_value = 50.0
        mock_memory.return_value = Mock(percent=50.0, available=2048*1024*1024)
        mock_disk.return_value = Mock(percent=85.0)  # Above 80% warning threshold
        
        monitor = ResourceMonitor()
        status = monitor.check_resource_health()
        
        assert status['disk'] == 'warning'
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    def test_insufficient_memory_warning(self, mock_disk, mock_memory, mock_cpu):
        """Test insufficient memory triggers warning log"""
        mock_cpu.return_value = 50.0
        mock_memory.return_value = Mock(percent=60.0, available=50*1024*1024)  # Only 50MB
        mock_disk.return_value = Mock(percent=50.0)
        
        monitor = ResourceMonitor()
        # Request 200MB but only 50MB available
        available = monitor.is_resource_available(min_cpu_free=10.0, min_memory_mb=200.0)
        
        assert available is False
    
    def test_metrics_summary_no_history(self):
        """Test metrics summary with no history returns error"""
        monitor = ResourceMonitor()
        # Don't collect any metrics
        
        summary = monitor.get_metrics_summary(duration_minutes=5)
        
        assert 'error' in summary
        assert summary['error'] == 'No metrics available'


class TestTimeoutContextEdgeCases:
    """Additional tests for timeout context edge cases"""
    
    def test_context_exits_cleanly_after_manual_check(self):
        """Test that context exits properly even after manual timeout check"""
        ctx = TimeoutContext(seconds=2.0, operation="test_op")
        ctx.__enter__()
        
        # Quick operation - should not timeout
        time.sleep(0.1)
        ctx.check_timeout()  # Should not raise
        
        # Exit normally
        result = ctx.__exit__(None, None, None)
        assert result is False  # Don't suppress exceptions
    
    def test_context_with_exception_during_block(self):
        """Test that context does not suppress other exceptions"""
        try:
            with TimeoutContext(seconds=2.0, operation="error_op"):
                raise ValueError("Test error")
        except ValueError as e:
            assert "Test error" in str(e)
        except CustomTimeoutError:
            pytest.fail("Should not raise TimeoutError, should preserve ValueError")

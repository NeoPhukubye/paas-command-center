"""Tests for DevOps operations - validates log querying and outage detection logic."""

import pytest
from datetime import datetime


SAMPLE_DEVOPS_LOGS = [
    {"timestamp": "2025-06-15T14:05:00", "endpoint": "/checkout", "status_code": 500, "response_time_ms": 8500, "error_message": "Internal Server Error: database connection timeout"},
    {"timestamp": "2025-06-15T14:10:00", "endpoint": "/checkout", "status_code": 503, "response_time_ms": 10000, "error_message": "Service Unavailable: circuit breaker open"},
    {"timestamp": "2025-06-15T14:15:00", "endpoint": "/checkout", "status_code": 500, "response_time_ms": 9200, "error_message": "Internal Server Error: payment gateway unreachable"},
    {"timestamp": "2025-06-15T10:00:00", "endpoint": "/login", "status_code": 200, "response_time_ms": 120, "error_message": None},
    {"timestamp": "2025-06-15T10:05:00", "endpoint": "/dashboard", "status_code": 200, "response_time_ms": 95, "error_message": None},
    {"timestamp": "2025-06-14T08:00:00", "endpoint": "/checkout", "status_code": 200, "response_time_ms": 250, "error_message": None},
]


class TestOutageDetection:
    """Tests for identifying outage windows from devops_logs data."""

    def test_identify_error_spike_endpoints(self):
        error_logs = [log for log in SAMPLE_DEVOPS_LOGS if log["status_code"] >= 500]
        affected_endpoints = set(log["endpoint"] for log in error_logs)
        assert "/checkout" in affected_endpoints

    def test_outage_window_boundary(self):
        outage_start = datetime(2025, 6, 15, 14, 0, 0)
        outage_end = datetime(2025, 6, 15, 16, 0, 0)

        outage_logs = [
            log for log in SAMPLE_DEVOPS_LOGS
            if log["status_code"] >= 500
            and outage_start <= datetime.fromisoformat(log["timestamp"]) <= outage_end
        ]
        assert len(outage_logs) == 3

    def test_error_rate_calculation(self):
        total = len(SAMPLE_DEVOPS_LOGS)
        errors = sum(1 for log in SAMPLE_DEVOPS_LOGS if log["status_code"] >= 500)
        error_rate = errors / total
        assert error_rate == pytest.approx(0.5, abs=0.01)

    def test_average_response_time_during_outage(self):
        outage_logs = [
            log for log in SAMPLE_DEVOPS_LOGS
            if log["status_code"] >= 500
        ]
        avg_response = sum(log["response_time_ms"] for log in outage_logs) / len(outage_logs)
        assert avg_response > 5000

    def test_normal_response_time(self):
        normal_logs = [
            log for log in SAMPLE_DEVOPS_LOGS
            if log["status_code"] < 400
        ]
        avg_response = sum(log["response_time_ms"] for log in normal_logs) / len(normal_logs)
        assert avg_response < 500


class TestLogFiltering:
    """Tests for filtering logs by various criteria."""

    def test_filter_by_endpoint(self):
        checkout_logs = [log for log in SAMPLE_DEVOPS_LOGS if log["endpoint"] == "/checkout"]
        assert len(checkout_logs) == 4

    def test_filter_by_status_code(self):
        success_logs = [log for log in SAMPLE_DEVOPS_LOGS if 200 <= log["status_code"] < 300]
        assert len(success_logs) == 3

    def test_filter_by_time_range(self):
        start = datetime(2025, 6, 15, 14, 0, 0)
        end = datetime(2025, 6, 15, 15, 0, 0)
        filtered = [
            log for log in SAMPLE_DEVOPS_LOGS
            if start <= datetime.fromisoformat(log["timestamp"]) <= end
        ]
        assert len(filtered) == 3

    def test_filter_errors_only(self):
        errors = [log for log in SAMPLE_DEVOPS_LOGS if log["error_message"] is not None]
        assert all(log["status_code"] >= 500 for log in errors)


class TestMetricsAggregation:
    """Tests for computing operational metrics from log data."""

    def test_p99_response_time(self):
        response_times = sorted(log["response_time_ms"] for log in SAMPLE_DEVOPS_LOGS)
        p99_index = int(len(response_times) * 0.99)
        p99 = response_times[min(p99_index, len(response_times) - 1)]
        assert p99 == 10000

    def test_uptime_percentage(self):
        total = len(SAMPLE_DEVOPS_LOGS)
        successful = sum(1 for log in SAMPLE_DEVOPS_LOGS if log["status_code"] < 500)
        uptime = successful / total * 100
        assert uptime == pytest.approx(50.0, abs=0.1)

    def test_error_breakdown_by_type(self):
        error_messages = [log["error_message"] for log in SAMPLE_DEVOPS_LOGS if log["error_message"]]
        assert any("database connection timeout" in msg for msg in error_messages)
        assert any("payment gateway unreachable" in msg for msg in error_messages)
        assert any("circuit breaker open" in msg for msg in error_messages)

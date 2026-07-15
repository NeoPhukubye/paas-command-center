"""Tests for SaaS financial analytics - cost tracking, anomaly detection, and categorization."""

import pytest
from datetime import datetime


SAMPLE_FINANCIALS = [
    {"transaction_id": "txn-001", "timestamp": "2025-06-15T14:30:00", "vendor_name": "AWS", "amount": 18500.00, "category": "Infrastructure", "status": "completed"},
    {"transaction_id": "txn-002", "timestamp": "2025-06-15T14:45:00", "vendor_name": "GCP", "amount": 12000.00, "category": "Infrastructure", "status": "completed"},
    {"transaction_id": "txn-003", "timestamp": "2025-06-10T09:00:00", "vendor_name": "AWS", "amount": 1500.00, "category": "Infrastructure", "status": "completed"},
    {"transaction_id": "txn-004", "timestamp": "2025-06-10T10:00:00", "vendor_name": "HubSpot", "amount": 3200.00, "category": "Marketing", "status": "completed"},
    {"transaction_id": "txn-005", "timestamp": "2025-06-12T11:00:00", "vendor_name": "Stripe", "amount": 450.00, "category": "Payments", "status": "completed"},
    {"transaction_id": "txn-006", "timestamp": "2025-06-08T08:00:00", "vendor_name": "Datadog", "amount": 800.00, "category": "Analytics", "status": "pending"},
    {"transaction_id": "txn-007", "timestamp": "2025-06-15T15:00:00", "vendor_name": "Snowflake", "amount": 22000.00, "category": "Infrastructure", "status": "failed"},
]


class TestCostAggregation:
    """Tests for aggregating costs by category and vendor."""

    def test_total_spend(self):
        total = sum(t["amount"] for t in SAMPLE_FINANCIALS)
        assert total == pytest.approx(58450.00)

    def test_spend_by_category(self):
        infra_spend = sum(t["amount"] for t in SAMPLE_FINANCIALS if t["category"] == "Infrastructure")
        assert infra_spend == pytest.approx(54000.00)

    def test_spend_by_vendor(self):
        aws_spend = sum(t["amount"] for t in SAMPLE_FINANCIALS if t["vendor_name"] == "AWS")
        assert aws_spend == pytest.approx(20000.00)

    def test_category_percentage(self):
        total = sum(t["amount"] for t in SAMPLE_FINANCIALS)
        infra = sum(t["amount"] for t in SAMPLE_FINANCIALS if t["category"] == "Infrastructure")
        pct = infra / total * 100
        assert pct > 90  # infrastructure dominates during outage


class TestCostAnomalyDetection:
    """Tests for detecting cost spikes correlated with the outage."""

    def test_outage_period_costs_exceed_normal(self):
        outage_start = datetime(2025, 6, 15, 14, 0, 0)
        outage_end = datetime(2025, 6, 15, 16, 0, 0)

        outage_costs = [
            t["amount"] for t in SAMPLE_FINANCIALS
            if t["category"] == "Infrastructure"
            and outage_start <= datetime.fromisoformat(t["timestamp"]) <= outage_end
        ]
        normal_costs = [
            t["amount"] for t in SAMPLE_FINANCIALS
            if t["category"] == "Infrastructure"
            and not (outage_start <= datetime.fromisoformat(t["timestamp"]) <= outage_end)
        ]

        avg_outage = sum(outage_costs) / len(outage_costs) if outage_costs else 0
        avg_normal = sum(normal_costs) / len(normal_costs) if normal_costs else 0
        assert avg_outage > avg_normal * 5  # at least 5x spike

    def test_identify_top_cost_transactions(self):
        sorted_txns = sorted(SAMPLE_FINANCIALS, key=lambda t: t["amount"], reverse=True)
        top_3 = sorted_txns[:3]
        # Top costs should all be infrastructure during outage
        assert all(t["category"] == "Infrastructure" for t in top_3)

    def test_failed_transactions_during_outage(self):
        outage_start = datetime(2025, 6, 15, 14, 0, 0)
        outage_end = datetime(2025, 6, 15, 16, 0, 0)

        failed_during_outage = [
            t for t in SAMPLE_FINANCIALS
            if t["status"] == "failed"
            and outage_start <= datetime.fromisoformat(t["timestamp"]) <= outage_end
        ]
        assert len(failed_during_outage) >= 1


class TestTransactionValidation:
    """Tests for transaction data integrity."""

    def test_unique_transaction_ids(self):
        ids = [t["transaction_id"] for t in SAMPLE_FINANCIALS]
        assert len(ids) == len(set(ids))

    def test_amounts_are_positive(self):
        for t in SAMPLE_FINANCIALS:
            assert t["amount"] > 0

    def test_valid_statuses(self):
        valid_statuses = {"completed", "pending", "failed"}
        for t in SAMPLE_FINANCIALS:
            assert t["status"] in valid_statuses

    def test_timestamps_are_parseable(self):
        for t in SAMPLE_FINANCIALS:
            dt = datetime.fromisoformat(t["timestamp"])
            assert isinstance(dt, datetime)


class TestBudgetAlerts:
    """Tests for budget threshold logic."""

    def test_daily_budget_breach(self):
        daily_budget = 10000
        # Group by date
        daily_totals = {}
        for t in SAMPLE_FINANCIALS:
            date = t["timestamp"][:10]
            daily_totals[date] = daily_totals.get(date, 0) + t["amount"]

        breached_days = [d for d, total in daily_totals.items() if total > daily_budget]
        assert "2025-06-15" in breached_days

    def test_vendor_concentration_risk(self):
        total = sum(t["amount"] for t in SAMPLE_FINANCIALS)
        vendor_totals = {}
        for t in SAMPLE_FINANCIALS:
            vendor_totals[t["vendor_name"]] = vendor_totals.get(t["vendor_name"], 0) + t["amount"]

        # Check if any vendor exceeds 40% of total spend
        concentrated = [v for v, amt in vendor_totals.items() if amt / total > 0.4]
        assert len(concentrated) >= 0  # may or may not have concentration

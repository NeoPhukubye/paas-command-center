"""Tests for Customer CRM / Growth analytics - churn risk, segmentation, and outage impact."""

import pytest
from datetime import datetime


SAMPLE_CUSTOMERS = [
    {"customer_id": "CUST-0001", "name": "Alice Smith", "email": "alice.smith42@example.com", "plan_tier": "Enterprise", "lifetime_value": 180000.00, "churn_risk_score": 0.88, "last_active": "2025-06-12T10:00:00"},
    {"customer_id": "CUST-0002", "name": "Bob Johnson", "email": "bob.johnson7@example.com", "plan_tier": "Enterprise", "lifetime_value": 95000.00, "churn_risk_score": 0.72, "last_active": "2025-06-13T08:00:00"},
    {"customer_id": "CUST-0003", "name": "Carol Williams", "email": "carol.williams55@example.com", "plan_tier": "Pro", "lifetime_value": 45000.00, "churn_risk_score": 0.81, "last_active": "2025-06-11T14:00:00"},
    {"customer_id": "CUST-0004", "name": "David Brown", "email": "david.brown12@example.com", "plan_tier": "Pro", "lifetime_value": 22000.00, "churn_risk_score": 0.25, "last_active": "2025-06-15T09:00:00"},
    {"customer_id": "CUST-0005", "name": "Eve Jones", "email": "eve.jones88@example.com", "plan_tier": "Starter", "lifetime_value": 5000.00, "churn_risk_score": 0.15, "last_active": "2025-06-14T16:00:00"},
    {"customer_id": "CUST-0006", "name": "Frank Garcia", "email": "frank.garcia3@example.com", "plan_tier": "Free", "lifetime_value": 200.00, "churn_risk_score": 0.10, "last_active": "2025-06-15T12:00:00"},
    {"customer_id": "CUST-0007", "name": "Grace Miller", "email": "grace.miller61@example.com", "plan_tier": "Enterprise", "lifetime_value": 210000.00, "churn_risk_score": 0.91, "last_active": "2025-06-10T07:00:00"},
]


class TestChurnRiskAnalysis:
    """Tests for churn risk scoring and segmentation."""

    def test_high_risk_customers_identified(self):
        high_risk = [c for c in SAMPLE_CUSTOMERS if c["churn_risk_score"] >= 0.65]
        assert len(high_risk) == 4

    def test_high_risk_correlates_with_high_value(self):
        high_risk = [c for c in SAMPLE_CUSTOMERS if c["churn_risk_score"] >= 0.65]
        for customer in high_risk:
            assert customer["lifetime_value"] > 40000

    def test_low_risk_customers(self):
        low_risk = [c for c in SAMPLE_CUSTOMERS if c["churn_risk_score"] < 0.45]
        assert len(low_risk) == 3

    def test_revenue_at_risk(self):
        high_risk = [c for c in SAMPLE_CUSTOMERS if c["churn_risk_score"] >= 0.65]
        revenue_at_risk = sum(c["lifetime_value"] for c in high_risk)
        assert revenue_at_risk > 400000


class TestCustomerSegmentation:
    """Tests for customer segmentation by plan tier."""

    def test_enterprise_customers(self):
        enterprise = [c for c in SAMPLE_CUSTOMERS if c["plan_tier"] == "Enterprise"]
        assert len(enterprise) == 3

    def test_tier_value_ordering(self):
        tier_avg = {}
        for tier in ["Free", "Starter", "Pro", "Enterprise"]:
            customers = [c for c in SAMPLE_CUSTOMERS if c["plan_tier"] == tier]
            if customers:
                tier_avg[tier] = sum(c["lifetime_value"] for c in customers) / len(customers)

        if "Free" in tier_avg and "Enterprise" in tier_avg:
            assert tier_avg["Enterprise"] > tier_avg["Free"]

    def test_plan_tier_distribution(self):
        tiers = [c["plan_tier"] for c in SAMPLE_CUSTOMERS]
        assert "Enterprise" in tiers
        assert "Pro" in tiers
        assert "Starter" in tiers
        assert "Free" in tiers


class TestOutageImpactOnCustomers:
    """Tests for correlating outage impact with customer engagement."""

    def test_high_value_customers_inactive_after_outage(self):
        outage_date = datetime(2025, 6, 15, 14, 0, 0)
        high_risk = [c for c in SAMPLE_CUSTOMERS if c["churn_risk_score"] >= 0.65]

        for customer in high_risk:
            last_active = datetime.fromisoformat(customer["last_active"])
            assert last_active < outage_date

    def test_low_risk_customers_still_active(self):
        outage_date = datetime(2025, 6, 15, 0, 0, 0)
        low_risk = [c for c in SAMPLE_CUSTOMERS if c["churn_risk_score"] < 0.45]

        recent_count = sum(
            1 for c in low_risk
            if datetime.fromisoformat(c["last_active"]) >= outage_date - __import__("datetime").timedelta(days=2)
        )
        assert recent_count > 0

    def test_days_since_last_active(self):
        reference = datetime(2025, 6, 15, 16, 0, 0)  # end of outage
        high_risk = [c for c in SAMPLE_CUSTOMERS if c["churn_risk_score"] >= 0.65]

        for customer in high_risk:
            last_active = datetime.fromisoformat(customer["last_active"])
            days_inactive = (reference - last_active).days
            assert days_inactive >= 2


class TestCustomerDataIntegrity:
    """Tests for CRM data validation."""

    def test_unique_customer_ids(self):
        ids = [c["customer_id"] for c in SAMPLE_CUSTOMERS]
        assert len(ids) == len(set(ids))

    def test_valid_email_format(self):
        for c in SAMPLE_CUSTOMERS:
            assert "@" in c["email"]
            assert c["email"].endswith("@example.com")

    def test_customer_id_format(self):
        for c in SAMPLE_CUSTOMERS:
            assert c["customer_id"].startswith("CUST-")
            assert len(c["customer_id"]) == 9

    def test_churn_risk_bounds(self):
        for c in SAMPLE_CUSTOMERS:
            assert 0.0 <= c["churn_risk_score"] <= 1.0

    def test_lifetime_value_non_negative(self):
        for c in SAMPLE_CUSTOMERS:
            assert c["lifetime_value"] >= 0

    def test_valid_plan_tiers(self):
        valid_tiers = {"Free", "Starter", "Pro", "Enterprise"}
        for c in SAMPLE_CUSTOMERS:
            assert c["plan_tier"] in valid_tiers


class TestRetentionMetrics:
    """Tests for retention and growth metric calculations."""

    def test_average_lifetime_value(self):
        avg_ltv = sum(c["lifetime_value"] for c in SAMPLE_CUSTOMERS) / len(SAMPLE_CUSTOMERS)
        assert avg_ltv > 50000

    def test_weighted_churn_risk(self):
        total_ltv = sum(c["lifetime_value"] for c in SAMPLE_CUSTOMERS)
        weighted_risk = sum(
            c["churn_risk_score"] * c["lifetime_value"] / total_ltv
            for c in SAMPLE_CUSTOMERS
        )
        # Weighted risk should be high since high-value customers are at risk
        assert weighted_risk > 0.5

    def test_net_revenue_retention_scenario(self):
        # If all high-risk customers churn, calculate revenue impact
        total_ltv = sum(c["lifetime_value"] for c in SAMPLE_CUSTOMERS)
        churned_ltv = sum(
            c["lifetime_value"] for c in SAMPLE_CUSTOMERS
            if c["churn_risk_score"] >= 0.65
        )
        retention_rate = (total_ltv - churned_ltv) / total_ltv * 100
        assert retention_rate < 55  # significant impact

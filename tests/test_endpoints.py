"""Tests for FastAPI endpoints using TestClient with mocked Snowflake queries."""

from unittest.mock import patch
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# --- Dashboard & Health ---

class TestDashboard:
    def test_dashboard_returns_html(self):
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "PaaS Command Center" in response.text

    def test_dashboard_contains_all_sections(self):
        response = client.get("/")
        assert "DevOps Monitoring" in response.text
        assert "SaaS Financials" in response.text
        assert "Customer Growth" in response.text

    def test_dashboard_contains_endpoint_links(self):
        response = client.get("/")
        assert "/ops/logs" in response.text
        assert "/finance/transactions" in response.text
        assert "/growth/customers" in response.text

    def test_health_check(self):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "paas-command-center"


# --- Ops Endpoints ---

MOCK_LOGS = [
    {"log_id": 1, "timestamp": "2025-06-15T14:05:00", "endpoint": "/checkout", "status_code": 500, "response_time_ms": 8500, "error_message": "Internal Server Error: database connection timeout"},
    {"log_id": 2, "timestamp": "2025-06-15T10:00:00", "endpoint": "/login", "status_code": 200, "response_time_ms": 120, "error_message": None},
]

MOCK_OUTAGE_SUMMARY = [
    {"endpoint": "/checkout", "total_requests": 150, "error_count": 120, "error_rate_pct": 80.0, "avg_response_ms": 9500},
    {"endpoint": "/login", "total_requests": 80, "error_count": 25, "error_rate_pct": 31.25, "avg_response_ms": 4200},
]

MOCK_HEALTH_METRICS = [
    {"hour": "2025-06-15T14:00:00", "requests": 300, "errors": 180, "avg_response_ms": 7800, "p_max_response_ms": 15000},
    {"hour": "2025-06-15T15:00:00", "requests": 280, "errors": 150, "avg_response_ms": 6200, "p_max_response_ms": 12000},
]


class TestOpsEndpoints:
    @patch("app.routers.ops.query", return_value=MOCK_LOGS)
    def test_get_logs_default(self, mock_query):
        response = client.get("/ops/logs")
        assert response.status_code == 200
        assert len(response.json()) == 2
        mock_query.assert_called_once()

    @patch("app.routers.ops.query", return_value=[MOCK_LOGS[0]])
    def test_get_logs_filter_by_endpoint(self, mock_query):
        response = client.get("/ops/logs?endpoint=/checkout")
        assert response.status_code == 200
        call_args = mock_query.call_args
        assert "/checkout" in call_args[0][1]

    @patch("app.routers.ops.query", return_value=[MOCK_LOGS[0]])
    def test_get_logs_filter_by_status_code(self, mock_query):
        response = client.get("/ops/logs?status_code=500")
        assert response.status_code == 200

    @patch("app.routers.ops.query", return_value=[MOCK_LOGS[0]])
    def test_get_errors(self, mock_query):
        response = client.get("/ops/errors")
        assert response.status_code == 200
        assert response.json()[0]["status_code"] == 500

    @patch("app.routers.ops.query", return_value=[MOCK_LOGS[0]])
    def test_get_errors_custom_limit(self, mock_query):
        response = client.get("/ops/errors?limit=10")
        assert response.status_code == 200
        call_args = mock_query.call_args
        assert 10 in call_args[0][1]

    @patch("app.routers.ops.query", return_value=MOCK_OUTAGE_SUMMARY)
    def test_outage_summary(self, mock_query):
        response = client.get("/ops/outage-summary")
        assert response.status_code == 200
        data = response.json()
        assert data[0]["endpoint"] == "/checkout"
        assert data[0]["error_rate_pct"] == 80.0

    @patch("app.routers.ops.query", return_value=MOCK_HEALTH_METRICS)
    def test_health_metrics(self, mock_query):
        response = client.get("/ops/health-metrics")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["errors"] == 180


# --- Finance Endpoints ---

MOCK_TRANSACTIONS = [
    {"transaction_id": "txn-001", "timestamp": "2025-06-15T14:30:00", "vendor_name": "AWS", "amount": 18500.00, "category": "Infrastructure", "status": "completed"},
    {"transaction_id": "txn-002", "timestamp": "2025-06-10T09:00:00", "vendor_name": "HubSpot", "amount": 3200.00, "category": "Marketing", "status": "completed"},
]

MOCK_SPEND_BY_CATEGORY = [
    {"category": "Infrastructure", "transaction_count": 120, "total_spend": 450000.00, "avg_amount": 3750.00},
    {"category": "Marketing", "transaction_count": 80, "total_spend": 180000.00, "avg_amount": 2250.00},
]

MOCK_COST_SPIKE = [
    {"hour": "2025-06-15T14:00:00", "category": "Infrastructure", "total_cost": 85000.00, "txn_count": 12},
    {"hour": "2025-06-15T15:00:00", "category": "Infrastructure", "total_cost": 62000.00, "txn_count": 8},
]

MOCK_VENDOR_BREAKDOWN = [
    {"vendor_name": "AWS", "transactions": 50, "total_spend": 220000.00, "avg_spend": 4400.00},
    {"vendor_name": "GCP", "transactions": 30, "total_spend": 95000.00, "avg_spend": 3166.67},
]


class TestFinanceEndpoints:
    @patch("app.routers.finance.query", return_value=MOCK_TRANSACTIONS)
    def test_get_transactions_default(self, mock_query):
        response = client.get("/finance/transactions")
        assert response.status_code == 200
        assert len(response.json()) == 2

    @patch("app.routers.finance.query", return_value=[MOCK_TRANSACTIONS[0]])
    def test_get_transactions_filter_category(self, mock_query):
        response = client.get("/finance/transactions?category=Infrastructure")
        assert response.status_code == 200
        call_args = mock_query.call_args
        assert "Infrastructure" in call_args[0][1]

    @patch("app.routers.finance.query", return_value=[MOCK_TRANSACTIONS[0]])
    def test_get_transactions_filter_status(self, mock_query):
        response = client.get("/finance/transactions?status=completed")
        assert response.status_code == 200

    @patch("app.routers.finance.query", return_value=MOCK_SPEND_BY_CATEGORY)
    def test_spend_by_category(self, mock_query):
        response = client.get("/finance/spend-by-category")
        assert response.status_code == 200
        data = response.json()
        assert data[0]["category"] == "Infrastructure"
        assert data[0]["total_spend"] > data[1]["total_spend"]

    @patch("app.routers.finance.query", return_value=MOCK_COST_SPIKE)
    def test_cost_spike(self, mock_query):
        response = client.get("/finance/cost-spike")
        assert response.status_code == 200
        data = response.json()
        assert data[0]["total_cost"] > 50000

    @patch("app.routers.finance.query", return_value=MOCK_VENDOR_BREAKDOWN)
    def test_vendor_breakdown(self, mock_query):
        response = client.get("/finance/vendor-breakdown")
        assert response.status_code == 200
        data = response.json()
        assert data[0]["vendor_name"] == "AWS"


# --- Growth Endpoints ---

MOCK_CUSTOMERS = [
    {"customer_id": "CUST-0001", "name": "Alice Smith", "email": "alice.smith42@example.com", "plan_tier": "Enterprise", "lifetime_value": 180000.00, "churn_risk_score": 0.88, "last_active": "2025-06-12T10:00:00"},
    {"customer_id": "CUST-0004", "name": "David Brown", "email": "david.brown12@example.com", "plan_tier": "Pro", "lifetime_value": 22000.00, "churn_risk_score": 0.25, "last_active": "2025-06-15T09:00:00"},
]

MOCK_CHURN_RISK = [
    {"customer_id": "CUST-0001", "name": "Alice Smith", "email": "alice.smith42@example.com", "plan_tier": "Enterprise", "lifetime_value": 180000.00, "churn_risk_score": 0.88, "last_active": "2025-06-12T10:00:00"},
]

MOCK_REVENUE_AT_RISK = [
    {"plan_tier": "Enterprise", "at_risk_customers": 15, "revenue_at_risk": 2800000.00, "avg_churn_risk": 0.82},
    {"plan_tier": "Pro", "at_risk_customers": 8, "revenue_at_risk": 420000.00, "avg_churn_risk": 0.71},
]

MOCK_SEGMENTATION = [
    {"plan_tier": "Enterprise", "customer_count": 25, "avg_ltv": 150000.00, "avg_churn_risk": 0.78, "total_ltv": 3750000.00},
    {"plan_tier": "Pro", "customer_count": 35, "avg_ltv": 35000.00, "avg_churn_risk": 0.45, "total_ltv": 1225000.00},
]


class TestGrowthEndpoints:
    @patch("app.routers.growth.query", return_value=MOCK_CUSTOMERS)
    def test_get_customers_default(self, mock_query):
        response = client.get("/growth/customers")
        assert response.status_code == 200
        assert len(response.json()) == 2

    @patch("app.routers.growth.query", return_value=[MOCK_CUSTOMERS[0]])
    def test_get_customers_filter_tier(self, mock_query):
        response = client.get("/growth/customers?plan_tier=Enterprise")
        assert response.status_code == 200
        call_args = mock_query.call_args
        assert "Enterprise" in call_args[0][1]

    @patch("app.routers.growth.query", return_value=MOCK_CHURN_RISK)
    def test_churn_risk_default_threshold(self, mock_query):
        response = client.get("/growth/churn-risk")
        assert response.status_code == 200
        data = response.json()
        assert all(c["churn_risk_score"] >= 0.65 for c in data)

    @patch("app.routers.growth.query", return_value=MOCK_CHURN_RISK)
    def test_churn_risk_custom_threshold(self, mock_query):
        response = client.get("/growth/churn-risk?threshold=0.8")
        assert response.status_code == 200
        call_args = mock_query.call_args
        assert 0.8 in call_args[0][1]

    @patch("app.routers.growth.query", return_value=MOCK_REVENUE_AT_RISK)
    def test_revenue_at_risk(self, mock_query):
        response = client.get("/growth/revenue-at-risk")
        assert response.status_code == 200
        data = response.json()
        assert data[0]["plan_tier"] == "Enterprise"
        assert data[0]["revenue_at_risk"] > 1000000

    @patch("app.routers.growth.query", return_value=MOCK_SEGMENTATION)
    def test_segmentation(self, mock_query):
        response = client.get("/growth/segmentation")
        assert response.status_code == 200
        data = response.json()
        assert data[0]["total_ltv"] > data[1]["total_ltv"]


# --- Error Handling ---

class TestErrorHandling:
    @patch("app.routers.ops.query", side_effect=Exception("Connection failed"))
    def test_ops_endpoint_raises_on_db_error(self, mock_query):
        import pytest
        with pytest.raises(Exception, match="Connection failed"):
            client.get("/ops/logs")

    @patch("app.routers.finance.query", side_effect=Exception("Connection failed"))
    def test_finance_endpoint_raises_on_db_error(self, mock_query):
        import pytest
        with pytest.raises(Exception, match="Connection failed"):
            client.get("/finance/transactions")

    @patch("app.routers.growth.query", side_effect=Exception("Connection failed"))
    def test_growth_endpoint_raises_on_db_error(self, mock_query):
        import pytest
        with pytest.raises(Exception, match="Connection failed"):
            client.get("/growth/customers")

    def test_nonexistent_endpoint_returns_404(self):
        response = client.get("/nonexistent")
        assert response.status_code == 404


# --- OpenAPI / Docs ---

class TestAPIDocs:
    def test_openapi_schema_available(self):
        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert schema["info"]["title"] == "PaaS Command Center"

    def test_docs_page_available(self):
        response = client.get("/docs")
        assert response.status_code == 200

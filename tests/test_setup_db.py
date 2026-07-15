"""Tests for the database setup script's data generation logic."""

import sys
import os
import random
from datetime import datetime
from unittest.mock import MagicMock, patch, mock_open

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import setup_db


class TestConstants:
    def test_outage_window_is_two_hours(self):
        delta = setup_db.OUTAGE_END - setup_db.OUTAGE_START
        assert delta.total_seconds() == 7200

    def test_endpoints_contains_checkout(self):
        assert "/checkout" in setup_db.ENDPOINTS

    def test_categories_contains_infrastructure(self):
        assert "Infrastructure" in setup_db.CATEGORIES

    def test_plan_tiers_are_ordered(self):
        assert setup_db.PLAN_TIERS == ["Free", "Starter", "Pro", "Enterprise"]


class TestCreateTables:
    def test_executes_sql_statements(self, tmp_path):
        sql_content = "CREATE TABLE foo (id INT);\nCREATE TABLE bar (id INT);"
        sql_file = tmp_path / "setup_db.sql"
        sql_file.write_text(sql_content)

        mock_cur = MagicMock()
        with patch("setup_db.os.path.dirname", return_value=str(tmp_path)):
            setup_db.create_tables(mock_cur)

        assert mock_cur.execute.call_count == 2

    def test_skips_empty_statements(self, tmp_path):
        sql_content = "CREATE TABLE foo (id INT);  ;  ;"
        sql_file = tmp_path / "setup_db.sql"
        sql_file.write_text(sql_content)

        mock_cur = MagicMock()
        with patch("setup_db.os.path.dirname", return_value=str(tmp_path)):
            setup_db.create_tables(mock_cur)

        assert mock_cur.execute.call_count == 1


class TestGenerateDevopsLogs:
    def test_generates_correct_number_of_rows(self):
        mock_cur = MagicMock()
        setup_db.generate_devops_logs(mock_cur, num_records=100)
        rows = mock_cur.executemany.call_args[0][1]
        assert len(rows) == 100

    def test_row_structure(self):
        mock_cur = MagicMock()
        setup_db.generate_devops_logs(mock_cur, num_records=10)
        rows = mock_cur.executemany.call_args[0][1]
        for row in rows:
            assert len(row) == 5  # timestamp, endpoint, status_code, response_time_ms, error_message

    def test_endpoints_are_valid(self):
        mock_cur = MagicMock()
        setup_db.generate_devops_logs(mock_cur, num_records=50)
        rows = mock_cur.executemany.call_args[0][1]
        for row in rows:
            assert row[1] in setup_db.ENDPOINTS

    def test_status_codes_are_integers(self):
        mock_cur = MagicMock()
        setup_db.generate_devops_logs(mock_cur, num_records=50)
        rows = mock_cur.executemany.call_args[0][1]
        for row in rows:
            assert isinstance(row[2], int)

    def test_error_message_present_for_500(self):
        mock_cur = MagicMock()
        setup_db.generate_devops_logs(mock_cur, num_records=500)
        rows = mock_cur.executemany.call_args[0][1]
        for row in rows:
            if row[2] == 500:
                assert row[4] is not None
                assert "Internal Server Error" in row[4]

    def test_error_message_present_for_503(self):
        mock_cur = MagicMock()
        setup_db.generate_devops_logs(mock_cur, num_records=500)
        rows = mock_cur.executemany.call_args[0][1]
        for row in rows:
            if row[2] == 503:
                assert row[4] == "Service Unavailable: circuit breaker open"

    def test_error_message_none_for_success(self):
        mock_cur = MagicMock()
        setup_db.generate_devops_logs(mock_cur, num_records=500)
        rows = mock_cur.executemany.call_args[0][1]
        for row in rows:
            if row[2] in (200, 201, 301):
                assert row[4] is None

    def test_outage_window_has_high_response_times(self):
        random.seed(42)
        mock_cur = MagicMock()
        setup_db.generate_devops_logs(mock_cur, num_records=5000)
        rows = mock_cur.executemany.call_args[0][1]

        outage_checkout_rows = [
            row for row in rows
            if row[1] == "/checkout"
            and setup_db.OUTAGE_START <= datetime.fromisoformat(row[0]) <= setup_db.OUTAGE_END
        ]

        if outage_checkout_rows:
            avg_response = sum(r[3] for r in outage_checkout_rows) / len(outage_checkout_rows)
            assert avg_response > 1500  # outage rows should average well above normal

    def test_outage_window_has_elevated_error_rates(self):
        random.seed(42)
        mock_cur = MagicMock()
        setup_db.generate_devops_logs(mock_cur, num_records=5000)
        rows = mock_cur.executemany.call_args[0][1]

        outage_checkout_rows = [
            row for row in rows
            if row[1] == "/checkout"
            and setup_db.OUTAGE_START <= datetime.fromisoformat(row[0]) <= setup_db.OUTAGE_END
        ]

        if outage_checkout_rows:
            error_count = sum(1 for r in outage_checkout_rows if r[2] >= 500)
            error_rate = error_count / len(outage_checkout_rows)
            assert error_rate > 0.5  # majority should be errors during outage


class TestGenerateSaasFinancials:
    def test_generates_correct_number_of_rows(self):
        mock_cur = MagicMock()
        setup_db.generate_saas_financials(mock_cur, num_records=100)
        rows = mock_cur.executemany.call_args[0][1]
        assert len(rows) == 100

    def test_row_structure(self):
        mock_cur = MagicMock()
        setup_db.generate_saas_financials(mock_cur, num_records=10)
        rows = mock_cur.executemany.call_args[0][1]
        for row in rows:
            assert len(row) == 6  # transaction_id, timestamp, vendor, amount, category, status

    def test_transaction_ids_are_unique(self):
        mock_cur = MagicMock()
        setup_db.generate_saas_financials(mock_cur, num_records=200)
        rows = mock_cur.executemany.call_args[0][1]
        ids = [row[0] for row in rows]
        assert len(ids) == len(set(ids))

    def test_vendors_are_valid(self):
        mock_cur = MagicMock()
        setup_db.generate_saas_financials(mock_cur, num_records=50)
        rows = mock_cur.executemany.call_args[0][1]
        for row in rows:
            assert row[2] in setup_db.VENDORS

    def test_categories_are_valid(self):
        mock_cur = MagicMock()
        setup_db.generate_saas_financials(mock_cur, num_records=50)
        rows = mock_cur.executemany.call_args[0][1]
        for row in rows:
            assert row[4] in setup_db.CATEGORIES

    def test_status_values_are_valid(self):
        mock_cur = MagicMock()
        setup_db.generate_saas_financials(mock_cur, num_records=50)
        rows = mock_cur.executemany.call_args[0][1]
        for row in rows:
            assert row[5] in ("completed", "pending", "failed")

    def test_amounts_are_positive(self):
        mock_cur = MagicMock()
        setup_db.generate_saas_financials(mock_cur, num_records=100)
        rows = mock_cur.executemany.call_args[0][1]
        for row in rows:
            assert row[3] > 0


class TestGenerateCustomerCrm:
    def test_generates_correct_number_of_rows(self):
        mock_cur = MagicMock()
        setup_db.generate_customer_crm(mock_cur, num_records=50)
        rows = mock_cur.executemany.call_args[0][1]
        assert len(rows) == 50

    def test_row_structure(self):
        mock_cur = MagicMock()
        setup_db.generate_customer_crm(mock_cur, num_records=10)
        rows = mock_cur.executemany.call_args[0][1]
        for row in rows:
            assert len(row) == 7  # customer_id, name, email, plan_tier, ltv, churn, last_active

    def test_customer_ids_are_sequential(self):
        mock_cur = MagicMock()
        setup_db.generate_customer_crm(mock_cur, num_records=5)
        rows = mock_cur.executemany.call_args[0][1]
        assert rows[0][0] == "CUST-0001"
        assert rows[4][0] == "CUST-0005"

    def test_emails_contain_at_sign(self):
        mock_cur = MagicMock()
        setup_db.generate_customer_crm(mock_cur, num_records=20)
        rows = mock_cur.executemany.call_args[0][1]
        for row in rows:
            assert "@example.com" in row[2]

    def test_plan_tiers_are_valid(self):
        mock_cur = MagicMock()
        setup_db.generate_customer_crm(mock_cur, num_records=50)
        rows = mock_cur.executemany.call_args[0][1]
        for row in rows:
            assert row[3] in setup_db.PLAN_TIERS

    def test_churn_risk_in_valid_range(self):
        mock_cur = MagicMock()
        setup_db.generate_customer_crm(mock_cur, num_records=100)
        rows = mock_cur.executemany.call_args[0][1]
        for row in rows:
            assert 0.0 <= row[5] <= 1.0

    def test_high_value_customers_have_elevated_churn(self):
        random.seed(42)
        mock_cur = MagicMock()
        setup_db.generate_customer_crm(mock_cur, num_records=200)
        rows = mock_cur.executemany.call_args[0][1]

        high_value = [row for row in rows if row[4] > 40000]
        if high_value:
            for row in high_value:
                assert row[5] >= 0.65

    def test_low_value_customers_have_bounded_churn(self):
        random.seed(42)
        mock_cur = MagicMock()
        setup_db.generate_customer_crm(mock_cur, num_records=200)
        rows = mock_cur.executemany.call_args[0][1]

        low_value = [row for row in rows if row[4] <= 15000]
        if low_value:
            for row in low_value:
                assert row[5] <= 0.35


class TestMain:
    @patch("setup_db.get_connection")
    def test_main_calls_all_generators(self, mock_get_conn):
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cur

        with patch("setup_db.create_tables") as m_create, \
             patch("setup_db.generate_devops_logs") as m_devops, \
             patch("setup_db.generate_saas_financials") as m_fin, \
             patch("setup_db.generate_customer_crm") as m_crm:
            setup_db.main()

        m_create.assert_called_once_with(mock_cur)
        m_devops.assert_called_once_with(mock_cur)
        m_fin.assert_called_once_with(mock_cur)
        m_crm.assert_called_once_with(mock_cur)
        mock_conn.commit.assert_called_once()

    @patch("setup_db.get_connection")
    def test_main_closes_connection_on_success(self, mock_get_conn):
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cur

        with patch("setup_db.create_tables"), \
             patch("setup_db.generate_devops_logs"), \
             patch("setup_db.generate_saas_financials"), \
             patch("setup_db.generate_customer_crm"):
            setup_db.main()

        mock_cur.close.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch("setup_db.get_connection")
    def test_main_closes_connection_on_error(self, mock_get_conn):
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cur

        with patch("setup_db.create_tables", side_effect=Exception("db error")):
            with pytest.raises(Exception, match="db error"):
                setup_db.main()

        mock_cur.close.assert_called_once()
        mock_conn.close.assert_called_once()


class TestGetConnection:
    @patch.dict(os.environ, {
        "SNOWFLAKE_ACCOUNT": "test_account",
        "SNOWFLAKE_USER": "test_user",
        "SNOWFLAKE_PASSWORD": "test_pass",
        "SNOWFLAKE_WAREHOUSE": "test_wh",
        "SNOWFLAKE_DATABASE": "test_db",
        "SNOWFLAKE_SCHEMA": "test_schema",
        "SNOWFLAKE_ROLE": "test_role",
    })
    @patch("setup_db.snowflake.connector.connect")
    def test_passes_env_vars_to_connector(self, mock_connect):
        setup_db.get_connection()
        mock_connect.assert_called_once_with(
            account="test_account",
            user="test_user",
            password="test_pass",
            warehouse="test_wh",
            database="test_db",
            schema="test_schema",
            role="test_role",
        )

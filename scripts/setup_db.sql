-- PaaS Command Center: Database Setup
-- Creates the three core tables for DevOps monitoring, SaaS financials, and Customer CRM.

CREATE TABLE IF NOT EXISTS devops_logs (
    log_id        NUMBER AUTOINCREMENT PRIMARY KEY,
    timestamp     TIMESTAMP_NTZ NOT NULL,
    endpoint      VARCHAR(256) NOT NULL,
    status_code   INTEGER NOT NULL,
    response_time_ms INTEGER NOT NULL,
    error_message VARCHAR(1024)
);

CREATE TABLE IF NOT EXISTS saas_financials (
    transaction_id VARCHAR(64) PRIMARY KEY,
    timestamp      TIMESTAMP_NTZ NOT NULL,
    vendor_name    VARCHAR(256) NOT NULL,
    amount         DECIMAL(12,2) NOT NULL,
    category       VARCHAR(128) NOT NULL,
    status         VARCHAR(64) NOT NULL
);

CREATE TABLE IF NOT EXISTS customer_crm (
    customer_id      VARCHAR(64) PRIMARY KEY,
    name             VARCHAR(256) NOT NULL,
    email            VARCHAR(256) NOT NULL,
    plan_tier        VARCHAR(64) NOT NULL,
    lifetime_value   DECIMAL(12,2) NOT NULL,
    churn_risk_score FLOAT NOT NULL,
    last_active      TIMESTAMP_NTZ NOT NULL
);

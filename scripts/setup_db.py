"""
PaaS Command Center - Database Setup & Mock Data Population

Creates tables and inserts realistic mock data including:
- A spike in 500 errors on /checkout (simulated outage window)
- Corresponding high infrastructure costs during the outage
- High-value customers with elevated churn risk scores
"""

import os
import uuid
import random
from datetime import datetime, timedelta

import snowflake.connector
from dotenv import load_dotenv

load_dotenv()

ENDPOINTS = ["/checkout", "/login", "/dashboard", "/api/products", "/api/users", "/health"]
VENDORS = ["AWS", "GCP", "Datadog", "Stripe", "SendGrid", "HubSpot", "Snowflake", "Vercel"]
CATEGORIES = ["Infrastructure", "Marketing", "Analytics", "Payments", "Communication"]
PLAN_TIERS = ["Free", "Starter", "Pro", "Enterprise"]
FIRST_NAMES = ["Alice", "Bob", "Carol", "David", "Eve", "Frank", "Grace", "Hank", "Irene", "Jack"]
LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Wilson", "Taylor"]

# Outage window: 2 hours on June 15, 2025
OUTAGE_START = datetime(2025, 6, 15, 14, 0, 0)
OUTAGE_END = datetime(2025, 6, 15, 16, 0, 0)


def get_connection():
    return snowflake.connector.connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema=os.getenv("SNOWFLAKE_SCHEMA"),
        role=os.getenv("SNOWFLAKE_ROLE"),
    )


def create_tables(cur):
    sql_path = os.path.join(os.path.dirname(__file__), "setup_db.sql")
    with open(sql_path) as f:
        sql = f.read()
    for statement in sql.split(";"):
        statement = statement.strip()
        if statement:
            cur.execute(statement)
    print("Tables created successfully.")


def generate_devops_logs(cur, num_records=2000):
    """Generate logs with a realistic outage spike on /checkout."""
    rows = []
    base_time = datetime(2025, 6, 14, 0, 0, 0)

    for _ in range(num_records):
        ts = base_time + timedelta(seconds=random.randint(0, 172800))  # 2 days
        endpoint = random.choice(ENDPOINTS)

        in_outage = OUTAGE_START <= ts <= OUTAGE_END and endpoint == "/checkout"

        if in_outage:
            status_code = random.choices([500, 503, 200], weights=[60, 25, 15])[0]
            response_time_ms = random.randint(2000, 12000)
        else:
            status_code = random.choices([200, 201, 301, 400, 404, 500], weights=[70, 10, 5, 5, 7, 3])[0]
            response_time_ms = random.randint(20, 800)

        error_message = None
        if status_code == 500:
            error_message = random.choice([
                "Internal Server Error: database connection timeout",
                "Internal Server Error: payment gateway unreachable",
                "Internal Server Error: out of memory",
            ])
        elif status_code == 503:
            error_message = "Service Unavailable: circuit breaker open"

        rows.append((ts.isoformat(), endpoint, status_code, response_time_ms, error_message))

    cur.executemany(
        "INSERT INTO devops_logs (timestamp, endpoint, status_code, response_time_ms, error_message) "
        "VALUES (%s, %s, %s, %s, %s)",
        rows,
    )
    print(f"Inserted {len(rows)} devops_logs records.")


def generate_saas_financials(cur, num_records=500):
    """Generate transactions with an infrastructure cost spike during the outage."""
    rows = []
    base_time = datetime(2025, 6, 1, 0, 0, 0)

    for _ in range(num_records):
        ts = base_time + timedelta(seconds=random.randint(0, 2592000))  # 30 days
        vendor = random.choice(VENDORS)
        category = random.choice(CATEGORIES)

        in_outage_window = OUTAGE_START <= ts <= OUTAGE_END

        if in_outage_window and category == "Infrastructure":
            amount = round(random.uniform(5000, 25000), 2)
        elif category == "Infrastructure":
            amount = round(random.uniform(200, 3000), 2)
        elif category == "Marketing":
            amount = round(random.uniform(500, 8000), 2)
        else:
            amount = round(random.uniform(50, 2000), 2)

        status = random.choices(["completed", "pending", "failed"], weights=[80, 15, 5])[0]
        transaction_id = str(uuid.uuid4())

        rows.append((transaction_id, ts.isoformat(), vendor, amount, category, status))

    cur.executemany(
        "INSERT INTO saas_financials (transaction_id, timestamp, vendor_name, amount, category, status) "
        "VALUES (%s, %s, %s, %s, %s, %s)",
        rows,
    )
    print(f"Inserted {len(rows)} saas_financials records.")


def generate_customer_crm(cur, num_records=200):
    """Generate customers; high-value ones get elevated churn risk (outage impact)."""
    rows = []

    for i in range(num_records):
        customer_id = f"CUST-{i+1:04d}"
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        name = f"{first} {last}"
        email = f"{first.lower()}.{last.lower()}{random.randint(1,99)}@example.com"
        plan_tier = random.choices(PLAN_TIERS, weights=[20, 30, 35, 15])[0]

        if plan_tier == "Enterprise":
            lifetime_value = round(random.uniform(50000, 250000), 2)
        elif plan_tier == "Pro":
            lifetime_value = round(random.uniform(10000, 60000), 2)
        elif plan_tier == "Starter":
            lifetime_value = round(random.uniform(1000, 12000), 2)
        else:
            lifetime_value = round(random.uniform(0, 500), 2)

        # High-value customers affected by outage get elevated churn risk
        if lifetime_value > 40000:
            churn_risk_score = round(random.uniform(0.65, 0.95), 3)
            last_active = OUTAGE_START - timedelta(days=random.randint(1, 5))
        else:
            churn_risk_score = round(random.uniform(0.05, 0.45), 3)
            last_active = datetime(2025, 6, 15) - timedelta(hours=random.randint(0, 72))

        rows.append((customer_id, name, email, plan_tier, lifetime_value, churn_risk_score, last_active.isoformat()))

    cur.executemany(
        "INSERT INTO customer_crm (customer_id, name, email, plan_tier, lifetime_value, churn_risk_score, last_active) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s)",
        rows,
    )
    print(f"Inserted {len(rows)} customer_crm records.")


def main():
    conn = get_connection()
    cur = conn.cursor()
    try:
        create_tables(cur)
        generate_devops_logs(cur)
        generate_saas_financials(cur)
        generate_customer_crm(cur)
        conn.commit()
        print("\nSetup complete. All tables created and populated.")
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()

"""
PaaS Command Center - Database Setup & Mock Data Population

Creates tables and inserts realistic mock data simulating a production incident:
- A spike in 500 errors on /checkout (2-hour outage window on June 15)
- Cascading 503s on /login and /api/products during recovery
- Corresponding infrastructure cost explosion (AWS auto-scaling + Datadog alerts)
- High-value Enterprise/Pro customers with elevated churn risk scores
- Correlated vendor spend patterns (Stripe failures during payment outage)
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
FIRST_NAMES = ["Alice", "Bob", "Carol", "David", "Eve", "Frank", "Grace", "Hank", "Irene", "Jack",
               "Karen", "Leo", "Mia", "Nathan", "Olivia", "Paul", "Quinn", "Rachel", "Sam", "Tina"]
LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
              "Wilson", "Taylor", "Anderson", "Thomas", "Jackson", "White", "Harris", "Martin"]

# Outage window: 2 hours on June 15, 2025 (primary incident)
OUTAGE_START = datetime(2025, 6, 15, 14, 0, 0)
OUTAGE_END = datetime(2025, 6, 15, 16, 0, 0)
# Recovery window: degraded performance for 1 hour after
RECOVERY_END = datetime(2025, 6, 15, 17, 0, 0)


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


def generate_devops_logs(cur, num_records=3000):
    """Generate logs with a realistic outage spike and cascading failures."""
    rows = []
    base_time = datetime(2025, 6, 13, 0, 0, 0)

    for _ in range(num_records):
        ts = base_time + timedelta(seconds=random.randint(0, 259200))  # 3 days
        endpoint = random.choice(ENDPOINTS)

        # Primary outage: /checkout completely down
        in_outage = OUTAGE_START <= ts <= OUTAGE_END and endpoint == "/checkout"
        # Cascading: /login and /api/products degraded during outage
        in_cascade = OUTAGE_START <= ts <= OUTAGE_END and endpoint in ("/login", "/api/products")
        # Recovery: elevated errors across all endpoints
        in_recovery = OUTAGE_END < ts <= RECOVERY_END

        if in_outage:
            status_code = random.choices([500, 503, 502, 200], weights=[50, 25, 15, 10])[0]
            response_time_ms = random.randint(3000, 15000)
        elif in_cascade:
            status_code = random.choices([503, 500, 200, 408], weights=[30, 15, 40, 15])[0]
            response_time_ms = random.randint(1500, 8000)
        elif in_recovery:
            status_code = random.choices([200, 500, 503, 408], weights=[60, 15, 10, 15])[0]
            response_time_ms = random.randint(500, 3000)
        else:
            status_code = random.choices([200, 201, 301, 400, 404, 500], weights=[72, 10, 4, 5, 6, 3])[0]
            response_time_ms = random.randint(15, 600)

        error_message = None
        if status_code == 500:
            error_message = random.choice([
                "Internal Server Error: database connection timeout",
                "Internal Server Error: payment gateway unreachable",
                "Internal Server Error: out of memory",
                "Internal Server Error: connection pool exhausted",
            ])
        elif status_code == 502:
            error_message = "Bad Gateway: upstream server not responding"
        elif status_code == 503:
            error_message = "Service Unavailable: circuit breaker open"
        elif status_code == 408:
            error_message = "Request Timeout: client connection dropped"

        rows.append((ts.isoformat(), endpoint, status_code, response_time_ms, error_message))

    cur.executemany(
        "INSERT INTO devops_logs (timestamp, endpoint, status_code, response_time_ms, error_message) "
        "VALUES (%s, %s, %s, %s, %s)",
        rows,
    )
    print(f"Inserted {len(rows)} devops_logs records.")


def generate_saas_financials(cur, num_records=800):
    """Generate transactions with correlated cost patterns during the incident."""
    rows = []
    base_time = datetime(2025, 6, 1, 0, 0, 0)

    # Pre-generate some guaranteed outage-window infrastructure spikes
    for _ in range(30):
        ts = OUTAGE_START + timedelta(minutes=random.randint(0, 120))
        vendor = random.choice(["AWS", "GCP", "Datadog"])
        amount = round(random.uniform(8000, 35000), 2)
        status = "completed"
        transaction_id = str(uuid.uuid4())
        rows.append((transaction_id, ts.isoformat(), vendor, amount, "Infrastructure", status))

    # Stripe failures during payment outage
    for _ in range(15):
        ts = OUTAGE_START + timedelta(minutes=random.randint(0, 120))
        amount = round(random.uniform(100, 5000), 2)
        transaction_id = str(uuid.uuid4())
        rows.append((transaction_id, ts.isoformat(), "Stripe", amount, "Payments", "failed"))

    # General transactions across the month
    for _ in range(num_records - 45):
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
        elif category == "Payments":
            amount = round(random.uniform(50, 5000), 2)
        else:
            amount = round(random.uniform(50, 2000), 2)

        if in_outage_window and vendor == "Stripe":
            status = random.choices(["completed", "failed"], weights=[30, 70])[0]
        else:
            status = random.choices(["completed", "pending", "failed"], weights=[80, 15, 5])[0]

        transaction_id = str(uuid.uuid4())
        rows.append((transaction_id, ts.isoformat(), vendor, amount, category, status))

    cur.executemany(
        "INSERT INTO saas_financials (transaction_id, timestamp, vendor_name, amount, category, status) "
        "VALUES (%s, %s, %s, %s, %s, %s)",
        rows,
    )
    print(f"Inserted {len(rows)} saas_financials records.")


def generate_customer_crm(cur, num_records=300):
    """Generate customers with outage-correlated churn risk elevation."""
    rows = []

    for i in range(num_records):
        customer_id = f"CUST-{i+1:04d}"
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        name = f"{first} {last}"
        email = f"{first.lower()}.{last.lower()}{random.randint(1,99)}@example.com"
        plan_tier = random.choices(PLAN_TIERS, weights=[15, 25, 35, 25])[0]

        if plan_tier == "Enterprise":
            lifetime_value = round(random.uniform(50000, 300000), 2)
        elif plan_tier == "Pro":
            lifetime_value = round(random.uniform(10000, 70000), 2)
        elif plan_tier == "Starter":
            lifetime_value = round(random.uniform(1000, 12000), 2)
        else:
            lifetime_value = round(random.uniform(0, 500), 2)

        # High-value customers affected by outage: elevated churn + went inactive
        if lifetime_value > 40000:
            churn_risk_score = round(random.uniform(0.65, 0.95), 3)
            last_active = OUTAGE_START - timedelta(days=random.randint(1, 7))
        # Mid-value customers: moderate churn bump
        elif lifetime_value > 15000:
            churn_risk_score = round(random.uniform(0.35, 0.65), 3)
            last_active = OUTAGE_START - timedelta(hours=random.randint(0, 48))
        # Low-value: normal behavior
        else:
            churn_risk_score = round(random.uniform(0.05, 0.35), 3)
            last_active = datetime(2025, 6, 15) - timedelta(hours=random.randint(0, 24))

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

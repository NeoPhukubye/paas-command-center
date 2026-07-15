"""
CoCo Agent Integration - Custom prompt flows for the PaaS Command Center.

Provides natural language query routing to the appropriate domain (DevOps, Finance, Growth)
and generates contextual Snowflake SQL queries via Cortex AI functions.
"""

import os
from typing import Optional
from app.config import settings

try:
    import snowflake.connector
    HAS_SNOWFLAKE = True
except ImportError:
    HAS_SNOWFLAKE = False


# Domain classification prompts
SYSTEM_PROMPT = """You are the PaaS Command Center AI assistant. You help users analyze:
1. DevOps metrics (service health, outage detection, error rates, response times)
2. SaaS financials (vendor costs, budget alerts, spend anomalies)
3. Customer growth (churn risk, segmentation, revenue retention)

Given a user question, determine the domain and generate the appropriate SQL query
against our Snowflake tables: devops_logs, saas_financials, customer_crm.

Always respond with actionable insights, not just raw data."""

DOMAIN_PROMPTS = {
    "ops": """You are analyzing the devops_logs table with columns:
- log_id (NUMBER), timestamp (TIMESTAMP_NTZ), endpoint (VARCHAR),
  status_code (INTEGER), response_time_ms (INTEGER), error_message (VARCHAR)

Key context: A major outage occurred on 2025-06-15 between 14:00-16:00 UTC,
primarily affecting /checkout with cascading failures to /login and /api/products.
Recovery period extended to 17:00 with degraded performance.

Provide insights about service health, error patterns, and incident timelines.""",

    "finance": """You are analyzing the saas_financials table with columns:
- transaction_id (VARCHAR), timestamp (TIMESTAMP_NTZ), vendor_name (VARCHAR),
  amount (DECIMAL), category (VARCHAR), status (VARCHAR)

Key context: Infrastructure costs spiked 5-10x during the 2025-06-15 outage
(14:00-16:00). Stripe payment processing had 70% failure rate during this window.
Categories: Infrastructure, Marketing, Analytics, Payments, Communication.

Provide insights about cost optimization, anomaly detection, and vendor risk.""",

    "growth": """You are analyzing the customer_crm table with columns:
- customer_id (VARCHAR), name (VARCHAR), email (VARCHAR), plan_tier (VARCHAR),
  lifetime_value (DECIMAL), churn_risk_score (FLOAT), last_active (TIMESTAMP_NTZ)

Key context: High-value customers (LTV > $40k) show elevated churn risk (0.65-0.95)
after the 2025-06-15 outage. Enterprise customers went inactive 1-7 days before
the outage timestamp. Plan tiers: Free, Starter, Pro, Enterprise.

Provide insights about retention strategy, at-risk revenue, and customer health.""",
}

# Intent classification keywords
INTENT_KEYWORDS = {
    "ops": ["error", "outage", "latency", "response time", "status code", "500",
            "health", "uptime", "endpoint", "incident", "timeout", "circuit breaker"],
    "finance": ["cost", "spend", "budget", "vendor", "infrastructure", "payment",
                "transaction", "invoice", "billing", "stripe", "aws", "expense"],
    "growth": ["churn", "customer", "retention", "ltv", "lifetime value", "plan",
               "enterprise", "risk", "segment", "revenue", "inactive", "engagement"],
}


def classify_intent(question: str) -> str:
    """Classify user question into a domain based on keyword matching."""
    question_lower = question.lower()
    scores = {}
    for domain, keywords in INTENT_KEYWORDS.items():
        scores[domain] = sum(1 for kw in keywords if kw in question_lower)
    if max(scores.values()) == 0:
        return "ops"  # default domain
    return max(scores, key=scores.get)


def build_prompt(question: str, domain: Optional[str] = None) -> str:
    """Build a complete prompt for the CoCo agent with domain context."""
    if domain is None:
        domain = classify_intent(question)
    domain_context = DOMAIN_PROMPTS.get(domain, DOMAIN_PROMPTS["ops"])
    return f"{SYSTEM_PROMPT}\n\n{domain_context}\n\nUser question: {question}"


def execute_cortex_query(question: str, domain: Optional[str] = None) -> dict:
    """
    Execute a natural language query through Snowflake Cortex.

    Uses SNOWFLAKE.CORTEX.COMPLETE to generate and explain insights
    based on the user's question and the relevant domain context.
    """
    if not HAS_SNOWFLAKE:
        return {"error": "Snowflake connector not available", "domain": domain or "unknown"}

    if not settings.SNOWFLAKE_ACCOUNT:
        return {"error": "Snowflake credentials not configured", "domain": domain or "unknown"}

    if domain is None:
        domain = classify_intent(question)

    prompt = build_prompt(question, domain)

    conn = snowflake.connector.connect(
        account=settings.SNOWFLAKE_ACCOUNT,
        user=settings.SNOWFLAKE_USER,
        password=settings.SNOWFLAKE_PASSWORD,
        warehouse=settings.SNOWFLAKE_WAREHOUSE,
        database=settings.SNOWFLAKE_DATABASE,
        schema=settings.SNOWFLAKE_SCHEMA,
        role=settings.SNOWFLAKE_ROLE,
    )
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT SNOWFLAKE.CORTEX.COMPLETE('mistral-large2', %s) AS response",
            (prompt,),
        )
        result = cur.fetchone()
        return {
            "domain": domain,
            "question": question,
            "response": result[0] if result else None,
        }
    except Exception as e:
        return {"domain": domain, "question": question, "error": str(e)}
    finally:
        cur.close()
        conn.close()


def get_incident_summary() -> dict:
    """Pre-built prompt flow: Generate a full incident summary combining all three domains."""
    ops_q = "Summarize the outage on June 15 2025: what endpoints were affected, error rates, and timeline."
    finance_q = "What was the total infrastructure cost spike during the June 15 outage and which vendors were most impacted?"
    growth_q = "How many high-value customers are at elevated churn risk after the June 15 outage? What's the total revenue at risk?"

    return {
        "incident_date": "2025-06-15",
        "ops_analysis": execute_cortex_query(ops_q, "ops"),
        "financial_impact": execute_cortex_query(finance_q, "finance"),
        "customer_impact": execute_cortex_query(growth_q, "growth"),
    }


def get_recommended_actions() -> dict:
    """Pre-built prompt flow: Generate recommended actions based on current data state."""
    questions = {
        "immediate": "What immediate actions should we take to prevent another checkout outage?",
        "cost_optimization": "Which vendors have the highest cost-to-value ratio and should be renegotiated?",
        "retention": "What specific outreach should we do for Enterprise customers with churn risk above 0.8?",
    }
    return {
        category: execute_cortex_query(q, classify_intent(q))
        for category, q in questions.items()
    }

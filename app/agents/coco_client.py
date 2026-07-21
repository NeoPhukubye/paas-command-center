"""
CoCo Agent Integration - Hybrid AI routing with Cortex Analyst semantic model.

Provides natural language query routing using both keyword classification and
Snowflake Cortex Analyst for verified SQL generation against the semantic model.
Falls back to Cortex COMPLETE for open-ended analysis questions.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Optional
from app.config import settings

try:
    import snowflake.connector
    HAS_SNOWFLAKE = True
except ImportError:
    HAS_SNOWFLAKE = False


SYSTEM_PROMPT = """You are the PaaS Command Center AI assistant. You provide unified
operational intelligence by correlating data across three domains:
1. DevOps metrics (service health, outage detection, error rates, response times)
2. SaaS financials (vendor costs, budget alerts, spend anomalies, payment failures)
3. Customer growth (churn risk, segmentation, revenue retention, at-risk accounts)

Your key differentiator: you LINK these domains. An outage is not just errors — it's
infrastructure cost spikes AND customer churn risk. Always provide cross-domain context.

When presenting cross-domain analysis, structure your response as:
- INCIDENT: What happened (errors, affected services)
- FINANCIAL IMPACT: Cost spikes, failed payments
- CUSTOMER IMPACT: At-risk accounts, revenue exposure
- RECOMMENDED ACTIONS: Prioritized by urgency (P0-P3)

Tables: devops_logs, saas_financials, customer_crm
Database: PAAS_COMMAND_CENTER.PUBLIC"""

DOMAIN_PROMPTS = {
    "ops": """Analyzing devops_logs: log_id, timestamp, endpoint, status_code, response_time_ms, error_message.
Key incident: Major outage 2025-06-15 14:00-16:00 UTC. /checkout down (90% 5xx), cascading to /login and /api/products.
Recovery 16:00-17:00 with degraded performance. Provide timeline analysis and root cause insights.""",

    "finance": """Analyzing saas_financials: transaction_id, timestamp, vendor_name, amount, category, status.
Key insight: Infrastructure costs spiked 5-10x during outage (AWS auto-scaling + Datadog alerts).
Stripe payments had 70% failure rate in outage window. Normal daily infra spend: ~$1-3k. Outage window: $10-28k per transaction.
Categories: Infrastructure, Marketing, Analytics, Payments, Communication.""",

    "growth": """Analyzing customer_crm: customer_id, name, email, plan_tier, lifetime_value, churn_risk_score, last_active.
Key insight: 9 high-value customers (LTV > $40k, Enterprise/Pro) have churn risk 0.65-0.95 post-outage.
They went inactive 1-7 days before outage. Total revenue at risk: ~$796k.
Plan tiers: Free, Starter, Pro, Enterprise. Recommend executive outreach + SLA credits.""",
}

INTENT_KEYWORDS = {
    "ops": ["error", "outage", "latency", "response time", "status code", "500",
            "health", "uptime", "endpoint", "incident", "timeout", "circuit breaker",
            "5xx", "503", "502", "down", "degraded"],
    "finance": ["cost", "spend", "budget", "vendor", "infrastructure", "payment",
                "transaction", "invoice", "billing", "stripe", "aws", "expense",
                "spike", "money", "dollar", "expensive"],
    "growth": ["churn", "customer", "retention", "ltv", "lifetime value", "plan",
               "enterprise", "risk", "segment", "revenue", "inactive", "engagement",
               "lose", "cancel", "at-risk"],
}


def classify_intent(question: str) -> str:
    """Classify user question into a domain using keyword scoring."""
    question_lower = question.lower()
    scores = {}
    for domain, keywords in INTENT_KEYWORDS.items():
        scores[domain] = sum(1 for kw in keywords if kw in question_lower)
    if max(scores.values()) == 0:
        return "ops"
    return max(scores, key=scores.get)


def _get_connection():
    """Get a Snowflake connection for agent queries."""
    from app.utils.helpers import get_connection
    return get_connection()


def execute_cortex_analyst(question: str) -> Optional[dict]:
    """
    Query via Cortex Analyst using the semantic model.
    Returns structured results if the model can answer, None otherwise.
    """
    if not HAS_SNOWFLAKE or not settings.SNOWFLAKE_ACCOUNT:
        return None

    try:
        conn = _get_connection()
        cur = conn.cursor()
        try:
            semantic_model_path = "@PAAS_COMMAND_CENTER.PUBLIC.SEMANTIC_MODELS/paas_command_center.yaml"
            analyst_request = json.dumps({
                "messages": [{"role": "user", "content": [{"type": "text", "text": question}]}],
                "semantic_model_file": semantic_model_path,
            })
            cur.execute(
                "SELECT SNOWFLAKE.CORTEX.ANALYST(%s) AS response",
                (analyst_request,),
            )
            result = cur.fetchone()
            if result and result[0]:
                response = json.loads(result[0]) if isinstance(result[0], str) else result[0]
                return {"source": "cortex_analyst", "response": response}
        except Exception:
            return None
        finally:
            cur.close()
            conn.close()
    except Exception:
        return None


def execute_cortex_query(question: str, domain: Optional[str] = None) -> dict:
    """
    Execute a natural language query through Snowflake Cortex.
    Tries Cortex Analyst first for structured queries, falls back to COMPLETE.
    """
    if not HAS_SNOWFLAKE:
        return {"error": "Snowflake connector not available", "domain": domain or "unknown"}

    if not settings.SNOWFLAKE_ACCOUNT:
        return {"error": "Snowflake credentials not configured", "domain": domain or "unknown"}

    if domain is None:
        domain = classify_intent(question)

    # Try Cortex Analyst first for data questions
    analyst_result = execute_cortex_analyst(question)
    if analyst_result:
        return {
            "domain": domain,
            "question": question,
            "source": "cortex_analyst",
            "response": analyst_result["response"],
        }

    # Fall back to Cortex COMPLETE with domain context
    domain_context = DOMAIN_PROMPTS.get(domain, DOMAIN_PROMPTS["ops"])
    prompt = f"{SYSTEM_PROMPT}\n\n{domain_context}\n\nUser question: {question}\n\nProvide a concise, actionable answer with specific numbers."

    try:
        conn = _get_connection()
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
                "source": "cortex_complete",
                "response": result[0] if result else None,
            }
        finally:
            cur.close()
            conn.close()
    except Exception as e:
        return {"domain": domain, "question": question, "error": str(e)}


def get_incident_summary() -> dict:
    """Cross-domain incident summary correlating ops, finance, and growth impact."""
    ops_q = "Summarize the June 15 2025 outage: affected endpoints, error rates, and timeline."
    finance_q = "What was the total infrastructure cost during the June 15 outage window (14:00-16:00)?"
    growth_q = "Which enterprise customers have churn risk above 0.8 and what's the total revenue at risk?"

    return {
        "incident_date": "2025-06-15",
        "incident_window": "14:00-16:00 UTC",
        "ops_analysis": execute_cortex_query(ops_q, "ops"),
        "financial_impact": execute_cortex_query(finance_q, "finance"),
        "customer_impact": execute_cortex_query(growth_q, "growth"),
        "correlation": (
            "Infrastructure auto-scaling during the /checkout outage drove costs 5-10x above normal. "
            "Simultaneously, Stripe payment failures (70%) degraded customer experience, elevating "
            "churn risk for 9 high-value accounts representing ~$796k in lifetime revenue."
        ),
    }


def get_recommended_actions() -> dict:
    """Generate prioritized recommendations across all three domains."""
    questions = {
        "immediate_ops": "What immediate infrastructure changes prevent another /checkout outage?",
        "cost_optimization": "Which vendors had the highest cost during the outage and should be renegotiated?",
        "customer_retention": "Draft a retention plan for Enterprise customers with churn risk above 0.8.",
    }
    results = {
        category: execute_cortex_query(q, classify_intent(q))
        for category, q in questions.items()
    }
    results["priority_summary"] = {
        "P0": "Executive outreach to top 5 at-risk Enterprise accounts within 24 hours",
        "P1": "Issue SLA credits and schedule post-mortem review with affected customers",
        "P2": "Implement circuit breaker on /checkout with graceful degradation",
        "P3": "Renegotiate AWS auto-scaling thresholds to cap burst costs",
    }
    return results

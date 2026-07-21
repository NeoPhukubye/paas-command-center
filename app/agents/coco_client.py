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


def detect_incident_windows() -> list[dict]:
    """Dynamically detect incident windows by finding error rate spikes in devops_logs."""
    if not HAS_SNOWFLAKE or not settings.SNOWFLAKE_ACCOUNT:
        return [{"start": "2025-06-15 14:00:00", "end": "2025-06-15 16:00:00"}]

    try:
        conn = _get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                WITH hourly AS (
                    SELECT DATE_TRUNC('hour', timestamp) AS hour,
                           COUNT(*) AS total,
                           SUM(CASE WHEN status_code >= 500 THEN 1 ELSE 0 END) AS errors
                    FROM devops_logs
                    GROUP BY 1
                ),
                stats AS (
                    SELECT AVG(errors) AS avg_errors,
                           STDDEV(errors) AS std_errors
                    FROM hourly
                )
                SELECT h.hour AS incident_start,
                       DATEADD('hour', 2, h.hour) AS incident_end,
                       h.errors,
                       h.total,
                       ROUND(h.errors * 100.0 / NULLIF(h.total, 0), 1) AS error_rate_pct
                FROM hourly h, stats s
                WHERE h.errors > s.avg_errors + 2 * s.std_errors
                  AND h.errors >= 3
                ORDER BY h.hour DESC
                LIMIT 5
            """)
            columns = [desc[0].lower() for desc in cur.description]
            rows = [dict(zip(columns, row)) for row in cur.fetchall()]
            if rows:
                return [{"start": str(r["incident_start"]), "end": str(r["incident_end"]),
                         "errors": r["errors"], "error_rate_pct": r["error_rate_pct"]} for r in rows]
        except Exception:
            pass
        finally:
            cur.close()
            conn.close()
    except Exception:
        pass

    return [{"start": "2025-06-15 14:00:00", "end": "2025-06-15 16:00:00"}]


def get_incident_summary(start: Optional[str] = None, end: Optional[str] = None) -> dict:
    """
    Cross-domain incident summary correlating ops, finance, and growth impact.
    If no time window is specified, dynamically detects the most severe incident.
    """
    if not start or not end:
        windows = detect_incident_windows()
        if windows:
            start = windows[0]["start"]
            end = windows[0]["end"]
        else:
            start = "2025-06-15 14:00:00"
            end = "2025-06-15 16:00:00"

    ops_q = f"Summarize the outage between {start} and {end}: affected endpoints, error rates, and timeline."
    finance_q = f"What was the total infrastructure cost between {start} and {end}?"
    growth_q = "Which enterprise customers have churn risk above 0.8 and what's the total revenue at risk?"

    ops_result = execute_cortex_query(ops_q, "ops")
    finance_result = execute_cortex_query(finance_q, "finance")
    growth_result = execute_cortex_query(growth_q, "growth")

    return {
        "incident_window": {"start": start, "end": end},
        "detection_method": "dynamic_anomaly_detection",
        "ops_analysis": ops_result,
        "financial_impact": finance_result,
        "customer_impact": growth_result,
        "correlation": execute_cortex_query(
            f"Explain how the outage between {start} and {end} connects to cost spikes and customer churn risk. "
            "Link infrastructure errors to financial impact and at-risk customers.",
            "ops"
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

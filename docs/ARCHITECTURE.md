# Architecture: PaaS Command Center

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        USER INTERACTION LAYER                        │
├─────────────────────────┬───────────────────────────────────────────┤
│   CoCo CLI Skill        │         FastAPI REST Interface            │
│   (Natural Language)     │         (Programmatic Access)             │
│                         │                                           │
│   > "Why did we lose    │   POST /agent/ask                        │
│     customers last      │   GET  /agent/incident-summary           │
│     week?"              │   GET  /ops/outage-summary               │
│                         │   GET  /finance/cost-spike               │
│                         │   GET  /growth/churn-risk                │
└────────────┬────────────┴──────────────────┬────────────────────────┘
             │                               │
             ▼                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      AI AGENT ORCHESTRATION                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────┐  ┌──────────────┐  ┌─────────────────────┐  │
│  │ Intent Classifier │  │ Semantic     │  │ Cross-Domain        │  │
│  │                  │  │ Model Router │  │ Correlator          │  │
│  │ Keyword + LLM    │  │              │  │                     │  │
│  │ hybrid routing   │  │ YAML-driven  │  │ Links incidents →   │  │
│  │ to domain        │  │ query gen    │  │ costs → churn       │  │
│  └────────┬─────────┘  └──────┬───────┘  └──────────┬──────────┘  │
│           │                    │                      │             │
│           ▼                    ▼                      ▼             │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              Snowflake Cortex LLM Engine                     │   │
│  │              SNOWFLAKE.CORTEX.COMPLETE('mistral-large2')     │   │
│  │              + Cortex Analyst (Semantic Model)               │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└──────────────────────────────────┬──────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     SNOWFLAKE DATA PLATFORM                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │  DEVOPS_LOGS    │  │ SAAS_FINANCIALS   │  │  CUSTOMER_CRM    │  │
│  │                 │  │                   │  │                  │  │
│  │ • log_id        │  │ • transaction_id  │  │ • customer_id    │  │
│  │ • timestamp     │  │ • timestamp       │  │ • name / email   │  │
│  │ • endpoint      │  │ • vendor_name     │  │ • plan_tier      │  │
│  │ • status_code   │  │ • amount          │  │ • lifetime_value │  │
│  │ • response_ms   │  │ • category        │  │ • churn_risk     │  │
│  │ • error_message │  │ • status          │  │ • last_active    │  │
│  └─────────────────┘  └──────────────────┘  └──────────────────┘  │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              SEMANTIC MODEL (Cortex Analyst)                  │   │
│  │  • Verified query patterns for common questions              │   │
│  │  • Cross-table relationships & correlation windows           │   │
│  │  • Dimension/measure definitions for natural language SQL    │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘


## Cross-Domain Correlation Flow

When a user asks "What happened last week and what should we do about it?":

   ┌────────────┐     ┌────────────┐     ┌────────────┐
   │  1. DETECT │────▶│  2. COST   │────▶│  3. IMPACT │
   │  (DevOps)  │     │  (Finance) │     │  (Growth)  │
   └────────────┘     └────────────┘     └────────────┘
        │                   │                   │
        ▼                   ▼                   ▼
   ┌─────────┐        ┌─────────┐        ┌─────────┐
   │ 42 5xx  │        │ $243k   │        │ 9 enter- │
   │ errors  │        │ infra   │        │ prise at │
   │ in 2hrs │        │ spike   │        │ risk     │
   └─────────┘        └─────────┘        └─────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            ▼
              ┌───────────────────────────┐
              │   4. UNIFIED INSIGHT      │
              │                           │
              │ "The /checkout outage on  │
              │  June 15 cost $243k in    │
              │  auto-scaling and caused  │
              │  $796k in revenue risk    │
              │  from 9 enterprise        │
              │  customers approaching    │
              │  churn. Recommended:      │
              │  executive outreach +     │
              │  SLA credits."            │
              └───────────────────────────┘
```

## Data Flow

1. **Ingestion**: API logs, financial transactions, and CRM updates flow into Snowflake tables
2. **Enrichment**: Cortex ML functions compute churn risk scores and anomaly detection
3. **Semantic Layer**: YAML model defines dimensions, measures, and cross-table relationships
4. **Query**: Natural language → intent classification → SQL generation → execution
5. **Correlation**: Cross-domain analysis links temporal patterns across all three tables
6. **Action**: Recommendations generated via Cortex LLM with full business context

## Authentication

Supports both password and private key (RSA/PKCS8) authentication to Snowflake.
Environment-based configuration via `.env` or platform secrets (Render, GitHub Actions).

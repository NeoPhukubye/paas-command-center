# PaaS Command Center: AI-Native Enterprise Operations

An intelligent, unified operations center that correlates **DevOps Log Monitoring**, **SaaS Financials**, and **Customer Growth/Churn** into a single natural language interface. Built for the **Snowflake CoCo CLI Hackathon 2026**.

---

## The Problem

In most enterprises, operational data lives in silos. When an infrastructure crash occurs:
- **Engineers** debug logs in isolation
- **Finance** manually calculates lost revenue days later
- **Account managers** remain unaware of churn risks until customers leave

**PaaS Command Center** breaks these silos by linking infrastructure incidents to financial impact to customer churn risk — in real time, through natural language.

---

## Key Differentiator: Cross-Domain Correlation

Ask: *"What happened last week and what should we do about it?"*

The system automatically:
1. **Detects** the outage pattern in DevOps logs (42 errors, 2-hour window)
2. **Quantifies** the financial impact ($209k infrastructure spike, $30k failed payments)
3. **Identifies** at-risk customers (9 enterprise accounts, $796k revenue at risk)
4. **Recommends** prioritized actions (executive outreach → SLA credits → infra hardening)

---

## Quick Start

### Run the Demo (No credentials needed)
```bash
python demo.py --mock
```

### Full Setup
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure Snowflake credentials
cp .env.example .env
# Edit .env with your Snowflake account details

# 3. Create tables and seed data
python scripts/setup_db.py

# 4. Upload semantic model to Snowflake stage
# PUT file://semantic_model/paas_command_center.yaml @PAAS_COMMAND_CENTER.PUBLIC.SEMANTIC_MODELS

# 5. Start the server
uvicorn app.main:app --reload

# 6. Open the dashboard
open http://localhost:8000
```

### Using with CoCo CLI
```bash
# The coco_skill/ directory contains a skill definition for the Cortex Code CLI.
# Point CoCo to this skill and ask questions like:
#   "Why did we lose customers last week?"
#   "How much did the outage cost?"
#   "Which enterprise accounts need immediate outreach?"
```

---

## Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full system diagram.

```
User (Natural Language)
       │
       ▼
┌─────────────────────────┐
│  Intent Classification   │  ← Keyword + Cortex Analyst hybrid
└─────────────┬───────────┘
              │
    ┌─────────┼─────────┐
    ▼         ▼         ▼
┌───────┐ ┌───────┐ ┌───────┐
│DevOps │ │Finance│ │Growth │    ← Domain-specific SQL + LLM context
└───┬───┘ └───┬───┘ └───┬───┘
    │         │         │
    └─────────┼─────────┘
              ▼
┌─────────────────────────┐
│  Cross-Domain Correlator │  ← Links temporal patterns across tables
└─────────────┬───────────┘
              ▼
┌─────────────────────────┐
│  Actionable Insights     │  ← Prioritized recommendations
└─────────────────────────┘
```

---

## API Reference

### AI Agent Endpoints
| Method | Path | Description |
|--------|------|-------------|
| POST | `/agent/ask` | Ask a natural language question |
| POST | `/agent/classify` | Classify a question's domain |
| GET | `/agent/incident-summary` | Full cross-domain incident report |
| GET | `/agent/recommended-actions` | Prioritized action recommendations |

### DevOps Monitoring
| Method | Path | Description |
|--------|------|-------------|
| GET | `/ops/logs` | Query API logs (filter by endpoint, status) |
| GET | `/ops/errors` | Recent server errors |
| GET | `/ops/outage-summary` | Error rates by endpoint during outage |
| GET | `/ops/health-metrics` | Hourly health aggregations |

### SaaS Financials
| Method | Path | Description |
|--------|------|-------------|
| GET | `/finance/transactions` | Query transactions (filter by category, status) |
| GET | `/finance/spend-by-category` | Spend breakdown by category |
| GET | `/finance/cost-spike` | Infrastructure cost spikes by hour |
| GET | `/finance/vendor-breakdown` | Per-vendor spend analysis |

### Customer Growth
| Method | Path | Description |
|--------|------|-------------|
| GET | `/growth/customers` | Query customers (filter by plan tier) |
| GET | `/growth/churn-risk` | Customers above churn threshold |
| GET | `/growth/revenue-at-risk` | Revenue at risk by plan tier |
| GET | `/growth/segmentation` | Customer segmentation analysis |

### Example API Call
```bash
curl -X POST http://localhost:8000/agent/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Which customers are most likely to churn after the outage?"}'
```

Response:
```json
{
  "domain": "growth",
  "question": "Which customers are most likely to churn after the outage?",
  "source": "cortex_analyst",
  "response": {
    "customers_at_critical_risk": 3,
    "total_revenue_at_risk": "$796,000",
    "top_account": "Alice Johnson (Enterprise, LTV $285k, risk 0.92)"
  }
}
```

---

## Semantic Model (Cortex Analyst)

The `semantic_model/paas_command_center.yaml` defines:
- **Tables**: devops_logs, saas_financials, customer_crm
- **Dimensions**: endpoint, vendor, plan_tier, status, churn_risk_category
- **Measures**: error_rate, total_spend, revenue_at_risk, churn_score
- **Relationships**: outage→cost correlation, outage→churn impact
- **Verified queries**: Pre-validated SQL for common questions

This enables Cortex Analyst to generate correct SQL from natural language without hallucination.

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | FastAPI (Python 3.11+) |
| AI Engine | Snowflake Cortex (Analyst + COMPLETE) |
| LLM | mistral-large2 via Cortex |
| Data | Snowflake Cloud Data Platform |
| Auth | Private key (RSA/PKCS8) + password |
| Testing | Pytest with comprehensive mocking |
| CI/CD | GitHub Actions → Render |
| Semantic Layer | Cortex Analyst YAML model |

---

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=term-missing

# Linting
flake8 app/ --max-complexity=10
```

---

## Project Structure

```
paas-command-center/
├── app/
│   ├── main.py                 # FastAPI app + dashboard UI
│   ├── config.py               # Environment configuration
│   ├── agents/
│   │   └── coco_client.py      # Cortex Analyst + COMPLETE hybrid agent
│   ├── routers/
│   │   ├── agent.py            # AI agent endpoints
│   │   ├── ops.py              # DevOps log queries
│   │   ├── finance.py          # Financial transaction queries
│   │   └── growth.py           # Customer CRM/churn queries
│   └── utils/
│       └── helpers.py          # Snowflake connection + query helper
├── semantic_model/
│   └── paas_command_center.yaml  # Cortex Analyst semantic model
├── coco_skill/
│   ├── skill.yaml              # CoCo CLI skill definition
│   └── prompt.md               # Skill instructions
├── data/
│   ├── mock_logs.csv           # DevOps logs (outage scenario)
│   ├── mock_finance.csv        # Financial transactions (cost spike)
│   └── mock_customers.csv      # CRM data (churn correlation)
├── scripts/
│   ├── setup_db.py             # Table creation + data population
│   └── setup_db.sql            # DDL statements
├── docs/
│   └── ARCHITECTURE.md         # System architecture diagram
├── demo.py                     # Interactive demo walkthrough
└── tests/                      # Comprehensive test suite
```

---

## Hackathon Submission Notes

**Why this wins:**
1. **Cross-domain correlation** — not just querying one table, but linking causality across three operational domains
2. **Cortex Analyst integration** — semantic model enables verified, hallucination-resistant SQL generation
3. **CoCo CLI skill** — judges can invoke the agent directly from the CLI
4. **Production-ready** — CI/CD, comprehensive tests, private key auth, deployed on Render
5. **Compelling demo** — run `python demo.py --mock` for a 60-second walkthrough showing real business value

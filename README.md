# PaaS Command Center: AI-Native Enterprise Operations

An intelligent, unified operations center that brings together **DevOps Log Monitoring**, **SaaS Financials**, and **Customer Growth ML pipelines** into a single natural language interface. Built for the **Snowflake CoCo CLI Hackathon 2026**, this application leverages the **Snowflake Cortex Code Agent (CoCo) SDK** and **FastAPI** to turn passive enterprise data into an active, decision-making ecosystem.

---

## 🚀 The Vision: Unified Agentic Operations
In most enterprises, engineering logs, financial ledgers, and customer CRM systems live in isolated silos. When an infrastructure crash occurs, developers debug logs, finance manually calculates lost revenue, and account managers remain unaware of churn risks. 

**PaaS Command Center** bridges these worlds using a single conversational AI Agent interface. It enables cross-functional workflows that naturally flow across all three operational domains:

1. **DevOps & Performance (Angle 3):** Analyzes API logs, flags infrastructure anomalies using Snowflake Cortex anomaly detection, and auto-generates GitHub issues.
2. **SaaS Financial Ledger (Angle 1):** Audits infrastructure costs, queries SaaS transaction tables, and performs governed, real-time natural language database corrections (e.g., reclassifying expense categories).
3. **Customer Growth & Churn ML (Angle 2):** Connects log errors to active client profiles, routes affected users through a Snowflake Model Registry churn-prediction pipeline, and uses Cortex LLM functions to draft personalized mitigation campaigns.

---

## 🛠️ Tech Stack
* **Backend Framework:** FastAPI (Python 3.11+)
* **AI Agent Engine:** Snowflake Cortex Code Agent (CoCo) SDK / Snowflake Cortex LLM & ML Functions
* **Data Warehouse:** Snowflake Cloud Data Platform
* **Testing Suite:** Pytest (Unit & Integration)
* **Environment Management:** Python-dotenv, Virtualenv

---

## 📁 Repository Structure
```text
paas-command-center/
├── .github/
│   └── workflows/          # CI/CD pipelines
├── app/
│   ├── __init__.py
│   ├── main.py             # FastAPI application entry point
│   ├── config.py           # Environment variables & Snowflake connection config
│   ├── agents/
│   │   ├── __init__.py
│   │   └── coco_client.py  # Snowflake Cortex Code Agent SDK wrapper
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── ops.py          # DevOps logs & performance endpoints
│   │   ├── finance.py      # SaaS billing & ledger endpoints
│   │   └── growth.py       # User CRM & Churn ML endpoints
│   └── utils/
│       ├── __init__.py
│       └── helpers.py
├── data/
│   ├── mock_logs.csv       # Seed data for DevOps logs
│   ├── mock_finance.csv    # Seed data for SaaS transactions
│   └── mock_customers.csv  # Seed data for CRM/Predictive metrics
├── scripts/
│   └── setup_db.py         # Script to spin up Snowflake tables & upload seed data
├── tests/
│   ├── __init__.py
│   ├── test_ops.py
│   ├── test_finance.py
│   └── test_growth.py
├── .gitignore
├── README.md
└── requirements.txt

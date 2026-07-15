from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from app.routers import ops, finance, growth, agent

app = FastAPI(
    title="PaaS Command Center",
    description="Unified DevOps, Finance, and Growth dashboard for the Snowflake CoCo CLI Hackathon",
    version="1.0.0",
)

app.include_router(ops.router)
app.include_router(finance.router)
app.include_router(growth.router)
app.include_router(agent.router)


@app.get("/", response_class=HTMLResponse)
def dashboard():
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PaaS Command Center</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0f1119; color: #e1e4e8; min-height: 100vh; }
        .header { background: linear-gradient(135deg, #1a1f36 0%, #0f1119 100%); border-bottom: 1px solid #2d3748; padding: 2rem; text-align: center; }
        .header h1 { font-size: 2.5rem; background: linear-gradient(90deg, #667eea, #764ba2); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .header p { color: #8b95a5; margin-top: 0.5rem; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 1.5rem; padding: 2rem; max-width: 1400px; margin: 0 auto; }
        .card { background: #1a1f36; border: 1px solid #2d3748; border-radius: 12px; padding: 1.5rem; transition: transform 0.2s, box-shadow 0.2s; }
        .card:hover { transform: translateY(-2px); box-shadow: 0 8px 25px rgba(0,0,0,0.3); }
        .card h2 { font-size: 1.2rem; margin-bottom: 0.75rem; }
        .card p { color: #8b95a5; font-size: 0.9rem; line-height: 1.5; }
        .card .endpoints { margin-top: 1rem; }
        .card .endpoints a { display: block; color: #667eea; text-decoration: none; padding: 0.4rem 0; font-family: monospace; font-size: 0.85rem; }
        .card .endpoints a:hover { color: #764ba2; }
        .ops { border-top: 3px solid #f56565; }
        .fin { border-top: 3px solid #48bb78; }
        .growth { border-top: 3px solid #667eea; }
        .status { text-align: center; padding: 2rem; color: #48bb78; }
        .badge { display: inline-block; background: #48bb78; color: #0f1119; padding: 0.25rem 0.75rem; border-radius: 20px; font-size: 0.75rem; font-weight: 600; }
    </style>
</head>
<body>
    <div class="header">
        <h1>PaaS Command Center</h1>
        <p>Unified DevOps, Finance & Growth Intelligence</p>
        <div style="margin-top: 1rem;"><span class="badge">LIVE</span></div>
    </div>
    <div class="grid">
        <div class="card ops">
            <h2>DevOps Monitoring</h2>
            <p>Real-time service health, error tracking, and outage detection across all endpoints.</p>
            <div class="endpoints">
                <a href="/ops/logs">/ops/logs</a>
                <a href="/ops/errors">/ops/errors</a>
                <a href="/ops/outage-summary">/ops/outage-summary</a>
                <a href="/ops/health-metrics">/ops/health-metrics</a>
            </div>
        </div>
        <div class="card fin">
            <h2>SaaS Financials</h2>
            <p>Cost tracking, vendor analysis, and infrastructure spend anomaly detection.</p>
            <div class="endpoints">
                <a href="/finance/transactions">/finance/transactions</a>
                <a href="/finance/spend-by-category">/finance/spend-by-category</a>
                <a href="/finance/cost-spike">/finance/cost-spike</a>
                <a href="/finance/vendor-breakdown">/finance/vendor-breakdown</a>
            </div>
        </div>
        <div class="card growth">
            <h2>Customer Growth</h2>
            <p>CRM intelligence with churn prediction, segmentation, and revenue-at-risk analysis.</p>
            <div class="endpoints">
                <a href="/growth/customers">/growth/customers</a>
                <a href="/growth/churn-risk">/growth/churn-risk</a>
                <a href="/growth/revenue-at-risk">/growth/revenue-at-risk</a>
                <a href="/growth/segmentation">/growth/segmentation</a>
            </div>
        </div>
    </div>
    <div class="status">
        <p>API Docs: <a href="/docs" style="color:#667eea;">/docs</a> | OpenAPI: <a href="/openapi.json" style="color:#667eea;">/openapi.json</a></p>
    </div>
</body>
</html>"""


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "paas-command-center"}

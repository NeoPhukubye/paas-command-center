from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from app.routers import ops, finance, growth, agent


@asynccontextmanager
async def lifespan(app):
    # Seed database on startup if tables are empty
    try:
        import subprocess, sys
        subprocess.run([sys.executable, "scripts/setup_db.py"], timeout=60)
    except Exception:
        pass
    yield


app = FastAPI(
    title="PaaS Command Center",
    description="Unified DevOps, Finance, and Growth dashboard for the Snowflake CoCo CLI Hackathon",
    version="1.0.0",
    lifespan=lifespan,
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
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0f1119; color: #e1e4e8; min-height: 100vh; }
        .header { background: linear-gradient(135deg, #1a1f36 0%, #0f1119 100%); border-bottom: 1px solid #2d3748; padding: 2rem; text-align: center; }
        .header h1 { font-size: 2.5rem; background: linear-gradient(90deg, #667eea, #764ba2); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .header p { color: #8b95a5; margin-top: 0.5rem; }
        .badge { display: inline-block; background: #48bb78; color: #0f1119; padding: 0.25rem 0.75rem; border-radius: 20px; font-size: 0.75rem; font-weight: 600; }

        /* Chat UI */
        .chat-section { max-width: 900px; margin: 2rem auto; padding: 0 2rem; }
        .chat-box { background: #1a1f36; border: 1px solid #2d3748; border-radius: 12px; overflow: hidden; }
        .chat-messages { min-height: 120px; max-height: 400px; overflow-y: auto; padding: 1.5rem; }
        .chat-messages .msg { margin-bottom: 1rem; padding: 0.75rem 1rem; border-radius: 8px; font-size: 0.9rem; line-height: 1.5; }
        .chat-messages .msg.user { background: #2d3748; margin-left: 2rem; }
        .chat-messages .msg.assistant { background: #1e2a4a; border-left: 3px solid #667eea; margin-right: 2rem; }
        .chat-messages .msg.system { background: #1a2332; color: #8b95a5; text-align: center; font-size: 0.8rem; }
        .chat-input-row { display: flex; border-top: 1px solid #2d3748; }
        .chat-input-row input { flex: 1; background: #0f1119; border: none; color: #e1e4e8; padding: 1rem 1.5rem; font-size: 0.95rem; outline: none; }
        .chat-input-row input::placeholder { color: #4a5568; }
        .chat-input-row button { background: linear-gradient(135deg, #667eea, #764ba2); border: none; color: white; padding: 1rem 1.5rem; cursor: pointer; font-weight: 600; transition: opacity 0.2s; }
        .chat-input-row button:hover { opacity: 0.9; }
        .chat-input-row button:disabled { opacity: 0.5; cursor: not-allowed; }
        .quick-prompts { display: flex; gap: 0.5rem; flex-wrap: wrap; margin-top: 0.75rem; }
        .quick-prompts button { background: #2d3748; border: 1px solid #4a5568; color: #e1e4e8; padding: 0.4rem 0.8rem; border-radius: 20px; font-size: 0.75rem; cursor: pointer; transition: background 0.2s; }
        .quick-prompts button:hover { background: #4a5568; }

        /* Charts */
        .charts-section { max-width: 1400px; margin: 2rem auto; padding: 0 2rem; }
        .charts-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 1.5rem; }
        .chart-card { background: #1a1f36; border: 1px solid #2d3748; border-radius: 12px; padding: 1.5rem; }
        .chart-card h3 { font-size: 1rem; margin-bottom: 1rem; color: #e1e4e8; }
        .chart-card canvas { max-height: 250px; }

        /* Domain cards */
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
        .typing { display: inline-block; } .typing span { animation: blink 1.4s infinite; opacity: 0.2; } .typing span:nth-child(2) { animation-delay: 0.2s; } .typing span:nth-child(3) { animation-delay: 0.4s; }
        @keyframes blink { 20% { opacity: 1; } }
    </style>
</head>
<body>
    <div class="header">
        <h1>PaaS Command Center</h1>
        <p>AI-Native Unified Operations Intelligence &mdash; Powered by Snowflake Cortex</p>
        <div style="margin-top: 1rem;"><span class="badge">LIVE</span></div>
    </div>

    <!-- Interactive Chat -->
    <div class="chat-section">
        <div class="chat-box">
            <div class="chat-messages" id="chat-messages">
                <div class="msg system">Ask anything about your infrastructure, costs, or customers. I correlate across all three domains.</div>
            </div>
            <div class="chat-input-row">
                <input type="text" id="chat-input" placeholder="e.g. What caused the last outage and which customers are at risk?" />
                <button id="chat-send" onclick="sendMessage()">Ask</button>
            </div>
        </div>
        <div class="quick-prompts">
            <button onclick="askQuick('Give me a full incident report')">Full Incident Report</button>
            <button onclick="askQuick('What was the cost impact of the last outage?')">Cost Impact</button>
            <button onclick="askQuick('Which customers are most likely to churn?')">Churn Risk</button>
            <button onclick="askQuick('Show me error rates by endpoint')">Error Rates</button>
            <button onclick="askQuick('What actions should we take right now?')">Recommended Actions</button>
        </div>
    </div>

    <!-- Visualizations -->
    <div class="charts-section">
        <div class="charts-grid">
            <div class="chart-card">
                <h3>Error Rate Timeline (Hourly)</h3>
                <canvas id="errorChart"></canvas>
            </div>
            <div class="chart-card">
                <h3>Infrastructure Cost Spike</h3>
                <canvas id="costChart"></canvas>
            </div>
            <div class="chart-card">
                <h3>Customer Churn Risk Distribution</h3>
                <canvas id="churnChart"></canvas>
            </div>
        </div>
    </div>

    <!-- Domain Cards -->
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
        <p>API Docs: <a href="/docs" style="color:#667eea;">/docs</a> | OpenAPI: <a href="/openapi.json" style="color:#667eea;">/openapi.json</a> | <a href="/agent/incidents" style="color:#667eea;">Detected Incidents</a></p>
    </div>

    <script>
    // Chat functionality
    const chatMessages = document.getElementById('chat-messages');
    const chatInput = document.getElementById('chat-input');
    const chatSend = document.getElementById('chat-send');

    chatInput.addEventListener('keydown', e => { if (e.key === 'Enter') sendMessage(); });

    function addMessage(text, role) {
        const div = document.createElement('div');
        div.className = 'msg ' + role;
        div.innerHTML = text.replace(/\\n/g, '<br>');
        chatMessages.appendChild(div);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return div;
    }

    async function sendMessage() {
        const q = chatInput.value.trim();
        if (!q) return;
        chatInput.value = '';
        addMessage(q, 'user');
        chatSend.disabled = true;
        const typing = addMessage('<span class="typing"><span>.</span><span>.</span><span>.</span></span>', 'assistant');

        try {
            const res = await fetch('/agent/ask', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({question: q})
            });
            const data = await res.json();
            typing.remove();
            let answer = data.response || data.error || JSON.stringify(data);
            if (typeof answer === 'object') answer = JSON.stringify(answer, null, 2);
            const domain = data.domain ? `<span style="color:#667eea;font-size:0.7rem;text-transform:uppercase;">[${data.domain}]</span> ` : '';
            const source = data.source ? `<span style="color:#4a5568;font-size:0.7rem;"> via ${data.source}</span>` : '';
            addMessage(domain + answer + source, 'assistant');
        } catch(e) {
            typing.remove();
            addMessage('Error: ' + e.message, 'assistant');
        }
        chatSend.disabled = false;
        chatInput.focus();
    }

    function askQuick(q) { chatInput.value = q; sendMessage(); }

    // Load charts from API data
    async function loadCharts() {
        try {
            // Error timeline chart
            const healthRes = await fetch('/ops/health-metrics');
            const healthData = await healthRes.json();
            if (healthData.length) {
                const labels = healthData.map(r => r.hour ? new Date(r.hour).toLocaleString('en', {month:'short', day:'numeric', hour:'numeric'}) : '');
                new Chart(document.getElementById('errorChart'), {
                    type: 'line',
                    data: {
                        labels,
                        datasets: [{
                            label: 'Errors',
                            data: healthData.map(r => r.errors),
                            borderColor: '#f56565',
                            backgroundColor: 'rgba(245,101,101,0.1)',
                            fill: true, tension: 0.3
                        }, {
                            label: 'Total Requests',
                            data: healthData.map(r => r.requests),
                            borderColor: '#667eea',
                            backgroundColor: 'rgba(102,126,234,0.05)',
                            fill: true, tension: 0.3
                        }]
                    },
                    options: { responsive: true, plugins: { legend: { labels: { color: '#8b95a5' } } }, scales: { x: { ticks: { color: '#4a5568', maxRotation: 45 } }, y: { ticks: { color: '#4a5568' }, grid: { color: '#2d3748' } } } }
                });
            }

            // Cost spike chart
            const costRes = await fetch('/finance/cost-spike');
            const costData = await costRes.json();
            if (costData.length) {
                const labels = costData.map(r => r.hour ? new Date(r.hour).toLocaleString('en', {month:'short', day:'numeric', hour:'numeric'}) : '');
                new Chart(document.getElementById('costChart'), {
                    type: 'bar',
                    data: {
                        labels,
                        datasets: [{
                            label: 'Infrastructure Cost ($)',
                            data: costData.map(r => r.hourly_cost || r.total_cost || r.amount),
                            backgroundColor: costData.map(r => (r.hourly_cost || r.total_cost || r.amount) > 5000 ? 'rgba(245,101,101,0.7)' : 'rgba(72,187,120,0.7)'),
                            borderColor: costData.map(r => (r.hourly_cost || r.total_cost || r.amount) > 5000 ? '#f56565' : '#48bb78'),
                            borderWidth: 1
                        }]
                    },
                    options: { responsive: true, plugins: { legend: { labels: { color: '#8b95a5' } } }, scales: { x: { ticks: { color: '#4a5568', maxRotation: 45 } }, y: { ticks: { color: '#4a5568' }, grid: { color: '#2d3748' } } } }
                });
            }

            // Churn risk chart
            const churnRes = await fetch('/growth/churn-risk');
            const churnData = await churnRes.json();
            if (churnData.length) {
                const names = churnData.slice(0, 10).map(r => r.name || r.customer_id || 'Customer');
                const scores = churnData.slice(0, 10).map(r => r.churn_risk_score);
                new Chart(document.getElementById('churnChart'), {
                    type: 'bar',
                    data: {
                        labels: names,
                        datasets: [{
                            label: 'Churn Risk Score',
                            data: scores,
                            backgroundColor: scores.map(s => s >= 0.8 ? 'rgba(245,101,101,0.7)' : s >= 0.65 ? 'rgba(237,137,54,0.7)' : 'rgba(72,187,120,0.7)'),
                            borderWidth: 0
                        }]
                    },
                    options: { indexAxis: 'y', responsive: true, plugins: { legend: { labels: { color: '#8b95a5' } } }, scales: { x: { max: 1, ticks: { color: '#4a5568' }, grid: { color: '#2d3748' } }, y: { ticks: { color: '#8b95a5' } } } }
                });
            }
        } catch(e) { console.warn('Charts failed to load:', e); }
    }
    loadCharts();
    </script>
</body>
</html>"""


@app.get("/health")
def health_check():
    from app.config import settings
    has_account = bool(settings.SNOWFLAKE_ACCOUNT)
    has_user = bool(settings.SNOWFLAKE_USER)
    has_auth = bool(settings.SNOWFLAKE_PASSWORD) or bool(settings.SNOWFLAKE_PRIVATE_KEY)
    has_db = bool(settings.SNOWFLAKE_DATABASE)

    db_connected = False
    db_error = None
    if has_account and has_user and has_auth:
        try:
            from app.utils.helpers import get_connection
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT CURRENT_DATABASE(), CURRENT_SCHEMA()")
            row = cur.fetchone()
            db_connected = True
            cur.close()
            conn.close()
        except Exception as e:
            db_error = str(e)

    return {
        "status": "healthy" if db_connected else "degraded",
        "service": "paas-command-center",
        "snowflake": {
            "account_configured": has_account,
            "user_configured": has_user,
            "auth_configured": has_auth,
            "database_configured": has_db,
            "connected": db_connected,
            "error": db_error,
        },
    }

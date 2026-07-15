from fastapi import APIRouter, Query
from app.utils.helpers import query

router = APIRouter(prefix="/ops", tags=["DevOps"])


@router.get("/logs")
def get_logs(endpoint: str = None, status_code: int = None, limit: int = 100):
    sql = "SELECT * FROM devops_logs WHERE 1=1"
    params = []
    if endpoint:
        sql += " AND endpoint = %s"
        params.append(endpoint)
    if status_code:
        sql += " AND status_code = %s"
        params.append(status_code)
    sql += " ORDER BY timestamp DESC LIMIT %s"
    params.append(limit)
    return query(sql, tuple(params))


@router.get("/errors")
def get_errors(limit: int = 50):
    return query(
        "SELECT * FROM devops_logs WHERE status_code >= 500 ORDER BY timestamp DESC LIMIT %s",
        (limit,),
    )


@router.get("/outage-summary")
def outage_summary():
    return query("""
        SELECT
            endpoint,
            COUNT(*) AS total_requests,
            SUM(CASE WHEN status_code >= 500 THEN 1 ELSE 0 END) AS error_count,
            ROUND(SUM(CASE WHEN status_code >= 500 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS error_rate_pct,
            ROUND(AVG(response_time_ms), 0) AS avg_response_ms
        FROM devops_logs
        WHERE timestamp BETWEEN '2025-06-15 14:00:00' AND '2025-06-15 16:00:00'
        GROUP BY endpoint
        ORDER BY error_rate_pct DESC
    """)


@router.get("/health-metrics")
def health_metrics():
    return query("""
        SELECT
            DATE_TRUNC('hour', timestamp) AS hour,
            COUNT(*) AS requests,
            SUM(CASE WHEN status_code >= 500 THEN 1 ELSE 0 END) AS errors,
            ROUND(AVG(response_time_ms), 0) AS avg_response_ms,
            MAX(response_time_ms) AS p_max_response_ms
        FROM devops_logs
        GROUP BY DATE_TRUNC('hour', timestamp)
        ORDER BY hour
    """)

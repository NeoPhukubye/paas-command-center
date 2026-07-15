from fastapi import APIRouter
from app.utils.helpers import query

router = APIRouter(prefix="/finance", tags=["Finance"])


@router.get("/transactions")
def get_transactions(category: str = None, status: str = None, limit: int = 100):
    sql = "SELECT * FROM saas_financials WHERE 1=1"
    params = []
    if category:
        sql += " AND category = %s"
        params.append(category)
    if status:
        sql += " AND status = %s"
        params.append(status)
    sql += " ORDER BY timestamp DESC LIMIT %s"
    params.append(limit)
    return query(sql, tuple(params))


@router.get("/spend-by-category")
def spend_by_category():
    return query("""
        SELECT
            category,
            COUNT(*) AS transaction_count,
            ROUND(SUM(amount), 2) AS total_spend,
            ROUND(AVG(amount), 2) AS avg_amount
        FROM saas_financials
        WHERE status = 'completed'
        GROUP BY category
        ORDER BY total_spend DESC
    """)


@router.get("/cost-spike")
def cost_spike():
    return query("""
        SELECT
            DATE_TRUNC('hour', timestamp) AS hour,
            category,
            ROUND(SUM(amount), 2) AS total_cost,
            COUNT(*) AS txn_count
        FROM saas_financials
        WHERE category = 'Infrastructure'
        GROUP BY DATE_TRUNC('hour', timestamp), category
        ORDER BY total_cost DESC
        LIMIT 20
    """)


@router.get("/vendor-breakdown")
def vendor_breakdown():
    return query("""
        SELECT
            vendor_name,
            COUNT(*) AS transactions,
            ROUND(SUM(amount), 2) AS total_spend,
            ROUND(AVG(amount), 2) AS avg_spend
        FROM saas_financials
        WHERE status = 'completed'
        GROUP BY vendor_name
        ORDER BY total_spend DESC
    """)

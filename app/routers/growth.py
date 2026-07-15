from fastapi import APIRouter
from app.utils.helpers import query

router = APIRouter(prefix="/growth", tags=["Growth"])


@router.get("/customers")
def get_customers(plan_tier: str = None, limit: int = 100):
    sql = "SELECT * FROM customer_crm WHERE 1=1"
    params = []
    if plan_tier:
        sql += " AND plan_tier = %s"
        params.append(plan_tier)
    sql += " ORDER BY lifetime_value DESC LIMIT %s"
    params.append(limit)
    return query(sql, tuple(params))


@router.get("/churn-risk")
def churn_risk(threshold: float = 0.65):
    return query(
        """
        SELECT customer_id, name, email, plan_tier, lifetime_value, churn_risk_score, last_active
        FROM customer_crm
        WHERE churn_risk_score >= %s
        ORDER BY churn_risk_score DESC
        """,
        (threshold,),
    )


@router.get("/revenue-at-risk")
def revenue_at_risk():
    return query("""
        SELECT
            plan_tier,
            COUNT(*) AS at_risk_customers,
            ROUND(SUM(lifetime_value), 2) AS revenue_at_risk,
            ROUND(AVG(churn_risk_score), 3) AS avg_churn_risk
        FROM customer_crm
        WHERE churn_risk_score >= 0.65
        GROUP BY plan_tier
        ORDER BY revenue_at_risk DESC
    """)


@router.get("/segmentation")
def segmentation():
    return query("""
        SELECT
            plan_tier,
            COUNT(*) AS customer_count,
            ROUND(AVG(lifetime_value), 2) AS avg_ltv,
            ROUND(AVG(churn_risk_score), 3) AS avg_churn_risk,
            ROUND(SUM(lifetime_value), 2) AS total_ltv
        FROM customer_crm
        GROUP BY plan_tier
        ORDER BY total_ltv DESC
    """)

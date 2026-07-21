from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Optional
from app.agents.coco_client import (
    classify_intent,
    execute_cortex_query,
    get_incident_summary,
    get_recommended_actions,
    detect_incident_windows,
)

router = APIRouter(prefix="/agent", tags=["AI Agent"])


class QueryRequest(BaseModel):
    question: str
    domain: Optional[str] = None


@router.post("/ask")
def ask_agent(request: QueryRequest):
    return execute_cortex_query(request.question, request.domain)


@router.post("/classify")
def classify(request: QueryRequest):
    domain = classify_intent(request.question)
    return {"question": request.question, "domain": domain}


@router.get("/incident-summary")
def incident_summary(start: Optional[str] = None, end: Optional[str] = None):
    """Cross-domain incident summary. Auto-detects incident window if not specified."""
    return get_incident_summary(start, end)


@router.get("/incidents")
def list_incidents():
    """List all detected incident windows based on anomaly detection."""
    return {"incidents": detect_incident_windows()}


@router.get("/recommended-actions")
def recommended_actions():
    return get_recommended_actions()


@router.get("/correlate")
def correlate(
    start: str = Query(..., description="Start of time window (YYYY-MM-DD HH:MM:SS)"),
    end: str = Query(..., description="End of time window (YYYY-MM-DD HH:MM:SS)"),
):
    """Correlate DevOps errors, financial impact, and customer risk for any time window."""
    return get_incident_summary(start, end)

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.agents.coco_client import (
    classify_intent,
    execute_cortex_query,
    get_incident_summary,
    get_recommended_actions,
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
def incident_summary():
    return get_incident_summary()


@router.get("/recommended-actions")
def recommended_actions():
    return get_recommended_actions()

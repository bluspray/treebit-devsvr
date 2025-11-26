from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI
from pydantic import BaseModel, Field


class LogEvent(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    host: str
    service: str
    level: str
    message: str


class PredictionResult(BaseModel):
    risk_score: float = Field(ge=0, le=1)
    label: str
    notes: Optional[str] = None


app = FastAPI(title="Treebit Predictive Ops API", version="0.1.0")


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok"}


def basic_score(events: List[LogEvent]) -> float:
    if not events:
        return 0.0
    weighted = sum(1.0 for event in events if event.level.lower() in {"error", "critical", "fatal"})
    return min(0.1 * len(events) + 0.2 * weighted, 1.0)


@app.post("/predict", response_model=PredictionResult)
def predict(events: List[LogEvent]) -> PredictionResult:
    score = basic_score(events)
    label = "normal" if score < 0.5 else "degraded"
    notes = "stub scoring; replace with real model and features"
    return PredictionResult(risk_score=score, label=label, notes=notes)

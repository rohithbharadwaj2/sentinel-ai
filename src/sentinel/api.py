from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from sentinel.models import AnalysisResult, Evidence, Incident
from sentinel.orchestrator import IncidentOrchestrator
from sentinel.retrieval import EvidenceStore

app = FastAPI(
    title="Sentinel AI",
    version="0.1.0",
    description="Evidence-grounded incident intelligence and recovery API",
)
store = EvidenceStore()


class EvidenceBatch(BaseModel):
    evidence: list[Evidence]


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": "0.1.0"}


@app.post("/evidence", response_model=list[Evidence])
def ingest_evidence(batch: EvidenceBatch) -> list[Evidence]:
    return store.add_many(batch.evidence)


@app.get("/evidence/{evidence_id}", response_model=Evidence)
def get_evidence(evidence_id: str) -> Evidence:
    evidence = store.get(evidence_id)
    if evidence is None:
        raise HTTPException(status_code=404, detail="Evidence not found")
    return evidence


@app.post("/analyze", response_model=AnalysisResult)
def analyze_incident(incident: Incident) -> AnalysisResult:
    return IncidentOrchestrator(store).analyze(incident)

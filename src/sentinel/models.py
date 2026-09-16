from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field


class EvidenceKind(str, Enum):
    LOG = "log"
    CODE = "code"
    DOCUMENT = "document"
    METRIC = "metric"
    TRACE = "trace"
    IMAGE = "image"
    DEPLOYMENT = "deployment"


class Evidence(BaseModel):
    id: str = Field(default_factory=lambda: f"ev_{uuid4().hex[:10]}")
    kind: EvidenceKind
    source: str
    content: str
    metadata: dict[str, str | int | float | bool] = Field(default_factory=dict)
    observed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Incident(BaseModel):
    id: str = Field(default_factory=lambda: f"inc_{uuid4().hex[:10]}")
    title: str
    description: str
    service: str
    severity: str = "unknown"
    symptoms: list[str] = Field(default_factory=list)


class Finding(BaseModel):
    agent: str
    statement: str
    evidence_ids: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)


class Diagnosis(BaseModel):
    summary: str
    findings: list[Finding]
    evidence_ids: list[str]
    confidence: float = Field(ge=0.0, le=1.0)


class RemediationStep(BaseModel):
    action: str
    rationale: str
    evidence_ids: list[str] = Field(default_factory=list)
    requires_human_approval: bool = True


class AnalysisResult(BaseModel):
    incident: Incident
    diagnosis: Diagnosis
    remediation: list[RemediationStep]

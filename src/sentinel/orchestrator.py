from __future__ import annotations

from sentinel.agents.core import CodeAgent, LogAgent, RetrievalAgent, TriageAgent, RemediationAgent
from sentinel.models import AnalysisResult, Diagnosis, Finding, Incident
from sentinel.retrieval import EvidenceStore


class IncidentOrchestrator:
    def __init__(self, store: EvidenceStore) -> None:
        self.store = store
        self.agents = [TriageAgent(), LogAgent(), CodeAgent(), RetrievalAgent()]
        self.remediation_agent = RemediationAgent()

    def analyze(self, incident: Incident) -> AnalysisResult:
        findings: list[Finding] = []
        for agent in self.agents:
            findings.extend(agent.analyze(incident, self.store))

        evidence_ids = sorted({eid for finding in findings for eid in finding.evidence_ids})
        confidence = (
            round(sum(f.confidence for f in findings) / len(findings), 2)
            if findings
            else 0.0
        )
        summary = (
            f"Sentinel produced {len(findings)} evidence-backed findings across "
            f"{len({f.agent for f in findings})} analysis agents."
            if findings
            else "Sentinel could not produce an evidence-backed diagnosis."
        )
        diagnosis = Diagnosis(
            summary=summary,
            findings=findings,
            evidence_ids=evidence_ids,
            confidence=confidence,
        )
        return AnalysisResult(
            incident=incident,
            diagnosis=diagnosis,
            remediation=self.remediation_agent.propose(findings),
        )

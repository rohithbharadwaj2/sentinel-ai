from __future__ import annotations

from abc import ABC, abstractmethod

from sentinel.models import EvidenceKind, Finding, Incident, RemediationStep
from sentinel.retrieval import EvidenceStore


class Agent(ABC):
    name: str

    @abstractmethod
    def analyze(self, incident: Incident, store: EvidenceStore) -> list[Finding]: ...


class TriageAgent(Agent):
    name = "triage"

    def analyze(self, incident: Incident, store: EvidenceStore) -> list[Finding]:
        query = " ".join([incident.service, incident.title, *incident.symptoms])
        evidence = store.search(query, limit=3)
        if not evidence:
            return []
        return [Finding(
            agent=self.name,
            statement=f"Relevant evidence exists for {incident.service} and the reported symptoms.",
            evidence_ids=[item.id for item in evidence],
            confidence=min(0.85, 0.55 + 0.1 * len(evidence)),
        )]


class LogAgent(Agent):
    name = "logs"
    SIGNALS = ("timeout", "error", "exception", "failed", "exhausted", "latency")

    def analyze(self, incident: Incident, store: EvidenceStore) -> list[Finding]:
        findings: list[Finding] = []
        for item in store.all():
            if item.kind != EvidenceKind.LOG:
                continue
            matches = [signal for signal in self.SIGNALS if signal in item.content.lower()]
            if matches:
                findings.append(Finding(
                    agent=self.name,
                    statement=f"Log signal detected: {', '.join(matches)}.",
                    evidence_ids=[item.id],
                    confidence=min(0.9, 0.55 + 0.08 * len(matches)),
                ))
        return findings


class CodeAgent(Agent):
    name = "code"

    def analyze(self, incident: Incident, store: EvidenceStore) -> list[Finding]:
        findings: list[Finding] = []
        for item in store.all():
            if item.kind not in {EvidenceKind.CODE, EvidenceKind.DEPLOYMENT}:
                continue
            text = item.content.lower()
            if any(word in text for word in ("pool", "timeout", "retry", "connection", "limit")):
                findings.append(Finding(
                    agent=self.name,
                    statement="A configuration or code change touches a resource/timeout control relevant to the incident.",
                    evidence_ids=[item.id],
                    confidence=0.76,
                ))
        return findings


class RetrievalAgent(Agent):
    name = "retrieval"

    def analyze(self, incident: Incident, store: EvidenceStore) -> list[Finding]:
        query = f"{incident.title} {incident.description} {' '.join(incident.symptoms)}"
        evidence = store.search(query, limit=5)
        if not evidence:
            return []
        return [Finding(
            agent=self.name,
            statement="Retrieved evidence shares terms with the incident description and symptoms.",
            evidence_ids=[item.id for item in evidence],
            confidence=0.65,
        )]


class RemediationAgent:
    name = "remediation"

    def propose(self, findings: list[Finding]) -> list[RemediationStep]:
        evidence_ids = sorted({eid for finding in findings for eid in finding.evidence_ids})
        if not evidence_ids:
            return [RemediationStep(
                action="Collect additional evidence before changing the system.",
                rationale="No supported finding has enough provenance to justify remediation.",
            )]
        return [
            RemediationStep(
                action="Compare the suspect deployment/configuration with the last known-good revision.",
                rationale="The analysis links incident signals with deployment or code evidence.",
                evidence_ids=evidence_ids,
            ),
            RemediationStep(
                action="Validate the smallest candidate change in an isolated test environment.",
                rationale="Sentinel should prove a remediation before any production or repository mutation.",
                evidence_ids=evidence_ids,
            ),
        ]

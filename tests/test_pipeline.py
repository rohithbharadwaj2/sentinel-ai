from sentinel.demo import build_demo
from sentinel.orchestrator import IncidentOrchestrator


def test_demo_produces_cited_findings() -> None:
    incident, store = build_demo()
    result = IncidentOrchestrator(store).analyze(incident)

    assert result.diagnosis.findings
    assert "ev_log_pool_timeout" in result.diagnosis.evidence_ids
    assert "ev_deploy_pool_change" in result.diagnosis.evidence_ids
    assert all(finding.evidence_ids for finding in result.diagnosis.findings)
    assert all(step.requires_human_approval for step in result.remediation)


def test_retrieval_returns_relevant_evidence() -> None:
    _, store = build_demo()
    matches = store.search("database pool timeout")
    ids = {item.id for item in matches}

    assert "ev_log_pool_timeout" in ids
    assert "ev_runbook" in ids

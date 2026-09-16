# Sentinel AI

### Evidence-grounded incident intelligence and recovery

Sentinel is an engineering project for investigating software incidents across heterogeneous operational evidence. The goal is to move beyond a generic incident chatbot: Sentinel builds a traceable evidence graph, delegates analysis to specialized agents, produces a cited diagnosis, and prepares remediation that can later be validated in an isolated sandbox.

> **Current status:** v0.1 foundation. The repository currently implements a deterministic, locally runnable incident-analysis pipeline. LLM, vector database, multimodal, GitHub patching, sandbox execution, and cloud integrations are intentionally tracked as subsequent milestones rather than claimed as completed features.

**Python · FastAPI · Pydantic · Agent Orchestration · Retrieval · Docker · GitHub Actions**

## Why Sentinel

A production incident rarely lives in one source. The useful clues may be split between application logs, deployment metadata, source code, runbooks, traces, metrics, and screenshots. Sentinel models those artifacts as first-class evidence and keeps the evidence attached to every conclusion.

```text
Incident
   │
   ▼
Triage Agent ──────────────┐
   │                       │
   ├──► Log Agent          │
   ├──► Code Agent         ├──► Evidence Store
   └──► Retrieval Agent    │       │
                           │       ▼
                           └──► Orchestrator
                                   │
                          cited diagnosis
                                   │
                                   ▼
                          Remediation Agent
                                   │
                           proposed actions
                                   │
                     [sandbox validation: next]
```

## v0.1 capabilities

- Typed incident, evidence, finding, diagnosis, and remediation models.
- In-memory evidence store with lexical retrieval and stable evidence IDs.
- Specialized triage, log, code, retrieval, and remediation agents.
- Orchestrator that merges agent findings without dropping provenance.
- FastAPI endpoints for health checks, evidence ingestion, and incident analysis.
- Deterministic checkout-latency demo fixture for reproducible development.
- Unit tests, Docker packaging, and GitHub Actions CI.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
uvicorn sentinel.api:app --reload
```

Then run the deterministic demo:

```bash
python -m sentinel.demo
```

API docs are available locally at `/docs` after the server starts.

## Example incident

The included fixture represents a checkout service whose p95 latency increases after a deployment. Logs contain a database-pool timeout and the deployment note mentions a pool-size configuration change. Sentinel retrieves both pieces of evidence, keeps their IDs in the resulting findings, and generates a remediation plan from the evidence instead of inventing an unsupported root cause.

## Repository structure

```text
sentinel-ai/
├── src/sentinel/
│   ├── agents/          # specialized analysis agents
│   ├── api.py           # FastAPI application
│   ├── demo.py          # reproducible local scenario
│   ├── models.py        # typed domain contracts
│   ├── orchestrator.py  # analysis workflow
│   └── retrieval.py     # evidence store + retrieval
├── tests/
├── docs/
│   └── ARCHITECTURE.md
├── .github/workflows/
│   └── ci.yml
├── Dockerfile
├── pyproject.toml
└── README.md
```

## Roadmap

| Milestone | Engineering goal | Status |
|---|---|---|
| v0.1 | typed evidence pipeline + deterministic agents + API + CI | **in progress** |
| v0.2 | embeddings, chunking, vector retrieval, retrieval evaluation | planned |
| v0.3 | LLM-backed structured agents with citation/faithfulness checks | planned |
| v0.4 | GitHub source ingestion + code-aware diagnosis | planned |
| v0.5 | OpenTelemetry traces + metrics ingestion | planned |
| v0.6 | screenshot/dashboard understanding | planned |
| v0.7 | Docker sandbox, patch generation, test validation | planned |
| v0.8 | PR generation + human approval boundary | planned |
| v0.9 | AWS deployment + observability + evaluation dashboard | planned |

## Design principles

**Evidence before confidence.** A diagnosis must point back to concrete evidence IDs.

**Deterministic core before LLM orchestration.** The pipeline should be testable before probabilistic components are introduced.

**Human approval before mutation.** Future remediation agents may propose patches, but repository or production changes should remain behind explicit approval and validation boundaries.

**Evaluation is a product feature.** Retrieval recall, citation correctness, diagnosis faithfulness, patch test pass rate, latency, and cost will be measured as the system grows.

## License

No license is asserted yet while the project architecture is evolving.

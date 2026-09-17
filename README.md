# UtiliCare Help Desk Triage Agent

UtiliCare is a bounded AI-assisted help-desk triage prototype for electricity and water service requests. A human help-desk agent remains responsible for ticket submission, routing, escalation, closure, billing changes, and infrastructure actions.

## Current project stage

Weeks 1 and 2 are complete. Week 3 adds a controlled retrieval-augmented generation (RAG) baseline: corpus validation, metadata-preserving chunking, deterministic retrieval, source-grounded context, and retrieval traces. The final evaluation trace must be generated locally before reporting results.

## Repository structure

```text
docs/
  requirements/       Week 1 charter, stories, boundary matrix; Week 2 model note
  architecture/       System and RAG diagrams
  weekly-reports/     One factual progress report per week
  evaluation/         Evaluation methods, datasets, and analysis documents
prompts/              Versioned prompt specifications and change history
knowledge/            Controlled corpus and source/provenance register
src/                  Application source code only
tests/                Executable tests and evaluation input cases only
evidence/
  traces/             Generated evaluation and runtime traces
  screenshots/        Demonstration screenshots
  demo/               Demonstration assets
```

Do not put generated results in `tests/`, source code in `docs/`, or secrets in the repository. Place each new item in the folder that owns its purpose.

## Week 1 and Week 2 evidence

| Week | Required evidence | Location |
| --- | --- | --- |
| 1 | Project charter, user stories, AI boundary matrix | `docs/requirements/` |
| 1 | Initial architecture diagram | `docs/architecture/Architectural_Diagram.docx` |
| 1–2 | Progress reports | `docs/weekly-reports/` |
| 2 | Model selection note | `docs/requirements/Model_Selection_Note.docx` |
| 2 | Prompt specification and version history | `prompts/` |
| 2 | Ten prompt-evaluation cases and results | `tests/test_cases.json`, `evidence/traces/week2_eval_results.csv` |
| 3 preparation | Controlled corpus and provenance register | `knowledge/corpus/`, `knowledge/source_register.csv` |

## Run the Week 2 baseline

1. Create and activate a Python virtual environment.
2. Install dependencies with `pip install -r requirements.txt`.
3. Copy `.env.example` to `.env` and supply `GEMINI_API_KEY`. Never commit `.env`.
4. Start the API with `uvicorn src.main:app --reload`.
5. Send `POST /triage` with `{"message":"My bill is too high"}`.

Run `python -m tests.run_eval` for the Week 2 prompt evaluation. It writes a timestamped result file to `evidence/traces/`; API or quota errors are recorded as failures and must not be reported as model classifications. Run `python -m tests.run_rag_eval` for the offline Week 3 retrieval evaluation.

## Week 3 placement rules

Place the RAG implementation in `src/`, controlled source files in `knowledge/corpus/`, provenance in `knowledge/source_register.csv`, RAG questions in `tests/`, result traces in `evidence/traces/`, the RAG diagram in `docs/architecture/`, and the evaluation analysis plus Week 3 report in `docs/evaluation/` and `docs/weekly-reports/` respectively.

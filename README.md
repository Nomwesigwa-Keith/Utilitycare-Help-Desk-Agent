# UtiliCare Help Desk Triage Agent

UtiliCare is a bounded AI-assisted help-desk triage prototype for electricity and water service requests. A human help-desk agent remains responsible for ticket submission, routing, escalation, closure, billing changes, and infrastructure actions.

## Current Project Stage

**Week 8 - Final Release** (October 2026)

This is the final release of the UtiliCare Help Desk Triage Agent, completing the 8-week capstone project for BSE4104 Emerging Trends in Software Engineering. The system implements:

- **Week 1-2**: Foundation model integration with structured classification
- **Week 3**: Retrieval-augmented generation (RAG) with controlled corpus
- **Week 4**: Tool function calling with authorization boundaries
- **Week 5**: Bounded agent workflow with iteration limits and stop conditions
- **Week 6**: Working memory for case history with strict isolation
- **Week 7**: Comprehensive evaluation (37 scenarios), observability/tracing, guardrails, and failure remediation

## Repository Structure

```text
docs/
  requirements/       Project charter, user stories, AI boundary matrix, model note,
                      tool catalogue, agent task contract, state model, memory design,
                      MCP interface specification
  architecture/       System architecture diagrams
  weekly-reports/     Weekly progress reports (Weeks 1-7)
  evaluation/         Evaluation methods, datasets, failure catalogue, and analysis
prompts/              Versioned prompt specifications and change history
knowledge/
  corpus/             Controlled knowledge base (30 documents)
  source_register.csv Corpus provenance and metadata
src/                  Application source code
  agent.py            Foundation model integration and parsing
  bounded_agent.py    Bounded workflow with iteration limits
  main.py             HTTP API endpoint
  memory.py           Working memory for case history
  orchestrator.py      Tool execution and validation
  rag.py              Retrieval-augmented generation
  tools.py            Tool implementations (get_outage_status, draft_ticket)
tests/                Executable tests and evaluation scenarios
evidence/
  traces/             Evaluation and runtime traces
  screenshots/        Demonstration screenshots
  demo/               Demonstration assets
data/                 Runtime data (gitignored)
  case_memory.json    Working memory storage
```

**Important**: The `data/` directory and `.env` file are gitignored. Never commit secrets or runtime data.

## Quick Start

### Prerequisites

- Python 3.10 or higher
- pip package manager
- A Google Gemini API key (free tier available)
- For pytest-based checks, install pytest separately: `python -m pip install pytest`

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Nomwesigwa-Keith/Utilitycare-Help-Desk-Agent.git
   cd Utilitycare-Help-Desk-Agent
   ```

2. **Create a Python virtual environment:**
   ```bash
   python -m venv venv
   # On Windows PowerShell:
   .\venv\Scripts\Activate.ps1
   # On Windows Command Prompt:
   venv\Scripts\activate.bat
   # On Linux/Mac:
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables** (PowerShell):
   ```bash
   Copy-Item .env.example .env
   # Edit .env and add your GEMINI_API_KEY
   ```
   On macOS/Linux, use `cp .env.example .env` instead. Keep the populated `.env` file private.

5. **Run the API & Decoupled Web Applications:**
   ```bash
   uvicorn src.main:app --reload
   ```

   Once running, access the decoupled web portals directly in your browser:
   - **Customer Help-Desk Portal (Public Chat):** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
   - **Supervisor Operations Console (Approval Cockpit):** [http://127.0.0.1:8000/supervisor](http://127.0.0.1:8000/supervisor)

6. **Test the HTTP Endpoint directly:**
   ```bash
   curl -X POST http://127.0.0.1:8000/triage \
       -H "Content-Type: application/json" \
       -d '{"message": "My power has been out since last night in Ntinda."}'
   ```

### Running the Bounded Agent Directly

For testing without the HTTP API:

```bash
python -m src.bounded_agent
```

This runs a smoke test with a sample message and prints the full state including the execution trace.

### Running Test & Evaluation Suites

**1. Automated Unit Test Suite (pytest):**
```bash
python -m pytest
```
Runs 13/13 passing contract, tool, bounded agent, and working memory tests.

**2. 37-Scenario Deterministic Extended Benchmark:**
```bash
python -m tests.run_extended_eval
```
Covers normal, edge, incorrect-information, adversarial, tool-failure, and unauthorized-action cases. Results written to `evidence/traces/`.

**Tool Authorization Tests:**
```bash
python -m tests.test_failure_authorization
```
Tests boundary conditions and unauthorized action prevention.

**Working Memory Tests** (after installing pytest as noted above):
```bash
python -m pytest tests/test_week6_working_memory.py
```
Verifies memory persistence and decision isolation.

## Capstone Deliverables & Task Assignment (Week 8)

The Week 8 final release represents coordinated engineering across all team members, structured according to our official project brief:

| Deliverable | Requirements | Assignee / Member | Primary Evidence & Location |
| :--- | :--- | :--- | :--- |
| **Final tagged release and README/run instructions** | Fix critical defects, document known limitations, tag a release, and make it runnable from a clean clone | **Umar** (Mubiru Umar) | Git tag `v1.0.0`; clean-clone instructions in `README.md`; `src/main.py` fixes. |
| **Final engineering report (8-12 pages, excluding appendices)** | Ten sections from the brief's template, plus references and appendices | **Everyone** (All 5 Team Members) | [`docs/UtiliCare_Final_Engineering_Report.docx`](docs/UtiliCare_Final_Engineering_Report.docx) |
| **Final evaluation/evidence pack** | Evaluation results, traces, the Failure Catalogue, and screenshots | **Lilian** (Nankunda Lilian) | [`evidence/FINAL_EVALUATION_REPORT.md`](evidence/FINAL_EVALUATION_REPORT.md); `evidence/traces/`; Failure Catalogue. |
| **Presentation deck and live demonstration** | 12-15 minutes, built around a real demo | **Arok & Khot** (Arok John Mayen & Khot Adet Majuong) | [`docs/presentation/UtiliCare_Final_Presentation_Deck.pptx`](docs/presentation/UtiliCare_Final_Presentation_Deck.pptx); [`FINAL_PRESENTATION_DECK.md`](docs/presentation/FINAL_PRESENTATION_DECK.md); decoupled Web UI. |
| **Completed ClickUp board and repository evidence** | Tasks closed and linked to PRs and commits | **Keith** (Nomwesigwa Keith) | ClickUp Sprint Board; merge commit `5917465`; PR management. |

## Project Evidence Directory

| Week | Deliverable | Location |
|------|-------------|----------|
| 1 | Project charter, user stories, AI boundary matrix | `docs/requirements/` |
| 1 | Initial architecture diagram | `docs/architecture/` |
| 1-8 | Weekly progress reports (Weeks 1 to 8) | `docs/weekly-reports/` |
| 2 | Model selection note | `docs/requirements/Model_Selection_Note.docx` |
| 2 | Prompt specification and version history | `prompts/` |
| 3 | RAG evaluation and failure catalogue | `docs/evaluation/Week3_RAG_Evaluation_and_Failure_Catalogue.md` |
| 4 | Tool authorization test evidence | `docs/evaluation/Week4_Failure_Authorization_Test_Evidence.md` |
| 5 | Agent task contract | `docs/requirements/Agent_Task_Contract for week 5.docx` |
| 5 | Execution trace evidence | `docs/evaluation/Week5_Execution_Trace_Evidence.md` |
| 6 | State model | `docs/requirements/Week6_Workflow_State_Model.docx` |
| 6 | Memory design and data handling | `docs/requirements/Memory_Design_and_Data_Handling_Note.docx` |
| 6 | Working memory evidence | `docs/evaluation/Week6_Working_Memory_Evidence.md` |
| 7 | 37-scenario evaluation benchmark | `docs/evaluation/Week 7_37scenario_evaluation.md` |
| 7 | Observability/tracing evidence | `docs/evaluation/Week7_Observability_Tracing_Evidence.md` |
| 7 | Guardrail evidence | `evidence/week7_guardrail_evidence.md` |
| 7 | Failure catalogue & remediation | `docs/evaluation/Failure_Catalogue_and_Remediation_Evidence.md` |
| 8 | Final Engineering Report (10 Sections) | `docs/UtiliCare_Final_Engineering_Report.docx` |
| 8 | Final Evaluation & Evidence Pack | `evidence/FINAL_EVALUATION_REPORT.md` |
| 8 | Presentation Deck & Live Demo Script | `docs/presentation/` |
| 8 | Week 8 Progress Report | `docs/weekly-reports/Week8_Progress_Report.docx` |

## Known Limitations

### API Stability
- The system uses the deprecated `google-generativeai` Python SDK and the configurable `models/gemini-flash-latest` alias. Provider SDK and model behavior may change; migrate to the supported SDK and pin a model before production use.

### Rate Limiting
- The free tier of Gemini API has rate limits. The client waits 2 seconds between model calls and retries selected transient errors, but this does not guarantee quota availability.
- Under high load, you may encounter 429 (quota exceeded) or 503 (service unavailable) errors.

### Memory Storage
- Working memory is stored locally in `data/case_memory.json` and is not backed up.
- Records expire after 30 days and are capped at 100 entries.
- Memory is advisory only for human operators and does not influence model decisions.

### Model Truncation
- In rare cases, the model may hit token limits and truncate responses. The system handles this gracefully by recording `model_parsing_failure` and stopping safely.

### Error Handling
- The system handles errors at multiple levels (HTTP, orchestrator, bounded agent) but certain edge cases may still cause unexpected behavior.
- Error details appear in returned traces where available; this prototype does not provide centralized or durable logging.

## Failure Remediation

Six critical failures were identified and remediated during Week 7:

| Failure ID | Description | Status |
|------------|-------------|--------|
| FC-02 | Tool area code whitespace & casing mismatch | ✅ Fixed |
| FC-04 | Unauthorized ticket status bypass | ✅ Fixed |
| FC-05 | Model JSON truncation & parse failure | ✅ Fixed |
| FC-07 | Working memory context leakage into LLM | ✅ Fixed |
| FC-08 | Unbounded agent loop on ambiguous inputs | ✅ Fixed |
| FC-10 | Empty/whitespace-only request crashing pipeline | ✅ Fixed |

The failure catalogue records the evidence for these remediations. Re-run the offline evaluation and relevant checks on the release commit; results depend on the local Python environment. See `docs/evaluation/Failure_Catalogue_and_Remediation_Evidence.md` for details.

## System Architecture

The agent follows a bounded workflow:

1. **Sense**: Retrieve customer message and knowledge base context via RAG
2. **Plan**: Classify issue and determine if tools are needed
3. **Act**: Execute approved tools (get_outage_status, draft_ticket)
4. **Observe**: Analyze tool results and determine next action
5. **Stop/Re-plan**: Stop on success, failure, or iteration limit (max 3)

Key safety boundaries:
- Maximum 3 iterations per request
- Tool allow-list (only get_outage_status and draft_ticket)
- Human approval required for ticket submission
- No autonomous infrastructure control
- No billing or financial decisions
- Memory context never influences model decisions

## License

This is an academic project for BSE4104 Emerging Trends in Software Engineering at Makerere University.

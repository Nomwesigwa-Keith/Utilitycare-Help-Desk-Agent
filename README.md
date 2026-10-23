# UtiliCare Help Desk Triage Agent

UtiliCare is a bounded AI-assisted help-desk triage prototype for electricity and water service requests. It classifies customer messages, grounds responses in a controlled knowledge base, can call a small allow-listed set of tools, and returns results for human review.

The system is intentionally designed with a human-in-the-loop boundary: an AI response does not submit, route, close, escalate, waive, or otherwise finalize a customer case automatically.

- **Course:** BSE4104 Emerging Trends in Software Engineering, Makerere University
- **Release:** Week 8 final release
- **Repository:** [Nomwesigwa-Keith/Utilitycare-Help-Desk-Agent](https://github.com/Nomwesigwa-Keith/Utilitycare-Help-Desk-Agent)
- **Team:** Group B — Nomwesigwa Keith, Mubiru Umar, Khot Adet Majuong, Nankunda Lilian, and Arok John Mayen

## Features

- Structured customer-message classification using Google Gemini.
- Retrieval-augmented generation (RAG) over a controlled 30-document corpus.
- Bounded agent execution with a maximum of three iterations.
- Two explicitly allow-listed tools:
  - `get_outage_status` — read-only outage lookup using simulated data.
  - `draft_ticket` — creates a draft that remains pending human approval.
- Working memory for case history with case isolation.
- Customer Help-Desk Portal and Supervisor Operations Console.
- Execution traces, telemetry, guardrails, and deterministic evaluation scenarios.
- Explicit refusal of unsupported or unauthorized actions, including billing changes and infrastructure control.

## How a request is handled

1. The API receives a free-text customer message.
2. The RAG layer retrieves relevant guidance from the controlled knowledge base.
3. The model classifies the request and produces structured guidance.
4. The bounded workflow decides whether an approved tool is needed.
5. Tool arguments and results are validated before they are used.
6. The workflow stops on a completed response, clarification, failure, or the iteration limit.
7. The result is returned to the customer portal and/or supervisor console for human review.

## Scope and limitations

- The outage data is mocked and is not a live utility feed.
- Ticket drafting is local and simulated; it does not connect to a production ticketing system.
- Retrieval uses lexical token overlap rather than a vector database or semantic embeddings.
- The deterministic benchmark evaluates repeatable application behavior; it is not a measure of live model quality.
- A valid Gemini API key is required for live model calls.
- The application is a prototype and must not be used to make unsupervised operational, financial, or infrastructure decisions.

## Repository structure

```text
docs/
  requirements/       Project charter, user stories, AI boundary matrix, model note,
                      tool catalogue, agent contract, state model, and memory design
  architecture/       System architecture diagrams
  weekly-reports/     Weekly progress reports
  evaluation/         Evaluation methods, datasets, failure catalogue, and analysis
  presentation/       Final presentation deck and supporting material
  Final_Engineering_Report.pdf
prompts/              Versioned prompt specification and change history
knowledge/
  corpus/             Controlled knowledge base documents (KB-001 to KB-030)
  source_register.csv Corpus provenance and metadata
src/
  agent.py            Gemini integration, prompting, parsing, and validation
  bounded_agent.py    Bounded workflow, state, limits, and execution traces
  main.py             FastAPI application and HTTP routes
  memory.py           Working-memory persistence and case isolation
  orchestrator.py     Tool allow-list, argument validation, and execution
  rag.py              Corpus loading, validation, chunking, and retrieval
  tools.py             Simulated outage lookup and ticket-draft tools
  static/             Customer and supervisor web interfaces
tests/
  Unit tests, contract tests, evaluation runners, and scenario data
evidence/
  traces/             Evaluation and runtime traces
  screenshots/        Demonstration screenshots
  demo/               Demonstration assets
data/                 Runtime data (gitignored)
```

The `.env` file and `data/` directory are intentionally excluded from version control. Never commit API keys, case-memory data, or other secrets.

## Quick start

### Prerequisites

- Python 3.10 or newer
- `pip`
- A Google Gemini API key for live model calls

### Windows PowerShell

```powershell
git clone https://github.com/Nomwesigwa-Keith/Utilitycare-Help-Desk-Agent.git
cd Utilitycare-Help-Desk-Agent

python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1

python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Open `.env` and set a real `GEMINI_API_KEY`:

```env
GEMINI_API_KEY=your-gemini-api-key
UTILICARE_MODEL=models/gemini-flash-latest
```

Start the application:

```powershell
python -m uvicorn src.main:app --reload
```

### macOS or Linux

```bash
git clone https://github.com/Nomwesigwa-Keith/Utilitycare-Help-Desk-Agent.git
cd Utilitycare-Help-Desk-Agent

python3 -m venv .venv
source .venv/bin/activate

python -m pip install -r requirements.txt
cp .env.example .env
```

Set `GEMINI_API_KEY` in `.env`, then start the application:

```bash
python -m uvicorn src.main:app --reload
```

## Demo portals

With the server running, open:

| Portal | URL | Purpose |
|---|---|---|
| Customer Help-Desk Portal | [http://127.0.0.1:8000/](http://127.0.0.1:8000/) | Submit and review customer triage requests |
| Supervisor Operations Console | [http://127.0.0.1:8000/supervisor](http://127.0.0.1:8000/supervisor) | Review draft tickets, approve dispatch, and inspect telemetry |
| Health check | [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health) | Confirm that the API is running |
| Interactive API documentation | [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) | Explore the OpenAPI endpoints |

Suggested demonstration scenarios:

1. **Ntinda power outage** — demonstrates RAG grounding and the read-only outage tool.
2. **Kololo water burst** — demonstrates ticket drafting and human approval.
3. **Bill waiver injection** — demonstrates prompt-injection defense and authorization boundaries.
4. **High water bill dispute** — demonstrates grounded guidance without a side-effecting tool.
5. **Ambiguous request** — demonstrates clarification handling.

## API examples

### PowerShell

```powershell
Invoke-RestMethod `
  -Uri http://127.0.0.1:8000/triage `
  -Method Post `
  -ContentType "application/json" `
  -Body '{"message":"My power has been out since last night in Ntinda.","demo_mode":true}'
```

### macOS/Linux

```bash
curl -X POST http://127.0.0.1:8000/triage \
  -H "Content-Type: application/json" \
  -d '{"message":"My power has been out since last night in Ntinda.","demo_mode":true}'
```

Useful read-only routes include:

```text
GET  /health
GET  /api/scenarios
GET  /api/eval-summary
GET  /api/tickets/pending
GET  /api/telemetry/latest
```

## Running the agent without the API

Run the bounded-agent smoke test directly:

```bash
python -m src.bounded_agent
```

It prints the resulting state and execution trace for a sample request.

## Tests and evaluations

Install the test runner if it is not already available:

```bash
python -m pip install pytest
```

Run the automated test suite:

```bash
python -m pytest
```

Run the working-memory tests:

```bash
python -m pytest tests/test_week6_working_memory.py
```

Run the deterministic 37-scenario benchmark:

```bash
python -m tests.run_extended_eval
```

Run the tool-authorization tests:

```bash
python -m tests.test_failure_authorization
```

Run the RAG evaluation:

```bash
python -m tests.run_rag_eval
```

Evaluation output and execution traces are written under `evidence/traces/`.

## Safety boundaries

- Maximum of **three agent iterations** per request.
- Only `get_outage_status` and `draft_ticket` are allow-listed.
- Ticket drafts remain `pending_approval` until a human supervisor acts.
- No billing, payment, financial-waiver, infrastructure-control, or automatic-closure tools are available.
- Model output is untrusted and must pass schema and authorization validation.
- Insufficient evidence is reported explicitly rather than being filled from model memory.
- Working memory is advisory and isolated by case; it is not used as an unrestricted model knowledge source.

## Configuration

| Variable | Purpose | Default |
|---|---|---|
| `GEMINI_API_KEY` | Google Gemini API credential | None; required for live calls |
| `UTILICARE_MODEL` | Gemini model identifier | `models/gemini-flash-latest` |

## Evidence and documentation

- [Final engineering report](docs/Final_Engineering_Report.pdf)
- [Evaluation report](evidence/FINAL_EVALUATION_REPORT.md)
- [Failure catalogue and remediation evidence](docs/evaluation/Failure_Catalogue_and_Remediation_Evidence.md)
- [Week 7 scenario evaluation](docs/evaluation/Week%207_37scenario_evaluation.md)
- [Prompt specification](prompts/prompt_spec.md)
- [Prompt changelog](prompts/CHANGELOG.md)
- [Presentation deck](docs/presentation/FINAL_PRESENTATION_DECK.md)

## Stopping the demo

Return to the terminal running Uvicorn and press:

```text
Ctrl+C
```

## License and academic use

This repository was developed as an academic capstone prototype. Review the project and course requirements before using any component in a production utility-service environment.

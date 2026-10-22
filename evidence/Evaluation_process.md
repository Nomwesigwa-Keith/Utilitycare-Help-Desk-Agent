Completion tracker
[ ] Activate .venv312 and verify Python 3.12
[ ] Run the full pytest suite: 13 expected passing tests
[ ] Run RAG evaluation: 15 expected passing cases
[ ] Run extended evaluation: 37 expected passing cases
[ ] Run standard evaluation and verify its exit code and result
[ ] Inspect generated CSV and JSON summaries
[ ] Review Week 4 failure-authorization and Week 7 guardrail evidence
[ ] Check all evaluation reports for outdated metrics
[ ] Capture genuine screenshots in evidence/screenshots
[ ] Run git diff --check and review git status
[ ] Review and commit the final evidence changes when ready

## commands ran
cd C:\Users\Asus\Documents\Utilitycare-Help-Desk-Agent

.\.venv312\Scripts\Activate.ps1

python --version
python -m pytest --version

python -m pytest -v

python -m tests.run_rag_eval

python -m tests.run_extended_eval

python -m tests.run_eval
$LASTEXITCODE

python -m pytest tests/test_bounded_agent_mock.py -v

python -m pytest tests/test_contract_validation.py -v

python -m pytest tests/test_tools.py -v

python -m pytest tests/test_week6_working_memory.py -v

Get-Content evidence\traces\extended_evaluation_summary.json

Import-Csv evidence\traces\extended_evaluation_results.csv | Format-Table -AutoSize

Import-Csv evidence\traces\week3_rag_eval_results.csv | Format-Table -AutoSize

(Import-Csv evidence\traces\extended_evaluation_results.csv).Count

(Import-Csv evidence\traces\week3_rag_eval_results.csv).Count

Get-ChildItem evidence\traces -File | Select-Object Name, Length, LastWriteTime | Format-Table -AutoSize

Get-Content evidence\traces\week4_failure_authorization_results.csv

Get-Content evidence\traces\week7_guardrail_pi_summary.json

Get-Content evidence\traces\week7_observability_trace_1_provider_error.json

Get-ChildItem docs\evaluation -Recurse -File | Select-Object FullName, Length | Format-Table -AutoSize

Get-Content "docs\evaluation\Week3_RAG_Evaluation_and_Failure_Catalogue.md"

Get-Content "docs\evaluation\Week4_Failure_Authorization_Test_Evidence.md"

Get-Content "docs\evaluation\Week5_Execution_Trace_Evidence.md"

Get-Content "docs\evaluation\Week6_Working_Memory_Evidence.md"

Get-Content "docs\evaluation\Week7_Observability_Tracing_Evidence.md"

Get-Content "docs\evaluation\Week 7_37scenario_evaluation.md"

Get-Content "docs\evaluation\Failure_Catalogue_and_Remediation_Evidence.md"

New-Item -ItemType Directory -Force evidence\screenshots

Get-ChildItem evidence\screenshots -Force

git diff --check

git status

git diff --stat

git diff -- evidence/traces/extended_evaluation_summary.json

git diff -- evidence/traces/week3_rag_eval_results.csv

git diff -- evidence/traces/extended_evaluation_results.csv

git ls-files evidence/traces docs/evaluation evidence/screenshots

git status --short

git add evidence/traces/extended_evaluation_results.csv

git add evidence/traces/extended_evaluation_summary.json

git add evidence/traces/week3_rag_eval_results.csv

git diff --cached --check

git diff --cached --stat

git status

git commit -m "Update final agent evaluation evidence"

git push origin nankunda
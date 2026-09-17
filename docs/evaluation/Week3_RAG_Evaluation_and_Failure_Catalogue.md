# Week 3 RAG Evaluation and Failure Catalogue

## Evaluation method

`tests/rag_test_cases.json` contains 15 retrieval questions: 10 answerable, 3 partially answerable, and 2 deliberately unanswerable. `python -m tests.run_rag_eval` runs the local deterministic retriever and writes the raw result table to `evidence/traces/week3_rag_eval_results.csv`.

A retrieval test passes when its expected grounding status matches the result and, for answerable or partially answerable questions, the expected controlled source appears in the returned source list. This evaluates retrieval and source traceability. A separate live-model run is required to evaluate the final generated guidance.

## Grounding controls

- The corpus is read only from `knowledge/corpus/`; every document must match a row in `knowledge/source_register.csv`.
- Every chunk retains its document ID, title, category, and chunk ID.
- The application, rather than Gemini, attaches returned sources and the retrieval trace to the API response.
- When no relevant chunk is found, the model receives `insufficient_evidence` and must not answer from its memory.
- The application rejects a model response that claims a grounding status different from the retriever's status.

## Failure catalogue

| ID | Failure or limitation | Cause | Current response | Re-test evidence |
| --- | --- | --- | --- | --- |
| F-01 | A current restoration time cannot be answered. | The controlled corpus contains reporting guidance, not live outage data. | Mark the result as partially answerable; do not claim a current status or time. | `RAG-11` |
| F-02 | A precise billing rate cannot be answered. | No tariff table or customer account data is in the corpus. | Mark the result as partially answerable and direct it to human billing review. | `RAG-12` |
| F-03 | A question outside utility support could be answered from model memory. | A foundation model has general knowledge beyond the controlled corpus. | Retriever returns `insufficient_evidence`; prompt prohibits memory-based guidance. | `RAG-14`, `RAG-15` |
| F-04 | Lexical retrieval can miss unfamiliar wording or synonyms. | This Week 3 baseline uses transparent token-overlap ranking, not semantic embeddings. | Retain query, scores, chunks and source IDs in the trace; review missed questions before choosing an embedding upgrade. | Run all 15 cases and record failures. |
| F-05 | A Gemini request can exceed a short client deadline or meet temporary service overload. | The Week 2 client used a 3-second deadline and disabled retries; the provider also returned 503 and 429 responses. | Use a 30-second per-attempt timeout with bounded exponential retries for 429, 503 and 504. Retain the final error when retries are exhausted. | Re-run one grounded `/triage` request after quota is available. |
| F-06 | Duplicate-charge question retrieved the wrong document. | The initial token-overlap matcher treated `charged` and `charge` as different tokens, so generic billing documents outranked KB-023. | Normalize common billing word forms before indexing and retrieval. | Re-tested: RAG-09 retrieved KB-023; the final retrieval evaluation passed 15/15. |

## Result-recording rule

The final `evidence/traces/week3_rag_eval_results.csv` was generated from the corrected code and records 15/15 retrieval cases passed. Record any future failed case, its returned source IDs, and the correction made before rerunning it.

# Prompt Version History

## v2.0 - 2026-09-17

Added the Week 3 grounding contract. The prompt now receives controlled retrieved context, requires a short guidance statement based only on that context, and requires the model to declare whether retrieval supplied sufficient evidence. Source citations and retrieval traces remain deterministic application output rather than model-generated claims.

## v1.1 - 2026-09-11

Changed the baseline classification prompt into a complete triage contract. It now defines each of the six categories used by the application, explicitly handles ambiguous and nonsensical input, requires a clarification flag and question, and prohibits fabricated tool use, ticket actions, sensitive-data handling, infrastructure control, financial actions, and unsupported promises. These changes make outputs safer to evaluate and consistent with the Project Charter and AI Boundary Matrix.

## v1.0 - 2026-09-11

Established the initial JSON-only classifier contract: a UtiliCare help-desk assistant selects one of `billing`, `outage`, `service_request`, `account`, `complaint`, or `other`, and returns category, confidence, and a one-sentence summary. This version proved the model integration path but did not specify ambiguity handling, safety boundaries, or a reliable recovery response for malformed or nonsensical customer messages.

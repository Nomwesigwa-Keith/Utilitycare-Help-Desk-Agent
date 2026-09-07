## Project Charter
## 1. Problem Statement
UtilityCare is a utility company for electricity and water services whose customer help desk currently handles service requests manually over phone and walk-in. Agents spend significant time searching printed manuals and past tickets to diagnose common issues such as power outages, suspected meter faults, water leaks and billing queries. There is no consistent way to check whether an outage is already known before creating a duplicate ticket. This causes slow response times, inconsistent troubleshooting advice, and duplicate tickets.

## 2. Target User 
Primary user: UtilityCare customer service agent triaging incoming customer issues.
Secondary user: the customer submitting the issue.

## 3. AI Value Proposition
AI is used for reasoning, retrieval and planning: understanding the customer's free-text issue, retrieving grounded troubleshooting guidance from an approved knowledge base, deciding which of a small set of approved tools to use and drafting a structured ticket. AI does not make final routing or closure decisions autonomously.

## 4. Minimum Proposal Statement
Our system helps a UtilityCare help-desk agent complete first-line triage of customer service requests. AI is used for reasoning, retrieval and planning. Deterministic software remains responsible for authentication, ticket schema validation, routing rules and escalation thresholds. The agent may use approved tools such knowledge base search but may not perform remote infrastructure control, automatic disconnection/reconnection, billing changes or autonomous ticket submission. We will build and evaluate the system using a synthetic knowledge base of public style help content and outage records.

## 5. Scope
In scope, Understanding and classifying a customer's service issue from free text.
Retrieving troubleshooting guidance from the created knowledge base.
Checking a mock outage/status tool for the customer's area.
Drafting a structured support ticket (category, priority, summary, next action).
Out of scope
Any remote control of infrastructure i.e. disconnection and reconnection.
Billing, refunds or any financial transaction.
Real customer data.
Autonomous ticket closure or escalation without human confirmation.

## 6. Assumptions
The team will author a small, synthetic knowledge base of troubleshooting/FAQ-style content.
The outage/status tool and ticketing system are simulated services built by the team, not connections to a real utility.
One foundation model will be integrated through the application.

## 7. Constraints
No confidential, personal or institutional data may be used or sent to external AI services.
High-impact actions such as ticket routing, escalation and closure must stay behind human approval.
Evidence trails: GitHub commits and ClickUp tasks.

## 8. Success Criteria
A user can describe a service issue and receive grounded, sourced troubleshooting guidance.
The agent correctly checks outage status before recommending escalation.
A correctly structured ticket draft is produced and requires explicit human approval to submit.
By Week 8: 30+ evaluation scenarios pass acceptable thresholds for groundedness, tool selection and safety (no unauthorized actions).

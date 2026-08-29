# AI Revenue Recovery Agent — Running Notes

## What We Are Building
A working AI Revenue Recovery Agent that identifies revenue at risk, diagnoses the situation, predicts recovery probability, chooses a recovery strategy, executes a safe simulated action, learns from outcomes, and measures recovered revenue.

## Multi-Agent Development System
We are building the application using multiple development agents:
- Cursor
- Antigravity
- Local/open-source agents when useful

They share the same project folder.

The `.agent/` directory is the shared memory/state system.

Important files:
- `.agent/TASKS.md` — task queue
- `.agent/STATE.md` — current project state
- `.agent/HANDOFF.md` — agent handoff instructions
- `.agent/AGENT_STATUS.json` — current agent status
- `.agent/DECISIONS.md` — architecture decisions
- `.agent/CHANGELOG.md` — project changes
- `AGENTS.md` — instructions all coding agents must follow

Agents must not depend on their previous chat history. The project files are the source of truth.

## Completed Work

### Step 1 — Shared Workspace
Completed.

Created the shared `.agent/` state system and initialized Git.

Git checkpoint:
`chore: initialize multi-agent workspace`

### Step 2 — Multi-Agent Protocol
Completed.

Created `AGENTS.md`.

This defines:
- shared project state
- agent ownership
- checkpoint requirements
- handoff procedure
- usage-constrained handoff behavior
- Git safety rules
- development principles

### Step 2.5 — State Synchronization
Completed.

Updated the `.agent/` files so the project correctly reflected that setup was complete and Cursor was the next development owner.

Git checkpoint:
`17e3451 — chore: complete multi-agent project setup`

### Step 3 — Backend Foundation
Completed by Cursor.

Created:
- `backend/app/__init__.py`
- `backend/app/main.py`
- `backend/app/config.py`
- `backend/app/database.py`
- `backend/app/models.py`
- `backend/tests/__init__.py`
- `backend/tests/test_health.py`
- `backend/requirements.txt`
- `.env.example`
- `backend/README.md`
- `.gitignore`

Installed:
- FastAPI
- Uvicorn
- SQLAlchemy
- python-dotenv
- pytest
- httpx

Implemented:
- FastAPI application
- SQLite database
- SQLAlchemy setup
- Initial Customer, RecoveryCase, Event and Action models
- `/health` endpoint
- Basic automated test

Verification:
`GET /health` works.

Test result:
`1 passed`

Git checkpoint:
`54c0d4905c3832c453c876e6429fe3a35f410e49 — checkpoint: backend foundation`

Final status:
Working tree clean.

### Step 4 — Synthetic Data Foundation
Completed by Cursor.

Created:
- `scripts/generate_data.py`
- `scripts/seed_historical.py` (optional SQLite import using existing models)
- `data/historical_events.csv`
- `backend/tests/test_historical_events.py`

Dataset size:
2,500 rows

Event types:
- payment_failure: 1,018
- checkout_abandonment: 760
- subscription_failure: 722

Recovered / not recovered:
1,260 recovered, 1,240 not recovered

Important fields:
customer_id, event_id, event_type, amount, payment_method, failure_reason, customer_age, account_age, previous_successes, previous_failures, retry_count, checkout_visits, cart_value, subscription_age, timestamp, recovery_action, recovery_time, recovered, recovered_amount

Categories:
- payment_method: card, paypal, apple_pay, google_pay, ach, bank_transfer
- recovery_action: retry_payment, update_payment_method, email_reminder, dunning_sequence, sms_nudge, cart_recovery_email, wait_retry, offer_discount
- failure_reason: event-type-specific (e.g. insufficient_funds, card_expired, cart_hesitation, dunning_unresponsive)

Consistency rules:
- Checkout abandonment has cart_value and checkout_visits; subscription_age is 0
- Subscription failure has subscription_age >= 1; cart_value is 0
- Payment failure has a payment failure reason; subscription_age is 0
- recovered=false rows have recovered_amount=0
- Most recovered rows collect the original amount (some partial recoveries)

Tests performed:
`pytest` from `backend/` — 9 passed (health + dataset tests)

Not done in this step:
- ML model training
- Recovery Agent
- LLM
- Frontend
- Database schema changes

Git checkpoint:
Not created in this step. The human owner will inspect and commit.

### Step 5 — Recovery Agent Analysis Pipeline
Started by Cursor, finalized & verified by Antigravity upon Cursor hitting its usage limit.

Created:
- `backend/app/agent/__init__.py`
- `backend/app/agent/schemas.py`
- `backend/app/agent/detector.py`
- `backend/app/agent/diagnosis.py`
- `backend/app/agent/scoring.py`
- `backend/app/agent/strategy.py`
- `backend/app/agent/orchestrator.py`
- `backend/tests/test_recovery_agent.py`

Modified:
- `backend/app/main.py` (added `POST /recovery/analyze` endpoint)

Implemented:
- Event detection & normalization for `payment_failure`, `checkout_abandonment`, and `subscription_failure`
- Deterministic explainable diagnosis rules with recoverability categories (`recoverable`, `potentially_recoverable`, `unlikely`)
- Deterministic explainable recovery probability scoring with confidence levels (`LOW`, `MEDIUM`, `HIGH`) and explicit factor breakdown
- Strategy selection supporting 7 recovery actions (`retry_now`, `retry_later`, `request_alternate_payment`, `send_checkout_reminder`, `send_subscription_update_request`, `escalate_to_manual_review`, `do_nothing`)
- `RecoveryAgent` orchestrator coordinating DETECT → DIAGNOSE → SCORE → CHOOSE STRATEGY
- Pydantic models for incoming event validation and structured analysis output
- FastAPI `POST /recovery/analyze` endpoint with error handling for unsupported and invalid events
- 9 unit and endpoint integration tests in `backend/tests/test_recovery_agent.py`

Verification:
- `pytest -v` across all backend tests: 18 passed (health, dataset, and recovery agent pipeline).

Not done in this step:
- sklearn ML model training/inference
- Ollama / LLM reasoning and messaging
- Frontend
- Action execution / simulation
- Bandit learning

Git checkpoint:
Not created. Handed over to user / next step.

## Current Status

P1 — Build Recovery Agent analysis pipeline: COMPLETE

Current owner:
Antigravity

Next major task:
P1 — Build real ML recovery probability model

Do not start the next task automatically.

## Architecture We Are Following

Product agent workflow:

DETECT
→ DIAGNOSE
→ SCORE
→ CHOOSE STRATEGY
→ GENERATE ACTION
→ EXECUTE
→ OBSERVE OUTCOME
→ UPDATE LEARNING
→ MEASURE REVENUE RECOVERED

Hybrid approach:
- deterministic rules for obvious decisions
- scikit-learn for recovery probability
- LLM for reasoning and customer messages
- adaptive learning/bandit for recovery strategy timing
- simulation layer for safe demo execution
- SQLite for persistent state

## Important Rule
We are building incrementally.

Do not dump or implement the entire application at once.

After each meaningful step:
1. Build
2. Test
3. Update project state
4. Update these running notes
5. Create Git checkpoint
6. Only then move to the next step

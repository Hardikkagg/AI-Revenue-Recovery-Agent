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

### Step 5.5 — Architecture & Operational Model Documentation
Completed by Antigravity before starting Step 6.

Created:
- `ARCHITECTURE.md` (High-level system architecture, current vs. planned matrix, complete Mermaid diagram, data flow, multi-agent protocol)
- `MODEL.txt` (Comprehensive system & operational model specification covering problem statement, 3 failure scenarios, roles of rules/ML/LLM/bandit/simulation/database, agentic properties, limitations, and 5-minute demo structure)

Updated:
- `.agent/STATE.md`
- `.agent/TASKS.md`
- `.agent/AGENT_STATUS.json`
- `.agent/CHANGELOG.md`
- `RUNNING_NOTES.md`

### Synthetic Data Validation
Completed by Antigravity before starting Step 6.

- Audit Date: August 30, 2026
- Dataset File: `data/historical_events.csv`
- Dataset Size: 2,500 rows × 19 columns
- Validation Result: PASS
- Important Findings: 100% data integrity, 0 nulls, 0 duplicate event IDs, clean event-type constraints, balanced target (50.4% recovered / 49.6% unrecovered).
- Leakage Findings: Mapped features into Group A (Safe), Group B (Excluded metadata/action), and Group C (Leaky post-outcome: `recovered_amount`, `recovery_time`).
- Recommendation for Step 6: Proceed with training using 12 approved Group A features (`amount`, `payment_method`, `failure_reason`, `customer_age`, `account_age`, `previous_successes`, `previous_failures`, `retry_count`, `checkout_visits`, `cart_value`, `subscription_age`, `event_type`).

Created:
- `DATA_VALIDATION.md`

### Synthetic Data ML Separability Audit
Completed by Antigravity before starting Step 6.

- Audit Date: August 30, 2026
- Models Tested: `DummyClassifier`, `LogisticRegression`, `RandomForestClassifier`, `GradientBoostingClassifier`
- Evaluation Results:
  - `DummyClassifier`: Acc 50.40%, ROC-AUC 0.5000
  - `LogisticRegression`: Test Acc 60.60%, Test ROC-AUC 0.6383, 5-Fold CV Acc 60.40% ± 1.41%, 5-Fold CV ROC-AUC 0.6389 ± 0.0230
  - `RandomForestClassifier`: Test Acc 61.20%, Test ROC-AUC 0.6280, 5-Fold CV Acc 59.12% ± 2.01%
  - `GradientBoostingClassifier`: Test Acc 60.60%, Test ROC-AUC 0.6204, 5-Fold CV Acc 59.00% ± 1.06%
- Group-Aware Customer CV (`GroupKFold`): LogisticRegression achieved 60.04% ± 1.05% (delta < 0.4% vs random split), verifying zero customer contamination.
- Leakage / Suspicious Performance Findings: No model reached $\ge 95\%$ or deterministic bounds. Dataset exhibits realistic irreducible noise from Bernoulli sampling in generator.
- Realism Assessment & Final Verdict: **A. REALISTIC / HEALTHY**
- Recommendation for Step 6: Use `LogisticRegression` with `StandardScaler` + `OneHotEncoder` on Group A features.

Created:
- `DATA_MODEL_EVALUATION.md`

### Step 6 — Real ML Recovery Probability Model
Completed by Antigravity.

- Model Architecture: `LogisticRegression` with `StandardScaler` (numerical features) + `OneHotEncoder` (categorical features) + `SimpleImputer` pipeline.
- Training Data: `data/historical_events.csv` (2,500 rows).
- Features Used (12 Approved Group A Features):
  - Numerical: `amount`, `customer_age`, `account_age`, `previous_successes`, `previous_failures`, `retry_count`, `checkout_visits`, `cart_value`, `subscription_age`
  - Categorical: `event_type`, `payment_method`, `failure_reason`
- Features Excluded (Target Leakage / Circularity / Meta):
  - Leakage: `recovered_amount`, `recovery_time`
  - Operational Circularity: `recovery_action`
  - Identifiers: `customer_id`, `event_id`, `timestamp`
- Evaluation Metrics:
  - Train Accuracy: 61.95% | Train ROC-AUC: 0.6611
  - Test Accuracy: 60.60% | Test ROC-AUC: 0.6383
  - Precision: 0.5958 | Recall: 0.6786 | F1 Score: 0.6345
  - Confusion Matrix: `[[132, 116], [81, 171]]` (Holdout test $n=500$)
  - 5-Fold Stratified CV Accuracy: 60.40% ± 1.41% | CV ROC-AUC: 0.6389 ± 0.0230
- Integration:
  - `backend/app/agent/predictor.py` provides `MLPredictor` with feature conversion, model loading, and coefficient-based factor explainability.
  - `backend/app/agent/scoring.py` updated to use `MLPredictor` for recovery probability scoring while preserving deterministic baseline as a safe fallback when model is unavailable.
  - Endpoint `POST /recovery/analyze` verified.
  - Added tests in `backend/tests/test_ml_model.py`. Full test suite passes: 29/29 tests green.

Created:
- `scripts/train_model.py`
- `backend/models/recovery_model.joblib`
- `backend/models/model_metrics.json`
- `backend/app/agent/predictor.py`
- `backend/tests/test_ml_model.py`

## Current Status

Step 6 (Real ML Recovery Probability Model): COMPLETE
Synthetic Data ML Separability Audit: COMPLETE (A. REALISTIC / HEALTHY)
Synthetic Data Validation: COMPLETE (PASS)
Documentation (ARCHITECTURE.md & MODEL.txt): COMPLETE
P1 — Build Recovery Agent analysis pipeline: COMPLETE

Current owner:
Antigravity

Next major task:
P1 — Build recovery simulation engine (Step 7)

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

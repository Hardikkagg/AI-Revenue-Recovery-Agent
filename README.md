# AI Revenue Recovery Agent

A sandbox AI Revenue Recovery Agent for failed-revenue events. It detects and normalizes events, diagnoses the failure, estimates recovery probability, selects a safe strategy, generates bounded reasoning and customer copy, simulates execution, records the outcome, calculates reward, updates an adaptive policy, persists recovery data, and exposes metrics.

The system does not process real payments, recover production revenue, send real customer messages, or create real support tickets. Payment gateway, communication, and manual-review actions are simulated locally.

## Implemented pipeline

`RecoveryEventInput` -> detection and normalization -> deterministic diagnosis -> ML recovery scoring -> deterministic strategy selection -> adaptive policy selection among approved strategies -> optional Ollama reasoning/customer message or deterministic fallback -> sandbox simulation -> observed outcome -> reward -> in-memory policy update -> SQLite persistence -> metrics.

Deterministic rules own validation, diagnosis, strategy safety, and financial bounds. Machine learning estimates probability. The optional LLM produces bounded text after the strategy is selected. It never authorizes recovery.

## Run locally

Backend:

```text
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Frontend:

```text
cd frontend
npm install
npm run dev
```

During Vite development, frontend `/api` requests are proxied to `http://127.0.0.1:8000`. A production deployment needs an appropriate `VITE_API_BASE_URL` and backend CORS configuration.

## API

- `GET /health` checks service availability.
- `POST /recovery/analyze` validates and analyzes an event without executing an action.
- `POST /recovery/simulate` analyzes an event, runs the sandbox action, observes the result, updates the in-memory policy, and persists the simulation.
- `GET /recovery/metrics` returns persisted case, revenue, recovery-rate, strategy, and feedback metrics.
- `POST /recovery/retrain` trains a candidate model from baseline data plus validated persisted simulation feedback and promotes it only when validation checks pass.

## Five-minute demo

1. Select Payment Failure with `network_error` and run Analyze Recovery.
2. Show the ML probability, temporary-failure diagnosis, recommended delayed retry, confidence, score factors, and deterministic fallback reasoning if Ollama is unavailable.
3. Run Execute Recovery and show the simulated recovered amount.
4. Open Learning to show outcome, reward, strategy, and policy feedback; then open Strategy Performance to show persisted metrics.
5. Select Fraud Hold and analyze it. Show `escalate_to_manual_review`, `MANUAL REVIEW`, disabled execution, and the deterministic safety explanation.

## ML and learning boundaries

The checked-in model is a scikit-learn LogisticRegression pipeline trained on 2,500 synthetic historical events. It uses 12 pre-outcome features: `amount`, `customer_age`, `account_age`, `previous_successes`, `previous_failures`, `retry_count`, `checkout_visits`, `cart_value`, `subscription_age`, `event_type`, `payment_method`, and `failure_reason`. The documented holdout performance is approximately 60.6% accuracy and 0.638 ROC-AUC; this is not production-grade evidence.

Retraining uses those same 12 features plus the `recovered` label. Outcome-derived fields, strategy, identifiers, decision context, and other leakage fields are excluded and invalid feedback is rejected.

The adaptive policy is an in-memory contextual epsilon-greedy policy. It adapts strategy selection only and can select only from strategies already approved by deterministic rules. It does not learn retry delays or communication channels, and its state is lost on process restart.

See [ARCHITECTURE.md](ARCHITECTURE.md) for the detailed data flow and [MODEL.txt](MODEL.txt) for the current operational model.

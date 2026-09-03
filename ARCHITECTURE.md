# AI Revenue Recovery Agent: Current Architecture

## Purpose

This project is a sandbox AI Revenue Recovery Agent for failed-revenue events. It demonstrates analysis, safe strategy selection, simulated execution, outcome learning, persistence, and operational metrics. It does not process real payments, recover real production revenue, send real customer messages, or create real support tickets.

## End-to-end data flow

```text
RecoveryEventInput
  -> detection and normalization
  -> deterministic diagnosis
  -> ML recovery scoring
  -> deterministic strategy selection
  -> adaptive policy selection among approved strategies
  -> Ollama reasoning/customer message or deterministic fallback
  -> sandbox simulation
  -> observed outcome
  -> reward calculation
  -> adaptive policy update
  -> SQLite persistence
  -> aggregated metrics
```

`POST /recovery/analyze` runs through strategy selection and text generation but does not execute or persist an action. `POST /recovery/simulate` runs the complete flow and persists one simulated case, event, and action.

## Component responsibilities

### Detection and diagnosis

`backend/app/agent/detector.py` normalizes supported event types: `payment_failure`, `checkout_abandonment`, and `subscription_failure`. It fills safe defaults and validates relevant constraints.

`backend/app/agent/diagnosis.py` applies deterministic rules for temporary failures, insufficient funds, expired cards, declines, fraud holds, closed accounts, checkout abandonment, and subscription failures. It returns a diagnosis code, plain-language explanation, recoverability, and recommended direction.

### ML scoring

`backend/app/agent/predictor.py` loads the checked-in scikit-learn LogisticRegression pipeline. It uses nine numeric features and three categorical features:

- Numeric: `amount`, `customer_age`, `account_age`, `previous_successes`, `previous_failures`, `retry_count`, `checkout_visits`, `cart_value`, `subscription_age`
- Categorical: `event_type`, `payment_method`, `failure_reason`

The model estimates recovery probability and returns coefficient-based feature contributions. If the model is unavailable or prediction fails, `scoring.py` uses its deterministic baseline scorer.

### Strategy and safety

`backend/app/agent/strategy.py` selects one of seven strategies: `retry_now`, `retry_later`, `request_alternate_payment`, `send_checkout_reminder`, `send_subscription_update_request`, `escalate_to_manual_review`, or `do_nothing`.

**AI proposes. Deterministic safety rules authorize.** Fraud holds, closed accounts, and cancellation-intent cases are forced to `escalate_to_manual_review`. The adaptive policy cannot override a forced escalation or no-op decision. The frontend disables execution for escalation, and the simulated gateway independently rejects terminal retry conditions.

### Adaptive policy

`backend/app/learning/policy.py` implements an in-memory contextual epsilon-greedy policy. Its context uses event type, diagnosis, payment method, probability bucket, and retry bucket. It updates strategy reward statistics after simulation and may choose only from the deterministic allow-list. It does not optimize retry delays or communication channels, and its state is not persisted.

### LLM and fallback

`backend/app/llm/` optionally calls a local Ollama server after the strategy is selected. The prompt constrains the LLM to produce reasoning and, for communication strategies, customer copy. It cannot change the strategy, authorize payment, claim pre-execution success, disclose internal scores, or invent discounts.

If Ollama is disabled, unavailable, times out, or returns invalid output, `LLMService` returns deterministic templates. The recovery API continues without an LLM. Non-communication strategies always have no customer message.

### Simulation and persistence

`backend/app/simulation/engine.py` executes all strategies in a local sandbox. The simulated gateway handles retry outcomes; the simulated communication service handles customer responses; escalation and no-op strategies produce no payment attempt. Recovered amounts are clamped to the amount at risk.

When called through the API, simulation persistence creates `Customer`, `RecoveryCase`, `Event`, and `Action` records in SQLite. The event stores the 12 ML features plus decision context. The action stores outcome, recovered amount, reward, and simulation details. `GET /recovery/metrics` aggregates persisted records.

## Retraining and leakage boundary

`POST /recovery/retrain` combines the 2,500-row baseline dataset with validated persisted simulation feedback, trains a candidate LogisticRegression pipeline, and promotes it only when the ROC-AUC and accuracy checks pass. Otherwise the current production model remains.

Training input is restricted to the 12 pre-outcome features listed above; `recovered` is the target label. The extraction service rejects missing or invalid fields, invalid labels, duplicate simulation IDs, inconsistent recovered amounts, and recovered amounts outside `[0, amount]`. It excludes outcome-derived fields such as `recovered_amount`, `recovery_time`, outcome, status, reward, customer response, gateway references, action details, strategy, identifiers, and decision context.

The model is trained on synthetic data and simulated feedback. Its approximate holdout metrics are 60.6% accuracy and 0.638 ROC-AUC, so it should not be presented as production-grade.

## API surface

| Endpoint | Behavior |
|---|---|
| `GET /health` | Returns service health. |
| `POST /recovery/analyze` | Detects, diagnoses, scores, selects, and generates reasoning without execution. |
| `POST /recovery/simulate` | Runs analysis plus sandbox execution, outcome observation, reward/policy update, and persistence. |
| `GET /recovery/metrics` | Aggregates persisted recovery and strategy metrics. |
| `POST /recovery/retrain` | Trains and conditionally promotes a feedback-augmented candidate model. |

## Frontend boundaries

The React frontend calls analyze, simulate, and metrics. Its Simulation and Learning views show current-session results; Strategy Performance shows persisted metrics. Vite proxies `/api` to the backend during development. Production requires explicit API URL and CORS configuration.

## Demo sequence

Use a `payment_failure` with `network_error`: Analyze, show ML probability/diagnosis/strategy/confidence/factors and fallback reasoning, Execute, show the simulated recovered amount, then show Learning and Strategy Performance. Follow with `fraud_hold`: Analyze, show `escalate_to_manual_review`, `MANUAL REVIEW`, disabled execution, and the safety explanation.

## Known limitations

- All execution and recovered revenue are simulated; no real settlement occurs.
- Simulation feedback is synthetic and influenced by the model probability.
- Policy statistics are in memory and disappear on restart.
- Simulation submissions are not deduplicated; repeated events create new cases.
- LLM output is optional and fallback text is expected when Ollama is unavailable.
- Frontend secondary views are session-scoped except for persisted Strategy Performance metrics.
- The model is trained on a synthetic dataset with modest validation performance.

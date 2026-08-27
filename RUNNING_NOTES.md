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

## Current Status

P0 — Backend Foundation: COMPLETE

Current owner:
None / waiting for next task.

Next major task:
Build the synthetic data foundation and recovery-case API/logic as the next incremental backend step.

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

# AI Revenue Recovery Agent — Multi-Agent Development Protocol

## 1. SOURCE OF TRUTH

The project folder is the single source of truth.

Never rely on previous AI conversation history.

Before starting work, read:

.agent/STATE.md
.agent/TASKS.md
.agent/HANDOFF.md
.agent/DECISIONS.md
.agent/CHANGELOG.md

## 2. AGENT OWNERSHIP

Only one development agent should actively modify a workstream at a time.

Current development agents:

- Cursor
- Antigravity
- Local/open-source coding agent when required

Do not overwrite another agent's work.

## 3. BEFORE WORKING

1. Read all relevant .agent files.
2. Identify the current task.
3. Check the Git status.
4. Understand existing implementation before changing it.
5. Do not redesign working architecture without a documented reason.

## 4. WHILE WORKING

Work only on the assigned task.

Prefer small, testable changes.

Do not create unnecessary dependencies.

Do not rewrite working code simply to make it look different.

After completing a meaningful unit of work:

- Test it.
- Update .agent/STATE.md.
- Update .agent/CHANGELOG.md.
- Update .agent/AGENT_STATUS.json.

## 5. CHECKPOINTS

Before handing work to another agent:

1. Finish or safely stop the current task.
2. Test the current state.
3. Update STATE.md.
4. Update TASKS.md.
5. Write a detailed HANDOFF.md.
6. Update AGENT_STATUS.json.
7. Commit the work to Git.

Never hand off with important work existing only in conversation history.

## 6. HANDOFF

A handoff must contain:

- Previous agent
- Next agent
- Completed work
- Current work
- Files changed
- Tests performed
- Known problems
- Exact next action
- Things the next agent must NOT change unnecessarily

## 7. USAGE / LIMIT HANDOFF

If the agent determines that its available usage is becoming constrained:

DO NOT start another large task.

Instead:

1. Finish the smallest safe unit of work.
2. Save all files.
3. Run tests.
4. Create checkpoint.
5. Update HANDOFF.md.
6. Set handoff_required=true in AGENT_STATUS.json.
7. Stop.

The project must remain usable even if an agent becomes unavailable.

## 8. GIT

Create checkpoints frequently.

Use descriptive commits such as:

checkpoint: backend foundation
checkpoint: recovery agent
checkpoint: payment workflow
checkpoint: frontend dashboard
checkpoint: llm integration

Never intentionally commit API keys, passwords or secrets.

## 9. CODING PRINCIPLES

Build the smallest working implementation first.

Do not over-engineer.

Prefer:

- simple architecture
- readable code
- explicit APIs
- reusable components
- deterministic behavior where appropriate
- real functionality over visual mockups

## 10. PRODUCT ARCHITECTURE

The Revenue Recovery Agent is a hybrid system.

Use:

Rules/logic:
for deterministic decisions

Machine Learning:
for recovery probability

LLM:
for reasoning, explanations and personalized customer messages

Learning system:
for adaptive recovery strategy selection

Simulation:
for safe demonstration of actions

Database:
for persistent state and outcomes

## 11. PRODUCT WORKFLOW

Every recovery case should ultimately follow:

DETECT
↓
DIAGNOSE
↓
SCORE
↓
CHOOSE STRATEGY
↓
GENERATE ACTION
↓
EXECUTE
↓
OBSERVE OUTCOME
↓
UPDATE LEARNING
↓
MEASURE REVENUE RECOVERED

## 12. DEMO REQUIREMENT

This project is being built for a 5-minute interactive demonstration.

Every important feature must actually work.

Avoid fake buttons and static numbers.

When an action is executed, the application should update its state and metrics.

## 13. IMPORTANT

Do not build the entire application at once.

Build incrementally.

Complete and verify each layer before moving to the next.

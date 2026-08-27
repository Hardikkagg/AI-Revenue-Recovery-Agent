# Architecture Decisions

## Decision 001 — Shared State

Cursor and Antigravity will use the same project folder.

Agent state will be stored inside .agent/.

Agents must not rely on conversation history.

## Decision 002 — Sequential Ownership

Only one coding agent should actively modify a given workstream at a time.

## Decision 003 — Checkpoints

Agents must save their work and create a checkpoint before handoff.

## Decision 004 — Git

Git will be used as the safety layer for all major checkpoints.

## Decision 005 — Product Architecture

The Revenue Recovery Agent will use a hybrid architecture:

Rules/logic + ML + LLM + learning system.

The LLM will not control the entire system.

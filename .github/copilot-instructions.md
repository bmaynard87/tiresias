# Copilot Instructions — Tiresias

## 1) Project Summary

- Tiresias is a **CI gatekeeper**: it enforces design quality through deterministic pass/fail decisions.
- It performs **pre-mortem design review** on Markdown documents and emits **structured outputs**.
- It is **not an assistant**: it gates on trackable obligations, not vibes.
- It is **deterministic, single-pass**: read → review → validate → render → write outputs → exit decision.
- It uses a **provider interface** for any LLM calls so tests can run with **no network**.

## 2) Non-Negotiables (Hard Constraints)

- **Deterministic behavior**
  - No randomness, no time-based behavior, no unstable ordering.
  - No environment-dependent behavior unless explicitly modeled as configuration.
- **No network in tests**
  - Tests must be hermetic and must not reach external services.
  - Use `FakeProvider` fixtures for all provider interactions.
- **No agent loops / autonomous multi-step tool use**
  - No background workers, no async loops, no “agentic” iterative execution.
  - Implement changes as plain functions and deterministic control flow.
- **Single-pass execution model**
  - CLI flow must remain: read → review → validate → render → write outputs → exit decision.
  - Avoid multi-stage pipelines that require stateful retries.
- **Provider interface required**
  - All provider logic must be behind an interface/protocol.
  - Real network providers must be optional and never used in tests.
- **Inputs (v1)**
  - Accept Markdown only (`.md`; optionally `.mdx` if explicitly expanded). No other formats without an explicit requirement.

## 3) TDD Expectations

- Prefer adding/updating tests first for deterministic components.
- New or changed logic requires tests for:
  - gating decisions and risk thresholds
  - schema validation and contract enforcement
  - waiver logic and expiry enforcement
  - state continuity across runs
  - deterministic verifiers
  - CLI exit codes and file outputs
- No tests should hit the network; use `FakeProvider` fixtures.
- Prefer:
  - small unit tests for pure functions (`gating.py`)
  - contract tests for schema (fixtures + validation)

## 4) Code Style & Structure

- Keep modules **small and boring**; avoid unnecessary abstraction.
- Prefer pure functions in `gating.py` and similar modules.
- Require docstrings on public functions and clear, actionable error messages.
- Favor explicitness over cleverness.
- Avoid global state except constants.

## 5) Data Contracts (Schema-first)

- All provider output must validate against the JSON schema.
- If the schema changes, update together:
  - schema definition
  - fixtures (`tests/fixtures/valid_review.json`, `tests/fixtures/invalid_review.json`)
  - tests
- Provider output must include **evidence** when marking items resolved.
- Avoid breaking schema changes; prefer additive fields with defaults.

## 6) Closed-Loop Passing (Key Product Requirement)

- Tiresias must recognize implemented improvements and allow CI to pass.
- Gate only on **trackable obligations** (e.g., `blockers[]` with stable IDs + pass criteria), not vague findings.
- Encourage stable blocker IDs across runs; avoid renaming/reinventing blockers.
- Support explicit waivers with accountability:
  - `owner`, `reason`, optional `expiry`
  - enforce expiry deterministically
- Deterministic verifiers may confirm resolution for common pass criteria (headers, checklist).

## 7) Git/Workflow Expectations

- Encourage feature branches; `main` should always pass `pytest`.
- Prefer small PR-sized changes with clear commit messages.

## 8) Security & Safety

- Secrets only via environment variables (never committed).
- No telemetry by default.
- Do not log full document contents by default; be careful with outputs in CI.

## 9) “When in doubt” Rules for Copilot

- If asked to add behavior, add tests first.
- If asked to integrate a provider (e.g., OpenAI), keep it optional behind the provider interface and add mockable seams.
- Never introduce non-deterministic CI gating.
- Prefer additive changes and keep backwards compatibility.

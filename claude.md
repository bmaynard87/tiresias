# Claude Code Instructions for Tiresias

This file defines **project‑level instructions for Claude Code** when working in this repository.  
It exists to preserve decisions, conventions, and workflow rules so future Claude sessions behave consistently.

---

## 1. Project Overview

**Tiresias** is an AI‑assisted *pre‑mortem design review tool* that analyzes engineering artifacts (design docs, ADRs, specs, prompts) to surface risks, missing considerations, and potential failure modes **before implementation**.

Core principles:
- Deterministic, explainable output
- No hallucinated reasoning
- Human‑readable explanations
- Conservative heuristics over ML guesswork
- Trust > cleverness

---

## 2. Technology Stack

- **Language:** Python 3.12+
- **Packaging:** `uv`, PEP‑621 `pyproject.toml`
- **CLI:** Typer
- **Rendering:** Rich (text), JSON (machine)
- **Schemas:** Pydantic
- **CI/CD:** GitHub Actions (lint, typecheck, test, build, release)

No async. No networking. No external services.

---

## 3. Branching & Git Rules (MANDATORY)

Claude **must follow these rules strictly**:

- **Never commit directly to `main`.**
- All work happens on feature branches:
  - `feat/*`, `fix/*`, `chore/*`
- Tags are **release markers only** and must:
  - Be created **from `main` only**
  - Match the version in `pyproject.toml`

### Correct release flow

1. Implement feature on a feature branch
2. Open PR → merge into `main`
3. Bump version on `main`
4. Commit version bump
5. Tag `vX.Y.Z`
6. Push tag → release workflow runs

Claude should **never create or move tags** during feature work.

---

## 4. Versioning (Single Source of Truth)

- The **only** authoritative version is in `pyproject.toml`
- Runtime version must be sourced via:

```python
from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("tiresias")
except PackageNotFoundError:
    __version__ = "0.0.0+dev"
```

No hardcoded version strings in runtime code.

Tests must **not** assert specific version literals — only that a valid string is present.

---

## 5. Output Contract (CRITICAL)

### Text Output

- Designed for **human trust**
- Calm, non‑judgmental tone
- Tables for findings
- Inline contextual explanations where needed

### JSON Output

- Designed for **machine consumption**
- Always includes full data (even if text output hides it)
- Backwards‑compatible only (additive changes allowed)

Claude must **never** remove or rename existing JSON fields.

---

## 6. Evidence Handling

- Evidence explains **why** a finding fired
- Never show regexes, internal heuristics, or raw text snippets
- Evidence is:
  - Line‑based
  - Declarative
  - Deterministic

### CLI behavior

- Default text output: **no evidence**
- `--show-evidence` / `--verbose`: show evidence inline under findings
- JSON output: **always includes evidence** regardless of flags

Severity‑based truncation:
- High: all evidence
- Medium: up to 2 lines
- Low: 1 line

---

## 7. Document Maturity Labeling

Maturity provides **context**, not judgment.

### Levels (exactly four)

1. Notes
2. Early Draft
3. Design Spec
4. Production‑Ready

### Rules

- Deterministic heuristics only
- Conservative bias (prefer lower maturity when uncertain)
- Does **not** affect risk scoring math

### Display

- Always shown in text output
- Appears **before** risk score
- JSON includes structured maturity block

Example JSON shape:

```json
"maturity": {
  "level": "early_draft",
  "confidence": "medium",
  "signals": ["missing_metrics", "few_sections_detected"],
  "metrics": {
    "char_count": 842,
    "section_count": 7,
    "core_sections_present": 4
  }
}
```

---

## 8. Risk Scoring Rules

- Risk score math must remain **stable and deterministic**
- Maturity labeling may contextualize risk in text output
- Maturity **must never change the numeric risk score**

---

## 9. Coding Standards

- Ruff enforced (E, F, I, UP)
- Mypy enabled (non‑strict, no implicit Optional)
- Formatting via `ruff format`
- No unused imports, variables, or dead code

Claude must run (conceptually) before finalizing changes:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src/tiresias
uv run pytest
```

---

## 10. Test Philosophy

- Tests validate **behavior**, not implementation details
- Prefer semantic assertions over exact string matches
- Tests must not rely on version literals or timestamps

Every new feature must include tests.

---

## 11. Scope Discipline

Claude must:
- Avoid refactors unrelated to the task
- Avoid expanding feature scope without approval
- Prefer minimal, readable changes

When unsure, **ask before implementing**.

---

## 12. Claude Operating Mode

Unless explicitly told otherwise, Claude should:

1. Start in **PLAN MODE**
2. Produce a clear plan
3. Wait for approval (`OK, implement`)
4. Implement cleanly and minimally

This file overrides any default Claude behavior.

---

## End

If instructions conflict, **this file wins**.


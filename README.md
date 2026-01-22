![Tiresias Logo](docs/logo-small.svg)

# Tiresias

**Design review and pre-mortem analysis for engineering artifacts.**

Tiresias performs automated design reviews on engineering documents (design docs, ADRs, specs, and AI prompts) to identify missing considerations, risks, and potential failure modes *before* implementation. Think of it as a pre-mortem tool that catches issues early—when they’re still cheap to fix.

> **Opinionated by design:** if a concern is not documented, Tiresias treats it as missing.

---

## Who This Is For

Tiresias is designed for:

* Engineers writing design docs, ADRs, and architecture proposals
* Teams enforcing design quality gates in CI/CD
* Platform, SRE, and security teams reviewing early-stage designs
* AI engineers validating prompts and system specs before deployment

If your organization believes that **undocumented assumptions become production incidents**, Tiresias is for you.

---

## Features

* Analyzes Markdown, text, JSON, and YAML files
* Identifies missing:

  * error handling
  * success metrics
  * test strategies
  * rollout and rollback plans
* Configurable analysis profiles (`general`, `security`, `performance`, `reliability`)
* **Finding suppressions** with required justification and optional expiry dates
* Deterministic heuristics (no LLM hallucination)
* Beautiful terminal output with risk scoring
* Machine-readable JSON output for CI/CD integration
* GitHub Action support for automated PR reviews
* Secret redaction for safe analysis

---

## Quick Demo

```bash
tiresias review examples/design.md
```

**Input:**
```
# Widget Service

We will build a widget service that handles widget creation and retrieval.

## Overview
It will be fast and scalable.
```

**Output:**
<p align="center">
  <img src="docs/screenshots/demo-output.png" width="800" /><br />
  <sub>
    Example output analyzing an early-stage design document.
    High risk is expected at the “Notes” maturity level.
  </sub>
</p>

High Severity Findings

```
ARCH-001  Missing error handling strategy
OPS-001   Missing rollout/deployment plan
REQ-001   Missing success metrics
```

---

## Evidence Mode

By default, Tiresias output stays clean and actionable. Use `--show-evidence` (or `--verbose`) to explain *why* each finding fired:

```bash
tiresias review examples/design.md --show-evidence
```

Example:

```
ARCH-001 Evidence:
  • No discussion of error handling, exceptions, failures, or fallback strategies
```

Evidence is always included in JSON output, regardless of CLI flags.

---

## Document Maturity

Tiresias assigns a **Document Maturity** label to contextualize findings:

| Level            | Score Range | Meaning                                         |
| ---------------- | ----------- | ----------------------------------------------- |
| Notes            | 0–25        | Early brainstorming, gaps expected              |
| Early Draft      | 26–50       | Incomplete sections, many gaps normal           |
| Design Spec      | 51–75       | Substantive design, findings indicate real gaps |
| Production-Ready | 76–100      | Comprehensive doc, findings are critical        |

> Maturity **does not affect risk score math**. Risk scoring is deterministic and stable.

---

## Installation

### Using uv (recommended)

```bash
git clone https://github.com/bmaynard/tiresias.git
cd tiresias
uv sync

uv run tiresias review docs/design.md
```

### As a tool

```bash
uv tool install tiresias

tiresias review docs/design.md
```

> **Note:** PyPI publishing is planned for a future release. For now, please install from source using the methods above.

---

## Quick Start

```bash
# Review a single document
tiresias review docs/design.md

# Review all documents in a directory
tiresias review docs/

# Export to JSON
tiresias review docs/ --format json --output report.json

# Use a specific profile
tiresias review specs/ --profile security

# CI mode: fail on high severity findings
tiresias review docs/ --fail-on high

# Show suppressed findings
tiresias review docs/ --show-suppressed
```

---

## CLI Usage

```
tiresias review <PATH_OR_GLOB> [OPTIONS]
```

### Options

| Option                 | Default   | Description                           |
| ---------------------- | --------- | ------------------------------------- |
| `--format`             | `text`    | Output format: `text` or `json`       |
| `--severity-threshold` | `low`     | Minimum severity to display           |
| `--fail-on`            | `none`    | Exit nonzero if findings ≥ severity   |
| `--profile`            | `general` | Analysis profile                      |
| `--show-evidence`      | `false`   | Show evidence for findings            |
| `--show-suppressed`    | `false`   | Show suppressed findings              |
| `--output`             | stdout    | Write output to file                  |
| `--no-color`           | `false`   | Disable color output                  |

---

## Explaining Rules

Use the `explain` command to get detailed information about specific rules:

```bash
# Explain a specific rule
tiresias explain REQ-001

# List all available rules
tiresias explain --list

# Get JSON output
tiresias explain ARCH-001 --format json
```

### Explain Options

| Option       | Default | Description                         |
| ------------ | ------- | ----------------------------------- |
| `--format`   | `text`  | Output format: `text` or `json`     |
| `--list`     | `false` | List all available rule IDs         |
| `--output`   | stdout  | Write output to file                |
| `--no-color` | `false` | Disable color output                |

### Example: Understanding a Finding

When you see a finding in your review:

```
REQ-001  Missing success metrics
```

Get details on how to address it:

```bash
$ tiresias explain REQ-001

╭──────────────────────────────────────────────────────────────────────────────╮
│ REQ-001: Missing success metrics                                             │
╰──────────────────────────────────────────────────────────────────────────────╯

Category: Requirements
Severity: High

What it checks:
  No section found discussing success criteria, metrics, or KPIs

Why it matters:
  Without measurable success criteria, it will be difficult to determine if the
  implementation achieves its goals or to make data-driven decisions

How to address it:
  Add a section defining concrete success metrics (e.g., adoption rate,
  performance targets, user satisfaction scores)
```

---

## Baseline Comparison Mode

Compare your current design against a baseline (branch or commit) to detect regressions and new issues.

### Usage

```bash
# Compare against main branch
tiresias review docs/ --baseline main

# Compare against specific commit
tiresias review docs/ --baseline a3f2b1c4

# Compare with remote branch
tiresias review docs/ --baseline origin/main

# CI mode: fail only on new/worsened HIGH findings
tiresias review docs/ --baseline main --fail-on high
```

### What Gets Compared

Tiresias compares findings by rule ID and category:

- **New**: Findings present now but not in baseline
- **Worsened**: Findings with increased severity vs baseline
- **Unchanged**: Findings with same severity (hidden by default)
- **Improved**: Findings with decreased severity (hidden by default)

Only **new** and **worsened** findings are shown in text output and affect `--fail-on` logic.

### Maturity Regression Warning

If your document maturity score decreases vs baseline, Tiresias warns you:

```
⚠ Warning: Document maturity decreased vs baseline
  Baseline maturity: 45/100
  Current maturity: 38/100
```

### CI Integration Example

```yaml
name: Design Review

on:
  pull_request:
    paths:
      - 'docs/**'

jobs:
  tiresias:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Need full history for baseline

      - uses: astral-sh/setup-uv@v5

      - run: uv sync

      - name: Review with baseline
        run: |
          uv run tiresias review docs/ \
            --baseline origin/main \
            --fail-on high \
            --format json \
            --output review.json

      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: tiresias-baseline-report
          path: review.json
```

### Notes

- Baseline mode requires files to be in a git repository
- If no matching files exist at baseline ref, all findings are treated as "new"
- JSON output includes full comparison details for CI/CD integration

---

## Configuration File

Create a `.tiresias.yml` file in your repo root:

```yaml
default_profile: general

ignore_paths:
  - "test/**"
  - "drafts/**"

redact_patterns:
  - "internal-key-\\w+"

category_weights:
  security: 1.5
  reliability: 1.2
  documentation: 0.5
```

---

## Suppressing Findings

Tiresias supports **finding suppressions** for accepted risks or false positives. Suppressions require documented justification and can be scoped by file, profile, or severity.

### Basic Suppression

Add suppressions to your `.tiresias.yml`:

```yaml
suppressions:
  - id: REQ-001
    reason: Success metrics tracked in external dashboard (see METRICS.md)

  - id: ARCH-001
    reason: Error handling delegated to API gateway layer
```

**Important**: Every suppression requires a `reason` field explaining the decision. This ensures suppressions are intentional and documented.

### Time-Limited Suppressions

Set an expiry date to create temporary suppressions:

```yaml
suppressions:
  - id: OPS-001
    reason: Rollout plan deferred until Q2 beta launch
    expires: 2026-06-30
```

When suppressions expire:
- They stop suppressing findings (findings reappear)
- Tiresias displays a warning with the expired suppression details
- You should update or remove expired entries from `.tiresias.yml`

### Scoped Suppressions

Suppress findings only for specific files, profiles, or severity levels:

```yaml
suppressions:
  # Only suppress in draft documents
  - id: REQ-001
    reason: Early brainstorm, metrics TBD
    scope: ["drafts/**/*.md"]

  # Only suppress for security profile
  - id: PERF-001
    reason: Performance not critical for security reviews
    profiles: ["security"]

  # Only suppress high-severity instances
  - id: TEST-001
    reason: High-severity test gap accepted for MVP
    severities: ["high"]

  # Combine filters (all must match)
  - id: DOC-001
    reason: Internal docs don't need changelog
    scope: ["internal/**"]
    profiles: ["general"]
    severities: ["low", "medium"]
```

**Scope patterns**: Use glob patterns like `*.md`, `docs/**/*.md`, or `design/*.txt`

**Profiles**: `general`, `security`, `performance`, `reliability`

**Severities**: `high`, `medium`, `low`

### Viewing Suppressed Findings

By default, suppressed findings are hidden. Use `--show-suppressed` to display them:

```bash
tiresias review docs/ --show-suppressed
```

Suppressed findings are marked with `[SUPPRESSED]` in the output.

### Suppression Summary

When findings are suppressed, Tiresias displays a summary:

```
┌─────────────────────────────────────────────────────┐
│ Suppressed Findings                                  │
│                                                      │
│ Total suppressed: 3                                 │
│   • High: 1                                         │
│   • Medium: 2                                       │
│   • Low: 0                                          │
│                                                      │
│ Use --show-suppressed to display them.              │
└─────────────────────────────────────────────────────┘
```

### JSON Output

Suppressed findings are always included in JSON output with `suppressed: true` and full suppression metadata:

```json
{
  "findings": [
    {
      "id": "REQ-001",
      "title": "Missing success metrics",
      "severity": "high",
      "suppressed": true,
      "suppression": {
        "reason": "Metrics tracked externally",
        "expires": "2026-12-31",
        "scope": ["docs/**"],
        "profiles": ["general"],
        "severities": ["high"]
      }
    }
  ]
}
```

### Best Practices

- **Document the "why"**: Explain the decision, don't just restate the finding
- **Link to context**: Reference tickets, docs, or decisions (e.g., "See ADR-042")
- **Use expiry dates**: For time-limited decisions or deferred work
- **Scope narrowly**: Use file patterns to avoid over-suppression
- **Review regularly**: Expired suppressions indicate decisions to revisit

---

## LLM Evidence Enrichment (Optional)

Tiresias supports **optional LLM-powered evidence enrichment** to improve finding quality. When enabled, an LLM analyzes your document and enhances evidence with direct quotes and tailored recommendations.

### Key Principles

- **Opt-in only**: LLM enrichment is disabled by default
- **Augmentation, not replacement**: Heuristic analysis remains the source of truth
- **Graceful degradation**: If LLM fails, falls back to heuristic evidence
- **Cost control**: Configurable caps on enrichments per run
- **Never blocks CI/CD**: Failures log warnings but don't fail the review

### Configuration

Add LLM config to your `.tiresias.yml`:

**Anthropic (Claude):**

```yaml
llm_config:
  enabled: true
  provider: anthropic
  model: claude-sonnet-4-5
  api_key_env: ANTHROPIC_API_KEY
  temperature: 0.3
  max_tokens: 2000
  timeout_seconds: 30
  max_retries: 2
  max_enrichments_per_run: 10  # Cost control: max findings to enrich
```

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

**OpenAI (GPT):**

```yaml
llm_config:
  enabled: true
  provider: openai
  model: gpt-4o
  api_key_env: OPENAI_API_KEY
  temperature: 0.3
  max_tokens: 2000
  timeout_seconds: 30
  max_retries: 2
  max_enrichments_per_run: 10
```

```bash
export OPENAI_API_KEY=sk-...
```

### Usage

Enable via CLI flag:

```bash
tiresias review docs/design.md --enable-llm
```

Or enable in config (applies to all reviews):

```yaml
llm_config:
  enabled: true
```

### How It Works

1. **Heuristic analysis runs first** (deterministic, fast)
2. **LLM enrichment layer** (optional, if enabled):
   - Prioritizes HIGH severity findings first
   - Enriches up to `max_enrichments_per_run` findings
   - Extracts direct quotes as evidence
   - Provides tailored recommendations
   - Skips already-enriched findings (immutability)
3. **Original findings preserved** if LLM fails

### Output

Enriched findings include an LLM banner:

```
✨ LLM Evidence Enrichment: anthropic (claude-sonnet-4-5) — 8/10 succeeded
```

JSON output includes enrichment metadata:

```json
{
  "metadata": {
    "llm_enrichment_enabled": true,
    "llm_provider": "anthropic",
    "llm_model": "claude-sonnet-4-5",
    "llm_enrichments_attempted": 10,
    "llm_enrichments_succeeded": 8,
    "llm_enrichments_failed": 2
  },
  "findings": [
    {
      "id": "REQ-001",
      "enriched_by_llm": true,
      "evidence": "The document states: 'We will track adoption metrics'...",
      "recommendation": "Add a dedicated Success Metrics section..."
    }
  ]
}
```

### Cost Control

Enrichment is capped by:
- **Document size**: Max 100,000 characters (~25k tokens)
- **Per-run cap**: Max `max_enrichments_per_run` findings (default 10)
- **Priority**: HIGH severity enriched first, then MEDIUM, then LOW

### Best Practices

- **Start with small documents**: Test with 1-2 page docs first
- **Monitor costs**: Check `llm_enrichments_attempted` in JSON output
- **Use in CI sparingly**: Enable only for key documents or PRs
- **Set conservative caps**: Start with `max_enrichments_per_run: 5`
- **Review enrichments**: LLM evidence is better but not perfect

### Supported Providers

- **Anthropic** (Claude): `claude-sonnet-4-5`, `claude-opus-4-5`, etc.
- **OpenAI** (GPT): `gpt-4o`, `gpt-4-turbo`, `gpt-4`, etc.

---

## JSON Output Schema (Example)

```json
{
  "metadata": {
    "tool_version": "X.Y.Z",
    "profile": "general",
    "model_provider": "heuristic"
  },
  "risk_score": 45,
  "findings": []
}
```

---

## GitHub Action Integration

```yaml
name: Design Review

on:
  pull_request:
    paths:
      - 'docs/**'
      - '**.md'

jobs:
  tiresias:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - run: uv sync
      - run: uv run tiresias review docs/ --fail-on high
```

---

## What Tiresias Checks (MVP)

* Requirements
* Architecture
* Testing
* Operations
* Security
* Performance
* Documentation

---

## Roadmap

* [x] Deterministic heuristic analysis
* [x] CLI with Rich output
* [x] JSON export for CI/CD
* [ ] LLM-assisted analysis (optional, opt-in)
* [ ] Custom rule plugins
* [ ] VS Code extension
* [ ] Interactive review mode

---

## Why “Tiresias”?

In Greek mythology, Tiresias was a blind prophet known for wisdom and foresight. This tool aims to provide foresight into design failures *before* they reach production.

---

## License

MIT License

---

## Contributing

1. Fork the repo
2. Create a feature branch
3. Commit your changes
4. Open a Pull Request

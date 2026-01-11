# Tiresias

**Design review and pre-mortem analysis for engineering artifacts.**

Tiresias performs automated design reviews on your engineering documents (design docs, ADRs, specs, prompts) to identify missing considerations, risks, and potential failure modes before implementation. Think of it as a pre-mortem tool that catches issues early in the design phase.

## Features

- Analyzes markdown, text, JSON, and YAML files for common design gaps
- Identifies missing: error handling, success metrics, test strategies, rollout plans, and more
- Configurable analysis profiles (general, security, performance, reliability)
- Beautiful terminal output with risk scoring
- Machine-readable JSON output for CI/CD integration
- GitHub Action support for automated PR reviews
- Secret redaction for safe analysis

## Installation

### Using uv (recommended)

```bash
# Clone and install
git clone https://github.com/yourusername/tiresias.git
cd tiresias
uv sync

# Run directly
uv run tiresias review docs/design.md
```

### As a tool

```bash
# Install as a uv tool (when published)
uv tool install tiresias

# Run
tiresias review docs/design.md
```

## Quick Start

```bash
# Review a single file
tiresias review docs/design.md

# Review a directory
tiresias review docs/

# Output JSON for parsing
tiresias review docs/ --format json --output report.json

# Security-focused review
tiresias review specs/ --profile security

# Fail CI if high-severity issues found
tiresias review docs/ --fail-on high
```

## CLI Usage

```
tiresias review <PATH_OR_GLOB> [OPTIONS]
```

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--format` | `text` | Output format: `text` or `json` |
| `--severity-threshold` | `low` | Min severity to display: `low`, `med`, `high` |
| `--fail-on` | `none` | Exit nonzero if findings ≥ severity: `none`, `med`, `high` |
| `--max-chars` | `200000` | Max characters per file (truncates safely) |
| `--redact` | (auto) | Additional regex patterns to redact (repeatable) |
| `--profile` | `general` | Analysis profile: `general`, `security`, `performance`, `reliability` |
| `--output` | (stdout) | Write output to file |
| `--no-color` | `false` | Disable color output |

### Examples

```bash
# Review with custom redaction
tiresias review design.md --redact 'internal-api-\w+'

# High-severity only, JSON output
tiresias review docs/ --severity-threshold high --format json

# Performance-focused review
tiresias review architecture.md --profile performance

# CI mode: fail on medium+ issues
tiresias review specs/ --fail-on med --no-color
```

## Configuration File

Create a `.tiresias.yml` in your repo root to customize behavior:

```yaml
# Default analysis profile
default_profile: general

# Ignore certain files/directories
ignore_paths:
  - "test/**"
  - "*.tmp.md"
  - "drafts/**"

# Additional secret patterns to redact
redact_patterns:
  - "internal-key-\\w+"
  - "project-secret-[a-z0-9]+"

# Customize risk scoring weights
category_weights:
  requirements: 1.0
  architecture: 1.0
  testing: 1.0
  operations: 1.0
  security: 1.5      # Security issues weighted higher
  performance: 0.8
  reliability: 1.2
  documentation: 0.5
```

## JSON Output Schema

```json
{
  "metadata": {
    "tool_version": "0.1.0",
    "timestamp": "2024-01-15T10:30:00Z",
    "input_files": ["docs/design.md"],
    "profile": "general",
    "model_provider": "heuristic",
    "elapsed_ms": 45
  },
  "findings": [
    {
      "id": "ARCH-001",
      "title": "Missing error handling strategy",
      "severity": "high",
      "category": "architecture",
      "evidence": "No discussion of error handling...",
      "impact": "System may fail ungracefully...",
      "recommendation": "Document error scenarios..."
    }
  ],
  "assumptions": ["API supports 1000 rps"],
  "open_questions": ["What about rate limiting?"],
  "quick_summary": [
    "Analyzed 1 file(s)",
    "Found 3 high-severity issue(s)"
  ],
  "risk_score": 45,
  "risk_score_explanation": "Risk score: 45/100 (Medium)..."
}
```

## GitHub Action Integration

Add to `.github/workflows/design-review.yml`:

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
        with:
          version: "latest"

      - name: Install Tiresias
        run: uv sync

      - name: Run design review
        run: |
          uv run tiresias review docs/ \
            --format json \
            --output report.json \
            --fail-on high

      - name: Upload report
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: tiresias-report
          path: report.json
```

## What Tiresias Checks (MVP)

### Requirements
- **REQ-001**: Missing success metrics (high)
- **REQ-002**: Unclear scope/goals (medium)
- **REQ-003**: Missing non-functional requirements (medium)

### Architecture
- **ARCH-001**: Missing error handling strategy (high)
- **ARCH-002**: Unclear dependencies (medium)
- **ARCH-003**: Missing data retention/privacy plan (high)

### Testing
- **TEST-001**: Missing test strategy (medium)

### Operations
- **OPS-001**: Missing rollout/deployment plan (high)
- **OPS-002**: Unclear ownership (medium)

### Security
- **SEC-001**: Missing security considerations (high)

### Performance
- **PERF-001**: Missing performance targets (low)

### Documentation
- **DOC-001**: Missing decision rationale (low)

## Analysis Profiles

- **general**: All rules (comprehensive review)
- **security**: Focus on security, privacy, and ownership
- **performance**: Architecture, performance targets, testing
- **reliability**: Error handling, testing, operations, performance

## Development

```bash
# Clone repo
git clone https://github.com/yourusername/tiresias.git
cd tiresias

# Install dependencies
uv sync

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=src/tiresias --cov-report=term-missing

# Type check
uv run mypy src/tiresias

# Lint and format
uv run ruff check src/ tests/
uv run ruff format src/ tests/

# Run CLI locally
uv run tiresias review docs/example.md
```

## Roadmap

- [x] MVP heuristic analysis (12 rules)
- [x] CLI with Typer + Rich output
- [x] JSON export for CI/CD
- [x] Configuration file support
- [x] GitHub Action example
- [ ] LLM-based analysis (Claude/OpenAI integration)
- [ ] Custom rule plugins
- [ ] Interactive mode
- [ ] VS Code extension
- [ ] Multi-repo scanning

## Why "Tiresias"?

In Greek mythology, Tiresias was a blind prophet known for wisdom and foresight. This tool aims to provide foresight into potential design issues before they become production problems.

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions welcome! Please open an issue first to discuss major changes.

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Credits

Built with:
- [Typer](https://typer.tiangolo.com/) - CLI framework
- [Rich](https://rich.readthedocs.io/) - Terminal formatting
- [Pydantic](https://docs.pydantic.dev/) - Data validation
- [uv](https://docs.astral.sh/uv/) - Python package manager

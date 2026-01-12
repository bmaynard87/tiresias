"""Typer CLI application."""

import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

import typer

from tiresias import __version__
from tiresias.core.analyzer import HeuristicAnalyzer
from tiresias.core.config import load_config
from tiresias.core.file_loader import discover_files, load_file_content, redact_secrets
from tiresias.core.scoring import calculate_risk_score
from tiresias.renderers.json import render_json
from tiresias.renderers.text import render_text
from tiresias.schemas.report import Metadata, ReviewReport, Severity

app = typer.Typer(
    name="tiresias",
    help="Design review and pre-mortem analysis for engineering artifacts",
    add_completion=False,
)


@app.command(name="review")
def review_command(
    path_or_glob: Annotated[
        str,
        typer.Argument(
            help="File path, directory, or glob pattern to analyze",
        ),
    ],
    format: Annotated[
        str,
        typer.Option(
            "--format",
            "-f",
            help="Output format",
        ),
    ] = "text",
    severity_threshold: Annotated[
        str,
        typer.Option(
            "--severity-threshold",
            help="Minimum severity to display",
        ),
    ] = "low",
    fail_on: Annotated[
        str,
        typer.Option(
            "--fail-on",
            help="Exit with error if findings >= this severity",
        ),
    ] = "none",
    max_chars: Annotated[
        int,
        typer.Option(
            "--max-chars",
            help="Maximum characters per file",
        ),
    ] = 200000,
    redact: Annotated[
        list[str] | None,
        typer.Option(
            "--redact",
            help="Additional regex patterns to redact (repeatable)",
        ),
    ] = None,
    profile: Annotated[
        str,
        typer.Option(
            "--profile",
            help="Analysis profile",
        ),
    ] = "general",
    output: Annotated[
        Path | None,
        typer.Option(
            "--output",
            "-o",
            help="Write output to file instead of stdout",
        ),
    ] = None,
    no_color: Annotated[
        bool,
        typer.Option(
            "--no-color",
            help="Disable color output",
        ),
    ] = False,
    show_evidence: Annotated[
        bool,
        typer.Option(
            "--show-evidence",
            "--verbose",
            help="Show evidence for each finding in text output",
        ),
    ] = False,
) -> None:
    """
    Perform design review analysis on engineering artifacts.

    Analyzes markdown, text, JSON, and YAML files for common design issues,
    missing considerations, and risks.
    """
    start_time = time.time()

    # Validate options
    if format not in ("text", "json"):
        typer.echo("Error: --format must be 'text' or 'json'", err=True)
        raise typer.Exit(2)

    if severity_threshold not in ("low", "med", "high"):
        typer.echo(
            "Error: --severity-threshold must be 'low', 'med', or 'high'",
            err=True,
        )
        raise typer.Exit(2)

    if fail_on not in ("none", "med", "high"):
        typer.echo(
            "Error: --fail-on must be 'none', 'med', or 'high'",
            err=True,
        )
        raise typer.Exit(2)

    if profile not in ("general", "security", "performance", "reliability"):
        typer.echo(
            "Error: --profile must be 'general', 'security', 'performance', or 'reliability'",
            err=True,
        )
        raise typer.Exit(2)

    try:
        # Load configuration
        config = load_config()

        # Override profile if not explicitly set
        if profile == "general" and config.default_profile != "general":
            profile = config.default_profile

        # Discover files
        files = discover_files(path_or_glob, config.ignore_paths)

        if not files:
            typer.echo(
                f"Error: No supported files found at '{path_or_glob}'",
                err=True,
            )
            raise typer.Exit(3)

        # Load and analyze files
        all_content = []
        redact_patterns = config.redact_patterns + (redact or [])

        for file in files:
            content = load_file_content(file, max_chars)
            content = redact_secrets(content, redact_patterns)
            all_content.append(content)

        # Combine content for analysis
        combined_content = "\n\n---\n\n".join(all_content)

        # Run analysis
        analyzer = HeuristicAnalyzer()
        findings = analyzer.analyze(combined_content, profile)
        assumptions = analyzer.extract_assumptions(combined_content)
        questions = analyzer.extract_questions(combined_content)

        # Apply severity threshold filter
        threshold_map = {
            "low": [Severity.LOW, Severity.MEDIUM, Severity.HIGH],
            "med": [Severity.MEDIUM, Severity.HIGH],
            "high": [Severity.HIGH],
        }
        allowed_severities = threshold_map[severity_threshold]
        filtered_findings = [f for f in findings if f.severity in allowed_severities]

        # Calculate risk score
        risk_score, risk_explanation = calculate_risk_score(findings, config.category_weights)

        # Generate summary
        summary = _generate_summary(findings, files)

        # Calculate elapsed time
        elapsed_ms = int((time.time() - start_time) * 1000)

        # Build report
        report = ReviewReport(
            metadata=Metadata(
                tool_version=__version__,
                timestamp=datetime.now(UTC).isoformat(),
                input_files=[str(f) for f in files],
                profile=profile,
                model_provider="heuristic",
                elapsed_ms=elapsed_ms,
            ),
            findings=filtered_findings,
            assumptions=assumptions,
            open_questions=questions,
            quick_summary=summary,
            risk_score=risk_score,
            risk_score_explanation=risk_explanation,
        )

        # Render output
        if format == "json":
            output_text = render_json(report)
        else:
            output_text = render_text(report, no_color, show_evidence)

        # Write output
        if output:
            output.write_text(output_text, encoding="utf-8")
        else:
            typer.echo(output_text)

        # Check fail-on condition
        if fail_on != "none":
            has_critical = any(f.severity == Severity.HIGH for f in findings)
            has_medium = any(f.severity == Severity.MEDIUM for f in findings)

            should_fail = False
            if fail_on == "high" and has_critical:
                should_fail = True
            elif fail_on == "med" and (has_critical or has_medium):
                should_fail = True

            if should_fail:
                raise typer.Exit(1)

    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(3)


def _generate_summary(findings: list, files: list[Path]) -> list[str]:
    """Generate quick summary bullets."""
    summary = []

    # File count
    summary.append(f"Analyzed {len(files)} file(s)")

    # Finding counts
    high = sum(1 for f in findings if f.severity == Severity.HIGH)
    med = sum(1 for f in findings if f.severity == Severity.MEDIUM)
    low = sum(1 for f in findings if f.severity == Severity.LOW)

    if high:
        summary.append(f"Found {high} high-severity issue(s)")
    if med:
        summary.append(f"Found {med} medium-severity issue(s)")
    if low:
        summary.append(f"Found {low} low-severity issue(s)")

    if not findings:
        summary.append("No issues detected")

    # Top categories
    if findings:
        categories: dict[str, int] = {}
        for f in findings:
            cat = f.category.value
            categories[cat] = categories.get(cat, 0) + 1
        top_cat = max(categories.items(), key=lambda x: x[1])
        summary.append(f"Most issues in: {top_cat[0]}")

    return summary


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            "-v",
            help="Show version and exit",
        ),
    ] = False,
) -> None:
    """Tiresias: Design review and pre-mortem analysis tool."""
    if version:
        typer.echo(f"tiresias {__version__}")
        raise typer.Exit(0)

    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit(0)


if __name__ == "__main__":
    app()

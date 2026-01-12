"""Typer CLI application."""

import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, cast

import typer

from tiresias import __version__
from tiresias.core.analyzer import HeuristicAnalyzer, extract_sections
from tiresias.core.baseline import check_maturity_regression, compare_findings
from tiresias.core.config import load_config
from tiresias.core.file_loader import discover_files, load_file_content, redact_secrets
from tiresias.core.git_baseline import list_files_at_ref, load_file_at_ref, validate_git_ref
from tiresias.core.maturity import compute_maturity
from tiresias.core.rules import get_rule_by_id, list_rule_ids
from tiresias.core.scoring import calculate_risk_score
from tiresias.core.suppression import apply_suppressions
from tiresias.renderers.explain import render_explain_list, render_explain_text
from tiresias.renderers.json import render_json
from tiresias.renderers.text import render_text
from tiresias.schemas.explain import RuleExplanation, RuleList
from tiresias.schemas.report import (
    BaselineSummary,
    ComparisonResult,
    Finding,
    FindingChange,
    FindingComparison,
    Maturity,
    MaturityMetrics,
    Metadata,
    ReviewReport,
    Severity,
)

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
    baseline: Annotated[
        str | None,
        typer.Option(
            "--baseline",
            help="Git ref to use as baseline for comparison (e.g., main, origin/main, commit-sha)",
        ),
    ] = None,
    show_suppressed: Annotated[
        bool,
        typer.Option(
            "--show-suppressed",
            help="Show suppressed findings in output",
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

        # Baseline analysis (if provided)
        baseline_report: dict[str, str | int | list[Finding]] | None = None
        if baseline:
            try:
                # Validate git ref
                commit_sha = validate_git_ref(baseline)

                # Supported extensions for file discovery
                supported_exts = {".md", ".txt", ".json", ".yaml", ".yml"}

                # Load baseline files
                baseline_files = list_files_at_ref(baseline, path_or_glob, supported_exts)

                if not baseline_files:
                    typer.echo(
                        f"Warning: No files found at baseline ref '{baseline}'. "
                        "Treating as empty baseline.",
                        err=True,
                    )

                # Load baseline content
                baseline_contents = []
                redact_patterns = config.redact_patterns + (redact or [])
                for file in baseline_files:
                    content = load_file_at_ref(baseline, file, max_chars)
                    content = redact_secrets(content, redact_patterns)
                    baseline_contents.append(content)

                baseline_combined = "\n\n---\n\n".join(baseline_contents)
                baseline_sections = extract_sections(baseline_combined)

                # Run baseline analysis
                baseline_analyzer = HeuristicAnalyzer()
                baseline_findings = baseline_analyzer.analyze(
                    baseline_combined, profile, baseline_sections
                )
                baseline_maturity = compute_maturity(baseline_combined, baseline_sections)
                baseline_risk, _ = calculate_risk_score(baseline_findings, config.category_weights)

                # Store baseline report data
                baseline_report = {
                    "git_ref": baseline,
                    "commit_sha": commit_sha,
                    "findings": baseline_findings,
                    "maturity_score": baseline_maturity.score,
                    "risk_score": baseline_risk,
                }

            except ValueError as e:
                typer.echo(f"Error: Invalid baseline ref '{baseline}': {e}", err=True)
                raise typer.Exit(3)

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

        for file_path in files:
            content = load_file_content(file_path, max_chars)
            content = redact_secrets(content, redact_patterns)
            all_content.append(content)

        # Combine content for analysis
        combined_content = "\n\n---\n\n".join(all_content)

        # Extract sections once (used by analyzer and maturity computation)
        sections = extract_sections(combined_content)

        # Run analysis
        analyzer = HeuristicAnalyzer()
        findings = analyzer.analyze(combined_content, profile, sections)
        assumptions = analyzer.extract_assumptions(combined_content)
        questions = analyzer.extract_questions(combined_content)

        # Compute document maturity
        maturity_result = compute_maturity(combined_content, sections)

        # Apply suppressions
        suppression_result = apply_suppressions(
            findings=findings,
            config=config,
            profile=profile,
            input_files=[str(f) for f in files],
        )

        # Baseline comparison (if baseline provided)
        comparison_result = None
        # Default: visible findings only (unless --show-suppressed)
        if show_suppressed:
            displayed_findings = findings  # Show all with suppressed marked
        else:
            displayed_findings = suppression_result.visible_findings

        if baseline_report:
            new, worsened, unchanged, improved = compare_findings(
                findings,
                cast(list[Finding], baseline_report["findings"]),
            )

            # Filter to new + worsened only
            displayed_findings = new + [f for f, _ in worsened]

            # Recalculate risk score from displayed findings
            risk_score, risk_explanation = calculate_risk_score(
                displayed_findings,
                config.category_weights,
            )

            # Check maturity regression
            maturity_regressed = check_maturity_regression(
                maturity_result.score,
                cast(int, baseline_report["maturity_score"]),
            )

            # Build comparison result
            comparison_result = ComparisonResult(
                baseline_summary=BaselineSummary(
                    git_ref=cast(str, baseline_report["git_ref"]),
                    commit_sha=cast(str, baseline_report["commit_sha"]),
                    findings_count=len(cast(list[Finding], baseline_report["findings"])),
                    risk_score=cast(int, baseline_report["risk_score"]),
                    maturity_score=cast(int, baseline_report["maturity_score"]),
                ),
                new_findings=new,
                worsened_findings=[
                    FindingComparison(
                        finding=f,
                        change=FindingChange.WORSENED,
                        baseline_severity=bs,
                    )
                    for f, bs in worsened
                ],
                unchanged_findings=unchanged,
                improved_findings=[
                    FindingComparison(
                        finding=f,
                        change=FindingChange.IMPROVED,
                        baseline_severity=bs,
                    )
                    for f, bs in improved
                ],
                maturity_regressed=maturity_regressed,
            )

        # Apply severity threshold filter to displayed findings
        threshold_map = {
            "low": [Severity.LOW, Severity.MEDIUM, Severity.HIGH],
            "med": [Severity.MEDIUM, Severity.HIGH],
            "high": [Severity.HIGH],
        }
        allowed_severities = threshold_map[severity_threshold]
        filtered_findings = [f for f in displayed_findings if f.severity in allowed_severities]

        # Calculate risk score (if not already calculated in baseline mode)
        if not baseline_report:
            risk_score, risk_explanation = calculate_risk_score(findings, config.category_weights)

        # Generate summary (use displayed findings for baseline mode)
        summary = _generate_summary(displayed_findings, files)

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
            maturity=Maturity(
                level=maturity_result.level,
                score=maturity_result.score,
                confidence=maturity_result.confidence,
                interpretation=maturity_result.interpretation,
                signals=maturity_result.signals,
                metrics=MaturityMetrics(
                    char_count=maturity_result.metrics.char_count,
                    section_count=maturity_result.metrics.section_count,
                    core_sections_present=maturity_result.metrics.core_sections_present,
                    core_sections_found=maturity_result.metrics.core_sections_found,
                ),
            ),
            findings=filtered_findings,
            assumptions=assumptions,
            open_questions=questions,
            quick_summary=summary,
            risk_score=risk_score,
            risk_score_explanation=risk_explanation,
            baseline_ref=baseline if baseline else None,
            comparison=comparison_result,
            suppressed_summary=suppression_result.get_suppressed_summary(),
            expired_suppressions=suppression_result.expired_suppressions,
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

        # Check fail-on condition (ignore suppressed findings)
        if fail_on != "none":
            has_critical = any(
                f.severity == Severity.HIGH and not f.suppressed for f in displayed_findings
            )
            has_medium = any(
                f.severity == Severity.MEDIUM and not f.suppressed for f in displayed_findings
            )

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


@app.command(name="explain")
def explain_command(
    rule_id: Annotated[
        str | None,
        typer.Argument(
            help="Rule ID to explain (e.g., REQ-001)",
        ),
    ] = None,
    format: Annotated[
        str,
        typer.Option(
            "--format",
            "-f",
            help="Output format",
        ),
    ] = "text",
    list_rules: Annotated[
        bool,
        typer.Option(
            "--list",
            help="List all available rule IDs",
        ),
    ] = False,
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
) -> None:
    """
    Explain a specific rule and how to address it.

    Shows detailed information about what a rule checks, why it matters,
    and how to fix findings. Use --list to see all available rules.
    """
    # Validate format option
    if format not in ("text", "json"):
        typer.echo("Error: --format must be 'text' or 'json'", err=True)
        raise typer.Exit(2)

    try:
        # Handle --list flag
        if list_rules:
            rules = list_rule_ids()

            if format == "json":
                rule_list = RuleList(rules=[{"id": rid, "title": title} for rid, title in rules])
                output_text = rule_list.model_dump_json(indent=2)
            else:
                output_text = render_explain_list(rules, no_color)

            # Write output
            if output:
                output.write_text(output_text, encoding="utf-8")
            else:
                typer.echo(output_text)

            raise typer.Exit(0)

        # Require rule_id if not --list
        if rule_id is None:
            typer.echo(
                "Error: Must provide a rule ID or use --list flag\n\n"
                "Usage:\n"
                "  tiresias explain <RULE_ID>\n"
                "  tiresias explain --list",
                err=True,
            )
            raise typer.Exit(2)

        # Lookup rule
        rule = get_rule_by_id(rule_id)
        if rule is None:
            typer.echo(
                f"Error: Unknown rule ID '{rule_id}'\n\n"
                "Available rules can be listed with:\n"
                "  tiresias explain --list",
                err=True,
            )
            raise typer.Exit(3)

        # Render output
        if format == "json":
            explanation = RuleExplanation(
                id=rule.id,
                title=rule.title,
                severity=rule.severity.value,
                category=rule.category.value,
                checks=rule.evidence_template,
                why=rule.impact,
                how_to_fix=rule.recommendation,
                pitfalls=rule.pitfalls,
            )
            output_text = explanation.model_dump_json(indent=2)
        else:
            output_text = render_explain_text(rule, no_color)

        # Write output
        if output:
            output.write_text(output_text, encoding="utf-8")
        else:
            typer.echo(output_text)

    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(3)


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

"""Rich text output renderer."""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from tiresias.schemas.report import Finding, ReviewReport, Severity


def _extract_evidence_lines(finding: Finding) -> list[str]:
    """
    Extract evidence as a list of lines from a finding.

    Args:
        finding: Finding with evidence field

    Returns:
        List of evidence lines (sentences)
    """
    if not finding.evidence:
        return []

    # Split by newlines first, then by sentence-ending punctuation
    lines: list[str] = []
    for paragraph in finding.evidence.split("\n"):
        paragraph = paragraph.strip()
        if not paragraph:
            continue

        # Split into sentences (. ! ?)
        # Keep the punctuation with each sentence
        import re

        sentences = re.split(r"(?<=[.!?])\s+", paragraph)
        lines.extend(s.strip() for s in sentences if s.strip())

    return lines


def _truncate_evidence(lines: list[str], severity: Severity) -> list[str]:
    """
    Truncate evidence lines based on severity level.

    Args:
        lines: List of evidence lines
        severity: Finding severity (HIGH=unlimited, MEDIUM=2, LOW=1)

    Returns:
        Truncated list of evidence lines
    """
    if not lines:
        return []

    # Severity-based line limits
    if severity == Severity.HIGH:
        max_lines = None  # Unlimited
    elif severity == Severity.MEDIUM:
        max_lines = 2
    else:  # LOW
        max_lines = 1

    if max_lines is None:
        return lines

    if len(lines) <= max_lines:
        return lines

    # Truncate and add ellipsis to last line
    truncated = lines[:max_lines]
    if truncated:
        truncated[-1] = truncated[-1].rstrip() + "..."

    return truncated


def render_text(report: ReviewReport, no_color: bool = False, show_evidence: bool = False) -> str:
    """
    Render report as rich text for terminal.

    Args:
        report: Review report to render
        no_color: Disable color output
        show_evidence: Show evidence for each finding

    Returns:
        Formatted text output
    """
    console = Console(
        force_terminal=not no_color,
        force_interactive=False,
        color_system=None if no_color else "auto",
        width=100,
    )

    # Capture output to string
    with console.capture() as capture:
        _render_header(console, report)
        _render_maturity(console, report)
        _render_risk_score(console, report)
        _render_findings(console, report, show_evidence)
        _render_assumptions(console, report)
        _render_questions(console, report)
        _render_summary(console, report)

    return capture.get()


def _render_header(console: Console, report: ReviewReport) -> None:
    """Render header with metadata."""
    header_text = Text()
    header_text.append("Tiresias Design Review Report\n", style="bold cyan")
    header_text.append(f"Version: {report.metadata.tool_version}  ", style="dim")
    header_text.append(f"Profile: {report.metadata.profile}  ", style="dim")
    header_text.append(f"Files: {len(report.metadata.input_files)}  ", style="dim")
    header_text.append(f"Duration: {report.metadata.elapsed_ms}ms", style="dim")

    console.print(Panel(header_text, border_style="cyan"))
    console.print()


def _render_maturity(console: Console, report: ReviewReport) -> None:
    """Render document maturity assessment."""
    maturity = report.maturity

    # Determine color based on maturity level
    color_map = {
        "notes": "bright_black",
        "early_draft": "yellow",
        "design_spec": "blue",
        "production_ready": "green",
    }
    color = color_map.get(maturity.level, "white")

    # Format level name for display
    level_display = maturity.level.replace("_", " ").title()

    # Build maturity text
    maturity_text = Text()
    maturity_text.append(f"Level: {level_display}\n", style=f"bold {color}")
    maturity_text.append(f"Score: {maturity.score}/100\n\n", style="dim")
    maturity_text.append(f"{maturity.interpretation}\n\n", style="")
    maturity_text.append("Signals: ", style="dim")
    maturity_text.append(", ".join(maturity.signals), style="dim italic")

    console.print(Panel(maturity_text, title="Document Maturity", border_style=color))
    console.print()


def _render_risk_score(console: Console, report: ReviewReport) -> None:
    """Render risk score with gauge."""
    score = report.risk_score

    # Determine color
    if score <= 20:
        color = "green"
    elif score <= 50:
        color = "yellow"
    elif score <= 80:
        color = "red"
    else:
        color = "bright_red"

    # Create gauge (10 blocks)
    filled = int(score / 10)
    gauge = "▓" * filled + "░" * (10 - filled)

    score_text = Text()
    score_text.append("Risk Score: ", style="bold")
    score_text.append(f"{score}/100  ", style=f"bold {color}")
    score_text.append(f"[{gauge}]\n", style=color)
    score_text.append(report.risk_score_explanation, style="dim")

    # Add maturity context for early-stage documents
    if report.maturity.level in ("notes", "early_draft"):
        score_text.append("\n\n")
        score_text.append("Note: ", style="italic")
        level_name = report.maturity.level.replace("_", " ")
        score_text.append(
            f"High risk scores are typical for {level_name} documents.",
            style="dim italic",
        )

    console.print(Panel(score_text, title="Overall Risk", border_style=color))
    console.print()


def _render_findings(console: Console, report: ReviewReport, show_evidence: bool = False) -> None:
    """Render findings grouped by severity."""
    if not report.findings:
        console.print("[green]No findings detected![/green]\n")
        return

    # Group by severity
    high = [f for f in report.findings if f.severity == Severity.HIGH]
    medium = [f for f in report.findings if f.severity == Severity.MEDIUM]
    low = [f for f in report.findings if f.severity == Severity.LOW]

    if high:
        console.print("[bold red]High Severity Findings[/bold red]")
        _render_findings_table(console, high, "red", show_evidence)
        console.print()

    if medium:
        console.print("[bold yellow]Medium Severity Findings[/bold yellow]")
        _render_findings_table(console, medium, "yellow", show_evidence)
        console.print()

    if low:
        console.print("[bold blue]Low Severity Findings[/bold blue]")
        _render_findings_table(console, low, "blue", show_evidence)
        console.print()


def _render_findings_table(
    console: Console, findings: list, color: str, show_evidence: bool = False
) -> None:
    """Render a table of findings with optional evidence blocks."""
    table = Table(
        show_header=True,
        header_style=f"bold {color}",
        border_style=color,
        expand=True,
    )
    table.add_column("ID", style="dim", width=10)
    table.add_column("Title", style="bold", width=30)
    table.add_column("Category", width=15)
    table.add_column("Recommendation", width=40)

    for finding in findings:
        table.add_row(
            finding.id,
            finding.title,
            finding.category.value,
            finding.recommendation,
        )

    console.print(table)

    # Display evidence blocks under the table if requested
    if show_evidence:
        for finding in findings:
            evidence_lines = _extract_evidence_lines(finding)
            if not evidence_lines:
                continue

            # Truncate based on severity
            truncated_lines = _truncate_evidence(evidence_lines, finding.severity)

            if truncated_lines:
                # Print evidence block with indentation
                console.print()  # Blank line before evidence
                evidence_text = Text()
                evidence_text.append(f"  {finding.id} Evidence:", style="dim italic")
                console.print(evidence_text)

                for line in truncated_lines:
                    bullet_text = Text()
                    bullet_text.append(f"    • {line}", style="dim")
                    console.print(bullet_text)


def _render_assumptions(console: Console, report: ReviewReport) -> None:
    """Render identified assumptions."""
    if not report.assumptions:
        return

    console.print("[bold]Identified Assumptions[/bold]")
    for i, assumption in enumerate(report.assumptions, 1):
        console.print(f"  {i}. {assumption}")
    console.print()


def _render_questions(console: Console, report: ReviewReport) -> None:
    """Render open questions."""
    if not report.open_questions:
        return

    console.print("[bold]Open Questions[/bold]")
    for i, question in enumerate(report.open_questions, 1):
        console.print(f"  {i}. {question}")
    console.print()


def _render_summary(console: Console, report: ReviewReport) -> None:
    """Render quick summary."""
    if not report.quick_summary:
        return

    summary_text = Text()
    summary_text.append("Quick Summary\n\n", style="bold")
    for bullet in report.quick_summary:
        summary_text.append(f"• {bullet}\n")

    console.print(Panel(summary_text, border_style="blue"))

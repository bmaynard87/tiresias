"""Rich text output renderer."""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from tiresias.schemas.report import ReviewReport, Severity


def render_text(report: ReviewReport, no_color: bool = False) -> str:
    """
    Render report as rich text for terminal.

    Args:
        report: Review report to render
        no_color: Disable color output

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
        _render_risk_score(console, report)
        _render_findings(console, report)
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
    header_text.append(
        f"Files: {len(report.metadata.input_files)}  ", style="dim"
    )
    header_text.append(
        f"Duration: {report.metadata.elapsed_ms}ms", style="dim"
    )

    console.print(Panel(header_text, border_style="cyan"))
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

    console.print(Panel(score_text, title="Overall Risk", border_style=color))
    console.print()


def _render_findings(console: Console, report: ReviewReport) -> None:
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
        _render_findings_table(console, high, "red")
        console.print()

    if medium:
        console.print("[bold yellow]Medium Severity Findings[/bold yellow]")
        _render_findings_table(console, medium, "yellow")
        console.print()

    if low:
        console.print("[bold blue]Low Severity Findings[/bold blue]")
        _render_findings_table(console, low, "blue")
        console.print()


def _render_findings_table(
    console: Console, findings: list, color: str
) -> None:
    """Render a table of findings."""
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

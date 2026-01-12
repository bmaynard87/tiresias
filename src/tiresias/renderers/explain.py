"""Rendering functions for explain command output."""

from io import StringIO

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from tiresias.core.rules import AnalysisRule


def render_explain_text(rule: AnalysisRule, no_color: bool = False) -> str:
    """
    Render rule explanation as rich text.

    Args:
        rule: The rule to explain
        no_color: Disable color output

    Returns:
        Formatted text output
    """
    output = StringIO()
    console = Console(file=output, force_terminal=not no_color, width=80)

    # Title panel
    title = f"{rule.id}: {rule.title}"
    panel = Panel(title, style="bold cyan" if not no_color else "")
    console.print(panel)
    console.print()

    # Category and Severity
    console.print(f"Category: {rule.category.value.title()}")
    console.print(f"Severity: {rule.severity.value.title()}")
    console.print()

    # What it checks
    console.print("[bold]What it checks:[/bold]" if not no_color else "What it checks:")
    console.print(f"  {rule.evidence_template}")
    console.print()

    # Why it matters
    console.print("[bold]Why it matters:[/bold]" if not no_color else "Why it matters:")
    console.print(f"  {rule.impact}")
    console.print()

    # How to address it
    console.print("[bold]How to address it:[/bold]" if not no_color else "How to address it:")
    console.print(f"  {rule.recommendation}")
    console.print()

    # Common pitfalls (optional)
    if rule.pitfalls:
        console.print("[bold]Common pitfalls:[/bold]" if not no_color else "Common pitfalls:")
        console.print(f"  {rule.pitfalls}")
    else:
        console.print("[bold]Common pitfalls:[/bold]" if not no_color else "Common pitfalls:")
        console.print("  (None specified)")

    return output.getvalue()


def render_explain_list(rules: list[tuple[str, str]], no_color: bool = False) -> str:
    """
    Render list of all rules with IDs and titles.

    Args:
        rules: List of (id, title) tuples
        no_color: Disable color output

    Returns:
        Formatted table output
    """
    output = StringIO()
    console = Console(file=output, force_terminal=not no_color, width=80)

    console.print("Available Rules")
    console.print()

    # Create table
    table = Table(show_header=True, header_style="bold" if not no_color else "")
    table.add_column("Rule ID", style="cyan" if not no_color else "")
    table.add_column("Title")

    for rule_id, title in rules:
        table.add_row(rule_id, title)

    console.print(table)
    console.print()
    console.print("Use: tiresias explain <RULE_ID>")

    return output.getvalue()

"""JSON output renderer."""

from tiresias.schemas.report import ReviewReport


def render_json(report: ReviewReport) -> str:
    """
    Render report as JSON.

    Args:
        report: Review report to render

    Returns:
        JSON string (deterministic, sorted keys, indented)
    """
    return report.model_dump_json(
        indent=2,
        exclude_none=True,
        by_alias=False,
    )

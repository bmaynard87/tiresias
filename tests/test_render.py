from tiresias.render import render_review_md


def test_render_includes_overall_risk() -> None:
    md = render_review_md(
        {
            "overall_risk": "high",
            "summary": "Summary.",
            "findings": [
                {
                    "title": "A finding title",
                    "severity": "high",
                    "description": "Desc",
                    "recommendation": "Rec",
                }
            ],
        }
    )
    assert "Overall Risk" in md


def test_render_includes_finding_title() -> None:
    md = render_review_md(
        {
            "overall_risk": "low",
            "summary": "Summary.",
            "findings": [
                {
                    "title": "Unique Finding Title",
                    "severity": "low",
                    "description": "Desc",
                    "recommendation": "Rec",
                }
            ],
        }
    )
    assert "Unique Finding Title" in md

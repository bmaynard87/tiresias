from tiresias.gating import risk_at_or_above, should_fail


def test_risk_at_or_above_high_high() -> None:
    assert risk_at_or_above("high", "high") is True


def test_risk_at_or_above_medium_high() -> None:
    assert risk_at_or_above("medium", "high") is False


def test_risk_at_or_above_critical_high() -> None:
    assert risk_at_or_above("critical", "high") is True


def test_should_fail_false_when_below_threshold() -> None:
    review = {"overall_risk": "high", "summary": "s", "findings": [{"title": "t", "severity": "high", "description": "d", "recommendation": "r"}]}
    assert should_fail(review, "critical") is False


def test_should_fail_true_when_at_or_above_threshold() -> None:
    review = {"overall_risk": "high", "summary": "s", "findings": [{"title": "t", "severity": "high", "description": "d", "recommendation": "r"}]}
    assert should_fail(review, "low") is True

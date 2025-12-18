from tiresias.gating import risk_at_or_above


def test_risk_at_or_above_high_high() -> None:
    assert risk_at_or_above("high", "high") is True


def test_risk_at_or_above_medium_high() -> None:
    assert risk_at_or_above("medium", "high") is False


def test_risk_at_or_above_critical_high() -> None:
    assert risk_at_or_above("critical", "high") is True

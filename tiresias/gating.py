from __future__ import annotations

from typing import Any, Mapping


_RISK_ORDER = ["low", "medium", "high", "critical"]


def _normalize_risk(value: str) -> str:
    if not isinstance(value, str):
        raise TypeError("risk values must be strings")
    normalized = value.strip().lower()
    if normalized not in _RISK_ORDER:
        raise ValueError(f"unknown risk level: {value!r}")
    return normalized


def risk_at_or_above(risk: str, threshold: str) -> bool:
    """Return True when risk severity is >= threshold severity."""

    risk_norm = _normalize_risk(risk)
    threshold_norm = _normalize_risk(threshold)
    return _RISK_ORDER.index(risk_norm) >= _RISK_ORDER.index(threshold_norm)


def should_fail(review: Mapping[str, Any], threshold: str) -> bool:
    """Return True when Tiresias should exit with a failure code.

    PR1: Centralize the decision through this single function.
    V1 behavior gates only on overall risk vs. a threshold.
    """

    risk = str(review.get("overall_risk", "")).strip().lower()
    return risk_at_or_above(risk, threshold)

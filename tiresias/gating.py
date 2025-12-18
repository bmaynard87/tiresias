from __future__ import annotations

from typing import Iterable


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


def should_fail(blockers: int | Iterable[object], threshold: str) -> bool:
    """Return True when execution should fail.

    V1 interpretation: any blockers are a failure regardless of threshold.
    `threshold` is accepted for a stable signature even if unused in V1.
    """

    _ = threshold  # kept for interface stability
    if isinstance(blockers, int):
        return blockers > 0
    return any(True for _item in blockers)

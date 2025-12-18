import json

import pytest
from jsonschema import ValidationError, validate

from tiresias.schemas import REVIEW_SCHEMA


def test_valid_review_passes(fixtures_dir):
    payload = json.loads((fixtures_dir / "valid_review.json").read_text(encoding="utf-8"))
    validate(instance=payload, schema=REVIEW_SCHEMA)


def test_invalid_review_fails(fixtures_dir):
    payload = json.loads((fixtures_dir / "invalid_review.json").read_text(encoding="utf-8"))
    with pytest.raises(ValidationError):
        validate(instance=payload, schema=REVIEW_SCHEMA)


def test_valid_review_with_blocker_passes(fixtures_dir):
    payload = json.loads(
        (fixtures_dir / "valid_review_with_blocker.json").read_text(encoding="utf-8")
    )
    validate(instance=payload, schema=REVIEW_SCHEMA)


def test_valid_review_without_blockers_field_passes():
    payload = {
        "overall_risk": "low",
        "summary": "A valid payload without blockers.",
        "findings": [
            {
                "title": "All good",
                "severity": "info",
                "description": "No blockers field present.",
                "recommendation": "Keep it up.",
            }
        ],
    }
    validate(instance=payload, schema=REVIEW_SCHEMA)

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

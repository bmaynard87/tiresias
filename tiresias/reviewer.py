from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from jsonschema import ValidationError, validate

from .providers.base import Provider
from .schemas import REVIEW_SCHEMA


class ReviewValidationError(ValueError):
    pass


@dataclass(frozen=True)
class Reviewer:
    provider: Provider

    def review_markdown(self, markdown: str) -> Dict[str, Any]:
        payload = self.provider.review(markdown)
        try:
            validate(instance=payload, schema=REVIEW_SCHEMA)
        except ValidationError as exc:
            raise ReviewValidationError(str(exc)) from exc
        return payload

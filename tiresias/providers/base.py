from __future__ import annotations

from typing import Any, Dict, Protocol


class Provider(Protocol):
    """Provider interface for producing structured review payloads.

    Implementations must be deterministic for a given input.
    """

    def review(self, markdown: str) -> Dict[str, Any]:
        ...

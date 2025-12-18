from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


@dataclass(frozen=True)
class TiresiasConfig:
    provider: str = "openai"


def load_config(path: Optional[Path]) -> TiresiasConfig:
    if path is None:
        return TiresiasConfig()

    if not path.exists():
        return TiresiasConfig()

    data: Dict[str, Any] = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    provider = str(data.get("provider", "openai")).strip() or "openai"
    return TiresiasConfig(provider=provider)

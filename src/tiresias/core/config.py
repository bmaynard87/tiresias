"""Configuration loader for .tiresias.yml."""

from pathlib import Path

import yaml

from tiresias.schemas.config import TiresiasConfig


def load_config(start_path: Path | None = None) -> TiresiasConfig:
    """
    Load .tiresias.yml configuration file.

    Searches for .tiresias.yml in:
    1. Current directory (start_path)
    2. Parent directories up to root
    3. Git repository root (if in a git repo)

    Falls back to defaults if no config file is found.

    Args:
        start_path: Starting directory for search (defaults to cwd)

    Returns:
        TiresiasConfig with merged settings
    """
    if start_path is None:
        start_path = Path.cwd()

    config_name = ".tiresias.yml"

    # Search upward from start_path
    current = start_path.resolve()
    for parent in [current, *current.parents]:
        config_file = parent / config_name
        if config_file.exists():
            return _load_config_file(config_file)

    # No config found, use defaults
    return TiresiasConfig()


def _load_config_file(config_path: Path) -> TiresiasConfig:
    """Load and parse a config file."""
    try:
        with config_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        # Merge category_weights with defaults instead of replacing
        if "category_weights" in data:
            defaults = TiresiasConfig()
            merged_weights = defaults.category_weights.copy()
            merged_weights.update(data["category_weights"])
            data["category_weights"] = merged_weights

        return TiresiasConfig(**data)
    except Exception as e:
        # If config is malformed, warn but continue with defaults
        # In production, you might want to log this
        import sys
        print(f"Config error: {e}", file=sys.stderr)
        return TiresiasConfig()

"""Tests for configuration loading."""

from pathlib import Path

from tiresias.core.config import load_config
from tiresias.schemas.config import TiresiasConfig


def test_load_config_defaults_when_no_file() -> None:
    """Test that defaults are used when no config file exists."""
    config = load_config()

    assert isinstance(config, TiresiasConfig)
    assert config.default_profile == "general"
    assert config.ignore_paths == []
    assert config.category_weights["security"] == 1.5


def test_load_config_from_file(tmp_path: Path) -> None:
    """Test loading config from .tiresias.yml."""
    config_file = tmp_path / ".tiresias.yml"
    config_file.write_text(
        """
default_profile: security
ignore_paths:
  - "test/**"
  - "*.tmp"
redact_patterns:
  - 'custom-secret-\\w+'
category_weights:
  security: 2.0
  documentation: 0.3
"""
    )

    config = load_config(tmp_path)

    assert config.default_profile == "security"
    assert "test/**" in config.ignore_paths
    assert "custom-secret-\\w+" in config.redact_patterns
    assert config.category_weights["security"] == 2.0
    assert config.category_weights["documentation"] == 0.3


def test_load_config_searches_parent_dirs(tmp_path: Path) -> None:
    """Test that config search walks up parent directories."""
    # Create config in parent
    config_file = tmp_path / ".tiresias.yml"
    config_file.write_text("default_profile: performance\n")

    # Search from subdirectory
    subdir = tmp_path / "sub" / "dir"
    subdir.mkdir(parents=True)

    config = load_config(subdir)

    assert config.default_profile == "performance"


def test_load_config_malformed_uses_defaults(tmp_path: Path) -> None:
    """Test that malformed config falls back to defaults."""
    config_file = tmp_path / ".tiresias.yml"
    config_file.write_text("this is not valid yaml: [[[")

    config = load_config(tmp_path)

    # Should use defaults without crashing
    assert config.default_profile == "general"

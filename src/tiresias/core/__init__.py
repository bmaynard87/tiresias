"""Core analysis engine for Tiresias."""

from tiresias.core.analyzer import HeuristicAnalyzer
from tiresias.core.config import load_config
from tiresias.core.file_loader import discover_files, load_file_content, redact_secrets
from tiresias.core.scoring import calculate_risk_score

__all__ = [
    "HeuristicAnalyzer",
    "load_config",
    "discover_files",
    "load_file_content",
    "redact_secrets",
    "calculate_risk_score",
]

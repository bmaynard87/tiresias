"""Core analysis engine for Tiresias."""

from tiresias.core.analyzer import HeuristicAnalyzer
from tiresias.core.baseline import FindingKey, check_maturity_regression, compare_findings
from tiresias.core.config import load_config
from tiresias.core.file_loader import discover_files, load_file_content, redact_secrets
from tiresias.core.git_baseline import list_files_at_ref, load_file_at_ref, validate_git_ref
from tiresias.core.rules import get_all_rules, get_rule_by_id, list_rule_ids
from tiresias.core.scoring import calculate_risk_score

__all__ = [
    "HeuristicAnalyzer",
    "load_config",
    "discover_files",
    "load_file_content",
    "redact_secrets",
    "calculate_risk_score",
    "get_all_rules",
    "get_rule_by_id",
    "list_rule_ids",
    "validate_git_ref",
    "list_files_at_ref",
    "load_file_at_ref",
    "compare_findings",
    "check_maturity_regression",
    "FindingKey",
]

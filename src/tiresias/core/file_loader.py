"""File discovery and content loading utilities."""

import re
from pathlib import Path


def discover_files(
    path_or_glob: str,
    ignore_paths: list[str] | None = None,
) -> list[Path]:
    """
    Discover files matching the given path or glob pattern.

    Args:
        path_or_glob: File path, directory, or glob pattern
        ignore_paths: List of glob patterns to ignore

    Returns:
        Sorted list of file paths
    """
    ignore_patterns = ignore_paths or []
    path = Path(path_or_glob)

    # Supported extensions
    supported_exts = {".md", ".txt", ".json", ".yaml", ".yml"}

    found_files: list[Path] = []

    if path.is_file():
        # Single file
        if path.suffix.lower() in supported_exts:
            found_files = [path]
    elif path.is_dir():
        # Directory - recursively find supported files
        for ext in supported_exts:
            found_files.extend(path.rglob(f"*{ext}"))
    else:
        # Glob pattern
        cwd = Path.cwd()
        found_files = list(cwd.glob(path_or_glob))
        # Filter to supported extensions
        found_files = [f for f in found_files if f.suffix.lower() in supported_exts]

    # Apply ignore patterns
    if ignore_patterns:
        filtered_files = []
        for file in found_files:
            should_ignore = False
            for pattern in ignore_patterns:
                if file.match(pattern):
                    should_ignore = True
                    break
            if not should_ignore:
                filtered_files.append(file)
        found_files = filtered_files

    # Return sorted for determinism
    return sorted(set(found_files))


def load_file_content(file_path: Path, max_chars: int = 200000) -> str:
    """
    Load file content with size limit.

    Args:
        file_path: Path to file
        max_chars: Maximum characters to read per file

    Returns:
        File content (truncated if necessary)
    """
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        # If file can't be read, return empty
        return ""

    if len(content) > max_chars:
        content = content[:max_chars] + "\n\n... (truncated due to size limit)"

    return content


def redact_secrets(content: str, custom_patterns: list[str] | None = None) -> str:
    """
    Redact potential secrets from content.

    Args:
        content: Text content
        custom_patterns: Additional regex patterns to redact

    Returns:
        Content with secrets replaced by ***REDACTED***
    """
    # Default patterns for common secret formats
    default_patterns = [
        r"(api[_-]?key|token|secret|password)\s*[:=]\s*['\"]?[\w\-]{8,}['\"]?",
        r"(bearer|basic)\s+[\w\-\.=]+",
        r"['\"][A-Za-z0-9+/]{40,}={0,2}['\"]",  # Base64-like strings
    ]

    patterns = default_patterns + (custom_patterns or [])

    redacted = content
    for pattern in patterns:
        redacted = re.sub(
            pattern,
            "***REDACTED***",
            redacted,
            flags=re.IGNORECASE,
        )

    return redacted

"""Git operations for baseline comparison."""

import subprocess
from pathlib import Path


def validate_git_ref(ref: str) -> str:
    """
    Validate git ref exists and resolve to commit SHA.

    Args:
        ref: Git reference (branch, tag, commit)

    Returns:
        Resolved commit SHA

    Raises:
        ValueError: If ref is invalid or not in a git repository
    """
    # Check if in git repo
    result = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        raise ValueError("Not in a git repository")

    # Resolve ref to SHA
    result = subprocess.run(
        ["git", "rev-parse", ref],
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        raise ValueError(f"reference not found: {ref}")

    return result.stdout.strip()


def list_files_at_ref(
    ref: str,
    path_or_glob: str,
    supported_exts: set[str],
) -> list[str]:
    """
    List files at a git ref matching path/glob.

    Args:
        ref: Git reference
        path_or_glob: File path, directory, or glob pattern
        supported_exts: Set of supported extensions (e.g., {'.md', '.txt'})

    Returns:
        List of relative file paths at the ref
    """
    path = Path(path_or_glob)

    # Build git ls-tree command
    if path.is_dir() or not path.exists():
        # Directory or glob - list all files under path
        git_path = str(path) if path.exists() else "."
    else:
        # Single file
        git_path = str(path)

    result = subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", ref, git_path],
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        # Path doesn't exist at ref
        return []

    # Filter by supported extensions
    files = []
    for line in result.stdout.strip().split("\n"):
        if not line:
            continue
        file_path = Path(line)
        if file_path.suffix.lower() in supported_exts:
            files.append(line)

    return sorted(files)


def load_file_at_ref(ref: str, file_path: str, max_chars: int = 200000) -> str:
    """
    Load file content from a git ref.

    Args:
        ref: Git reference
        file_path: Relative path to file
        max_chars: Maximum characters to read

    Returns:
        File content (truncated if necessary)
    """
    result = subprocess.run(
        ["git", "show", f"{ref}:{file_path}"],
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        # File doesn't exist or unreadable
        return ""

    content = result.stdout

    if len(content) > max_chars:
        content = content[:max_chars] + "\n\n... (truncated due to size limit)"

    return content

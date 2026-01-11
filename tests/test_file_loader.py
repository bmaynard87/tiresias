"""Tests for file loading utilities."""

from pathlib import Path

import pytest

from tiresias.core.file_loader import (
    discover_files,
    load_file_content,
    redact_secrets,
)


def test_discover_files_single_file(tmp_path: Path) -> None:
    """Test discovering a single file."""
    test_file = tmp_path / "test.md"
    test_file.write_text("# Test")

    files = discover_files(str(test_file))

    assert len(files) == 1
    assert files[0] == test_file


def test_discover_files_directory(tmp_path: Path) -> None:
    """Test discovering files in a directory."""
    (tmp_path / "doc1.md").write_text("# Doc 1")
    (tmp_path / "doc2.txt").write_text("Doc 2")
    (tmp_path / "config.json").write_text("{}")
    (tmp_path / "ignore.py").write_text("# Should be ignored")

    files = discover_files(str(tmp_path))

    assert len(files) == 3
    assert all(f.suffix in {".md", ".txt", ".json"} for f in files)


def test_discover_files_with_ignore_patterns(tmp_path: Path) -> None:
    """Test file discovery with ignore patterns."""
    (tmp_path / "include.md").write_text("# Include")
    (tmp_path / "ignore.md").write_text("# Ignore")

    files = discover_files(str(tmp_path), ignore_paths=["**/ignore.md"])

    assert len(files) == 1
    assert files[0].name == "include.md"


def test_discover_files_returns_sorted(tmp_path: Path) -> None:
    """Test that discovered files are sorted."""
    (tmp_path / "z.md").write_text("Z")
    (tmp_path / "a.md").write_text("A")
    (tmp_path / "m.md").write_text("M")

    files = discover_files(str(tmp_path))

    names = [f.name for f in files]
    assert names == sorted(names)


def test_load_file_content_basic(tmp_path: Path) -> None:
    """Test loading file content."""
    test_file = tmp_path / "test.md"
    content = "# Test\nSome content here"
    test_file.write_text(content)

    loaded = load_file_content(test_file)

    assert loaded == content


def test_load_file_content_truncates_large_files(tmp_path: Path) -> None:
    """Test that large files are truncated."""
    test_file = tmp_path / "large.txt"
    content = "x" * 300000  # 300k chars
    test_file.write_text(content)

    loaded = load_file_content(test_file, max_chars=1000)

    assert len(loaded) <= 1100  # 1000 + truncation message
    assert "truncated" in loaded


def test_load_file_content_handles_errors(tmp_path: Path) -> None:
    """Test that file loading handles errors gracefully."""
    nonexistent = tmp_path / "nonexistent.md"

    loaded = load_file_content(nonexistent)

    assert loaded == ""


def test_redact_secrets_api_keys() -> None:
    """Test redacting API keys."""
    content = "API_KEY=abc123secret456 and more text"

    redacted = redact_secrets(content)

    assert "abc123secret456" not in redacted
    assert "***REDACTED***" in redacted


def test_redact_secrets_tokens() -> None:
    """Test redacting tokens."""
    content = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"

    redacted = redact_secrets(content)

    assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in redacted
    assert "***REDACTED***" in redacted


def test_redact_secrets_custom_patterns() -> None:
    """Test custom redaction patterns."""
    content = "internal-key-12345"

    redacted = redact_secrets(content, custom_patterns=[r"internal-key-\w+"])

    assert "internal-key-12345" not in redacted
    assert "***REDACTED***" in redacted


def test_redact_secrets_preserves_normal_text() -> None:
    """Test that normal text is preserved."""
    content = "This is normal text without secrets"

    redacted = redact_secrets(content)

    assert redacted == content

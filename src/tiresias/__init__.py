"""Tiresias: Design review and pre-mortem analysis tool."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("tiresias")
except PackageNotFoundError:
    # Fallback for development when package not installed
    __version__ = "0.0.0+dev"

__all__ = ["__version__", "main"]


def main() -> None:
    """CLI entry point."""
    from tiresias.cli.app import app

    app()

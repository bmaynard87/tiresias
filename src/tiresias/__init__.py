"""Tiresias: Design review and pre-mortem analysis tool."""

__version__ = "0.1.0"

__all__ = ["__version__", "main"]


def main() -> None:
    """CLI entry point."""
    from tiresias.cli.app import app

    app()

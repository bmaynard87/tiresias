"""Output renderers for Tiresias reports."""

from tiresias.renderers.json import render_json
from tiresias.renderers.text import render_text

__all__ = ["render_json", "render_text"]

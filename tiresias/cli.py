from __future__ import annotations

import json
from pathlib import Path

import typer

from .config import load_config
from .gating import should_fail
from .providers.openai_provider import OpenAIProvider
from .render import render_review_md
from .reviewer import Reviewer


app = typer.Typer(add_completion=False, no_args_is_help=True)


@app.callback()
def main() -> None:
    """Tiresias: deterministic pre-mortem design review gatekeeper."""



def build_provider(provider_name: str):
    name = (provider_name or "").strip().lower()
    if name in ("openai", "stub"):
        return OpenAIProvider()
    raise typer.BadParameter(f"Unknown provider: {provider_name!r}")


@app.command()
def review(
    path: Path = typer.Argument(..., exists=True, dir_okay=False, readable=True),
    fail_on: str = typer.Option(
        "critical",
        "--fail-on",
        help="Exit with code 2 if overall risk is at or above this threshold.",
    ),
    config: Path = typer.Option(
        Path(".tiresias.yml"),
        "--config",
        help="Path to Tiresias YAML config (defaults to .tiresias.yml if present).",
        show_default=True,
    ),
) -> None:
    cfg = load_config(config)
    provider = build_provider(cfg.provider)

    markdown = path.read_text(encoding="utf-8")
    review_payload = Reviewer(provider=provider).review_markdown(markdown)

    rendered = render_review_md(review_payload)
    typer.echo(rendered)

    out_dir = Path(".tiresias.out")
    out_dir.mkdir(parents=True, exist_ok=True)

    (out_dir / "review.json").write_text(
        json.dumps(review_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (out_dir / "review.md").write_text(rendered + "\n", encoding="utf-8")

    if should_fail(review_payload, fail_on):
        raise typer.Exit(code=2)

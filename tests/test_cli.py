from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

import tiresias.cli as cli


runner = CliRunner()


def test_review_exits_zero_by_default(fixtures_dir, monkeypatch):
    def _fake_build_provider(_name: str):
        from tests.conftest import FakeProvider

        return FakeProvider(overall_risk="high")

    monkeypatch.setattr(cli, "build_provider", _fake_build_provider)

    with runner.isolated_filesystem():
        doc = Path("sample_doc.md")
        doc.write_text((fixtures_dir / "sample_doc.md").read_text(encoding="utf-8"), encoding="utf-8")

        result = runner.invoke(cli.app, ["review", str(doc)])
        assert result.exit_code == 0


def test_review_fails_when_fail_on_low(fixtures_dir, monkeypatch):
    def _fake_build_provider(_name: str):
        from tests.conftest import FakeProvider

        return FakeProvider(overall_risk="high")

    monkeypatch.setattr(cli, "build_provider", _fake_build_provider)

    with runner.isolated_filesystem():
        doc = Path("sample_doc.md")
        doc.write_text((fixtures_dir / "sample_doc.md").read_text(encoding="utf-8"), encoding="utf-8")

        result = runner.invoke(cli.app, ["review", str(doc), "--fail-on", "low"])
        assert result.exit_code == 2

"""Tests for API keys handed to the MCP server by the Claude Code plugin."""

from __future__ import annotations

import asyncio
import json
import os

import pytest

pytest.importorskip("fastmcp", reason="mcp extra not installed")

from mcp_server import server  # noqa: E402
from mcp_server.server import _apply_plugin_credentials, check_setup  # noqa: E402


@pytest.fixture(autouse=True)
def _fresh_plugin_state(monkeypatch, tmp_path):
    monkeypatch.setattr(server, "_plugin_provided_keys", set())
    # Settings() reads .env from the working directory; keep the developer's out.
    monkeypatch.chdir(tmp_path)


def test_plugin_key_is_promoted_to_provider_variable(monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.setenv("PAPERBANANA_PLUGIN_GOOGLE_API_KEY", "plugin-key")

    _apply_plugin_credentials()

    assert os.environ["GOOGLE_API_KEY"] == "plugin-key"
    assert "PAPERBANANA_PLUGIN_GOOGLE_API_KEY" not in os.environ


def test_plugin_key_wins_over_shell_environment(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "shell-key")
    monkeypatch.setenv("PAPERBANANA_PLUGIN_OPENAI_API_KEY", "plugin-key")

    _apply_plugin_credentials()

    assert os.environ["OPENAI_API_KEY"] == "plugin-key"


@pytest.mark.parametrize("unset_value", ["", "   ", "${user_config.google_api_key}"])
def test_unset_plugin_option_keeps_existing_key(monkeypatch, unset_value):
    monkeypatch.setenv("GOOGLE_API_KEY", "shell-key")
    monkeypatch.setenv("PAPERBANANA_PLUGIN_GOOGLE_API_KEY", unset_value)

    _apply_plugin_credentials()

    assert os.environ["GOOGLE_API_KEY"] == "shell-key"


def test_check_setup_reports_key_sources_without_values(monkeypatch, tmp_path):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("PAPERBANANA_PLUGIN_GOOGLE_API_KEY", "plugin-secret")
    _apply_plugin_credentials()

    report = json.loads(asyncio.run(check_setup()))

    assert report["api_keys"]["GOOGLE_API_KEY"] == {"set": True, "source": "plugin_config"}
    assert report["api_keys"]["OPENAI_API_KEY"] == {"set": False, "source": None}
    assert "plugin-secret" not in json.dumps(report)
    assert report["output_dir"] == str((tmp_path / "outputs").resolve())


def test_check_setup_distinguishes_environment_and_dotenv(monkeypatch, tmp_path):
    (tmp_path / ".env").write_text("OPENAI_API_KEY=from-dotenv\n", encoding="utf-8")
    monkeypatch.setenv("GOOGLE_API_KEY", "from-shell")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    report = json.loads(asyncio.run(check_setup()))

    assert report["api_keys"]["GOOGLE_API_KEY"]["source"] == "environment"
    assert report["api_keys"]["OPENAI_API_KEY"]["source"] == "dotenv"

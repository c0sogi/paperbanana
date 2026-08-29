"""Tests for exact MCP model selection and provider inference."""

from __future__ import annotations

import pytest

pytest.importorskip("fastmcp", reason="mcp extra not installed")

from mcp_server.model_catalog import exact_model_overrides
from mcp_server.server import _mcp_settings_for_continue, _settings_with_models


def test_exact_models_infer_their_providers():
    overrides = exact_model_overrides(vlm_model="gpt-5.2", image_model="gpt-image-2")
    assert overrides["vlm_provider"] == "openai"
    assert overrides["image_provider"] == "openai_imagen"


def test_provider_model_mismatch_is_rejected_before_api_call():
    with pytest.raises(ValueError, match="requires provider 'openai_imagen'"):
        exact_model_overrides(
            image_provider="google_imagen",
            image_model="gpt-image-2",
        )


def test_unknown_model_is_rejected_before_api_call():
    with pytest.raises(ValueError, match="Unsupported VLM model"):
        exact_model_overrides(vlm_model="made-up-model")


def test_explicit_models_win_over_provider_specific_environment(monkeypatch):
    monkeypatch.setenv("GOOGLE_VLM_MODEL", "environment-vlm")
    monkeypatch.setenv("OPENAI_IMAGE_MODEL", "environment-image")

    settings = _settings_with_models(
        vlm_model="gemini-3.7-flash",
        image_model="gpt-image-2",
    )

    assert settings.effective_vlm_model == "gemini-3.7-flash"
    assert settings.effective_image_model == "gpt-image-2"
    assert settings.vlm_provider == "gemini"
    assert settings.image_provider == "openai_imagen"


def test_explicit_models_win_over_provider_specific_yaml(tmp_path):
    config = tmp_path / "config.yaml"
    config.write_text(
        "vlm:\n  provider: openai\n  model: yaml-vlm\n"
        "image:\n  provider: openai_imagen\n  model: yaml-image\n",
        encoding="utf-8",
    )

    settings = _mcp_settings_for_continue(
        "outputs",
        str(config),
        vlm_model="gemini-3.7-flash",
        image_model="gpt-image-2",
    )

    assert settings.vlm_provider == "gemini"
    assert settings.effective_vlm_model == "gemini-3.7-flash"
    assert settings.image_provider == "openai_imagen"
    assert settings.effective_image_model == "gpt-image-2"

"""Smoke tests for the MCP server tool surface.

These guard against tools silently dropping out of registration (e.g. a
decorator typo or an import error in a tool module) and keep the public
tool list in sync with the docs.
"""

from __future__ import annotations

import asyncio
import json

import pytest

pytest.importorskip("fastmcp", reason="mcp extra not installed")

from mcp_server.server import mcp  # noqa: E402

EXPECTED_TOOLS = {
    "batch_diagrams",
    "batch_plots",
    "cancel_figure_session",
    "continue_diagram",
    "continue_plot",
    "continue_run",
    "download_references",
    "evaluate_diagram",
    "evaluate_plot",
    "generate_diagram",
    "generate_plot",
    "get_figure_session",
    "list_figure_sessions",
    "orchestrate_figures",
    "preview_figure_session",
    "start_diagram_session",
    "list_available_models",
}


def _list_tools():
    return asyncio.run(mcp.list_tools())


def test_all_expected_tools_registered():
    names = {t.name for t in _list_tools()}
    missing = EXPECTED_TOOLS - names
    assert not missing, f"MCP tools missing from registration: {missing}"


def test_no_unexpected_tools():
    """New tools are welcome — add them to EXPECTED_TOOLS and the README."""
    names = {t.name for t in _list_tools()}
    unexpected = names - EXPECTED_TOOLS
    assert not unexpected, (
        f"New MCP tools {unexpected} — update EXPECTED_TOOLS, the server "
        "docstring, and the README MCP section together."
    )


def test_every_tool_has_description():
    undocumented = [t.name for t in _list_tools() if not (t.description or "").strip()]
    assert not undocumented, f"MCP tools without descriptions: {undocumented}"


def test_generate_diagram_exposes_input_images_param():
    """generate_diagram accepts optional input_images (reference/sketch paths)."""
    tool = next(t for t in _list_tools() if t.name == "generate_diagram")
    assert "input_images" in tool.parameters.get("properties", {})


def _enum_values(tool_name: str, parameter: str) -> set[str]:
    tool = next(t for t in _list_tools() if t.name == tool_name)
    schema = tool.parameters["properties"][parameter]
    return set(next(branch["enum"] for branch in schema["anyOf"] if "enum" in branch))


def test_model_parameters_expose_exact_ids():
    expected_vlm = {
        "gemini-3.7-flash",
        "gpt-5.2",
    }
    expected_image = {
        "gemini-3.1-flash-image",
        "gemini-3-pro-image",
        "gpt-image-1.5",
        "gpt-image-2",
    }
    for tool_name in (
        "generate_diagram",
        "start_diagram_session",
        "continue_run",
        "generate_plot",
        "continue_diagram",
        "continue_plot",
        "evaluate_diagram",
        "evaluate_plot",
        "orchestrate_figures",
        "batch_diagrams",
        "batch_plots",
    ):
        assert _enum_values(tool_name, "vlm_model") == expected_vlm
    for tool_name in (
        "generate_diagram",
        "start_diagram_session",
        "continue_run",
        "continue_diagram",
        "continue_plot",
        "orchestrate_figures",
        "batch_diagrams",
        "batch_plots",
    ):
        assert _enum_values(tool_name, "image_model") == expected_image

    generate_plot = next(t for t in _list_tools() if t.name == "generate_plot")
    assert "image_model" not in generate_plot.parameters["properties"]


def test_list_available_models_returns_objective_catalog():
    from mcp_server.server import list_available_models

    catalog = json.loads(asyncio.run(list_available_models()))
    assert catalog["defaults"] == {
        "vlm_model": "gemini-3.7-flash",
        "image_model": "gemini-3.1-flash-image",
    }
    assert catalog["price_checked_at"] == "2026-08-29"
    assert {item["model"] for item in catalog["image_models"]} == {
        "gemini-3.1-flash-image",
        "gemini-3-pro-image",
        "gpt-image-1.5",
        "gpt-image-2",
    }


def test_validate_input_images_rejects_missing_and_non_raster(tmp_path):
    from mcp_server.server import _validate_input_images

    # Missing file
    with pytest.raises(ValueError, match="not found"):
        _validate_input_images([str(tmp_path / "missing.png")])

    # Non-raster file with image extension
    fake = tmp_path / "fake.png"
    fake.write_text("not an image", encoding="utf-8")
    with pytest.raises(ValueError, match="raster image"):
        _validate_input_images([str(fake)])

    # Valid tiny PNG passes
    from PIL import Image

    real = tmp_path / "real.png"
    Image.new("RGB", (2, 2), color=(255, 0, 0)).save(real)
    assert _validate_input_images([str(real)]) == [str(real)]
    assert _validate_input_images(None) == []

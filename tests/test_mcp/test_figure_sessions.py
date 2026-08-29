from __future__ import annotations

import asyncio
import json
from types import SimpleNamespace

import pytest
from PIL import Image

pytest.importorskip("fastmcp", reason="mcp extra not installed")

from fastmcp import Client

import mcp_server.server as server
from mcp_server.figure_sessions import FigureSessionStore, figure_sessions


@pytest.mark.asyncio
async def test_store_lists_and_cancels_active_session(tmp_path):
    store = FigureSessionStore()
    session = store.create(
        operation="test",
        run_id="run_test",
        run_dir=str(tmp_path / "run_test"),
    )
    started = asyncio.Event()

    async def _work() -> None:
        started.set()
        await asyncio.Event().wait()

    store.start_background(session, _work())
    await started.wait()

    active = store.list()
    assert [item["session_id"] for item in active] == [session.session_id]
    assert active[0]["status"] == "running"

    result = await store.cancel(session.session_id)
    assert result["cancelled"] is True
    assert store.get(session.session_id)["status"] == "cancelled"
    assert store.list() == []
    assert store.list(include_finished=True)[0]["status"] == "cancelled"


def test_snapshot_finds_latest_iteration_image(tmp_path):
    store = FigureSessionStore()
    run_dir = tmp_path / "run_test"
    image = run_dir / "iter_1" / "output.png"
    image.parent.mkdir(parents=True)
    image.write_bytes(b"image")
    session = store.create(operation="test", run_id="run_test", run_dir=str(run_dir))

    assert store.snapshot(session)["latest_image_path"] == str(image.resolve())


@pytest.mark.asyncio
async def test_mcp_background_session_reports_progress_and_cancels(monkeypatch):
    started = asyncio.Event()

    class _FakePipeline:
        def __init__(self, settings, progress_callback):
            self.settings = settings
            self.run_id = "run_fake"
            self._progress_callback = progress_callback

        async def generate(self, _gen_input):
            self._progress_callback(
                "iteration_started",
                {"iteration": 1, "total_iterations": 10},
            )
            started.set()
            await asyncio.Event().wait()

    monkeypatch.setattr(server, "PaperBananaPipeline", _FakePipeline)
    figure_sessions.clear()

    async with Client(server.mcp) as client:
        start_result = await client.call_tool(
            "start_diagram_session",
            {"source_context": "method", "caption": "figure", "iterations": 10},
        )
        session_id = json.loads(start_result.content[0].text)["session"]["session_id"]
        await started.wait()

        status_result = await client.call_tool(
            "get_figure_session",
            {"session_id": session_id},
        )
        status = json.loads(status_result.content[0].text)["session"]
        assert status["status"] == "running"
        assert status["progress_event"] == "iteration_started"
        assert status["progress"]["iteration"] == 1
        assert status["current_iteration"] == 1
        assert status["total_iterations"] == 10

        cancel_result = await client.call_tool(
            "cancel_figure_session",
            {"session_id": session_id},
        )
        cancelled = json.loads(cancel_result.content[0].text)
        assert cancelled["strict_success"] is True
        assert cancelled["session"]["status"] == "cancelled"
    figure_sessions.clear()


@pytest.mark.asyncio
async def test_mcp_background_session_completes_and_previews(tmp_path, monkeypatch):
    output = tmp_path / "final.png"
    Image.new("RGB", (4, 4), color=(20, 40, 60)).save(output)

    class _FakePipeline:
        def __init__(self, settings, progress_callback):
            self.settings = settings
            self.run_id = "run_complete"
            self._progress_callback = progress_callback

        async def generate(self, _gen_input):
            self._progress_callback("generation_completed", {"iterations": 1})
            return SimpleNamespace(
                image_path=str(output),
                generated_caption=None,
            )

    monkeypatch.setattr(server, "PaperBananaPipeline", _FakePipeline)
    figure_sessions.clear()

    async with Client(server.mcp) as client:
        start_result = await client.call_tool(
            "start_diagram_session",
            {"source_context": "method", "caption": "figure"},
        )
        session_id = json.loads(start_result.content[0].text)["session"]["session_id"]

        for _ in range(10):
            status_result = await client.call_tool(
                "get_figure_session",
                {"session_id": session_id},
            )
            status = json.loads(status_result.content[0].text)["session"]
            if status["status"] == "completed":
                break
            await asyncio.sleep(0)

        assert status["status"] == "completed"
        assert status["final_image_path"] == str(output.resolve())
        preview = await client.call_tool(
            "preview_figure_session",
            {"session_id": session_id},
        )
        assert preview.content[0].type == "image"
    figure_sessions.clear()

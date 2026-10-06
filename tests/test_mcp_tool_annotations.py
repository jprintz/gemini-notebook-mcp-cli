"""Every registered MCP tool must carry annotations (title and behaviour hints)."""

import asyncio

import pytest

from notebooklm_tools.mcp.server import mcp
from notebooklm_tools.mcp.tool_annotations import TOOL_ANNOTATIONS
from notebooklm_tools.mcp.tools._utils import _tool_registry


@pytest.fixture(scope="module")
def tools():
    # Wire-format dicts (what clients see), independent of the SDK's attribute naming.
    return {
        t.name: (
            t.annotations.model_dump(by_alias=True, exclude_none=True) if t.annotations else {}
        )
        for t in asyncio.run(mcp.list_tools())
    }


def test_annotation_map_covers_exactly_the_registered_tools():
    registered = {name for name, _ in _tool_registry}
    assert set(TOOL_ANNOTATIONS) == registered


def test_every_tool_has_a_title(tools):
    for name, ann in tools.items():
        assert ann.get("title"), f"{name} has no title"


def test_read_only_hint_is_set_explicitly_on_every_tool(tools):
    for name, ann in tools.items():
        assert "readOnlyHint" in ann, f"{name}: readOnlyHint not set"


def test_destructive_hint_is_set_on_every_non_read_only_tool(tools):
    for name, ann in tools.items():
        if not ann["readOnlyHint"]:
            assert "destructiveHint" in ann, f"{name}: destructiveHint not set"
            assert "idempotentHint" in ann, f"{name}: idempotentHint not set"


def test_read_only_tools_do_not_claim_destructive_hints(tools):
    for name, ann in tools.items():
        if ann["readOnlyHint"]:
            assert "destructiveHint" not in ann, f"{name}: read-only tool sets destructiveHint"


def test_open_world_hint_is_set_on_every_tool(tools):
    for name, ann in tools.items():
        assert "openWorldHint" in ann, f"{name}: openWorldHint not set"


def test_tools_that_can_delete_are_marked_destructive(tools):
    # Includes multi-action tools whose actions can delete or replace data.
    for name in (
        "alias",
        "batch",
        "collection_delete",
        "label",
        "note",
        "notebook_delete",
        "pipeline",
        "source_delete",
        "studio_delete",
        "tag",
    ):
        assert tools[name]["destructiveHint"] is True, name

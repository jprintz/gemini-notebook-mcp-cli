"""Every registered MCP tool must carry annotations (title and behaviour hints)."""

import asyncio

import pytest

from notebooklm_tools.mcp.server import mcp
from notebooklm_tools.mcp.tool_annotations import TOOL_ANNOTATIONS
from notebooklm_tools.mcp.tools._utils import _tool_registry


def _wire(annotations):
    # Wire-format dict (what clients see), independent of the SDK's attribute naming.
    return annotations.model_dump(by_alias=True, exclude_none=True) if annotations else {}


@pytest.fixture(scope="module")
def tools():
    # Built from the map, not mcp.list_tools(), so tools hidden through
    # NOTEBOOKLM_DISABLED_GROUPS / NOTEBOOKLM_DISABLED_TOOLS are still checked.
    return {name: _wire(ann) for name, ann in TOOL_ANNOTATIONS.items()}


def test_annotation_map_covers_exactly_the_registered_tools():
    registered = {name for name, _ in _tool_registry}
    assert set(TOOL_ANNOTATIONS) == registered


def test_listed_tools_carry_their_annotations():
    listed = asyncio.run(mcp.list_tools())
    assert listed
    for tool in listed:
        assert _wire(tool.annotations) == _wire(TOOL_ANNOTATIONS[tool.name]), tool.name


def test_every_tool_has_a_title(tools):
    for name, ann in tools.items():
        assert ann.get("title"), f"{name} has no title"


def test_read_only_hint_is_set_explicitly_on_every_tool(tools):
    for name, ann in tools.items():
        assert "readOnlyHint" in ann, f"{name}: readOnlyHint not set"


def test_all_four_hints_are_set_on_every_tool(tools):
    for name, ann in tools.items():
        for key in ("readOnlyHint", "destructiveHint", "idempotentHint", "openWorldHint"):
            assert key in ann, f"{name}: {key} not set"


def test_read_only_tools_are_neither_destructive_nor_non_idempotent(tools):
    for name, ann in tools.items():
        if ann["readOnlyHint"]:
            assert ann["destructiveHint"] is False, f"{name}: read-only tool is destructive"
            assert ann["idempotentHint"] is True, f"{name}: read-only tool is not idempotent"


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


def test_tools_with_write_options_are_not_read_only(tools):
    # research_status can import sources (auto_import=True).
    assert tools["research_status"]["readOnlyHint"] is False

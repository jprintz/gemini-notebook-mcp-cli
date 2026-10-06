"""MCP tool annotations (title and behaviour hints) for every registered tool.

Annotations let MCP clients group tools and decide when to ask for approval
without guessing from tool names. Hints follow the MCP spec:

- ``readOnlyHint``: the tool does not change anything. Set explicitly on every tool.
- ``destructiveHint``: the tool may delete or overwrite existing data. Set on every
  non-read-only tool (the spec default is ``True`` when omitted).
- ``idempotentHint``: repeating the call with the same arguments has no further effect.
- ``openWorldHint``: the tool talks to an external system (Gemini Notebook / Google).
  ``False`` means local config only.

Classification rules:

- Tools that only fetch data are read-only, including the query tools. A query adds
  to the notebook's chat history, which is treated as a side effect of reading.
- Tools that create things (notebooks, sources, notes, artifacts, exports) are
  additive: ``destructive=False``, ``idempotent=False``.
- Rename, set and configure tools overwrite a single value: ``destructive=False``,
  ``idempotent=True``.
- Delete tools, and tools that replace existing content, are ``destructive=True``.
- Multi-action tools take the most severe classification of any action they expose
  (for example ``note`` and ``label`` can delete, ``pipeline`` can run
  ``notebook_delete``).
- Sharing tools are not destructive, but they expose a notebook or contact other
  people, so they stay non-read-only and non-idempotent where they send invites.

The title is carried in ``ToolAnnotations.title`` so it works on every FastMCP
version that supports annotations.
"""

from mcp.types import ToolAnnotations


def _read(title: str, *, open_world: bool = True) -> ToolAnnotations:
    return ToolAnnotations(title=title, readOnlyHint=True, openWorldHint=open_world)


def _write(
    title: str, *, destructive: bool, idempotent: bool, open_world: bool = True
) -> ToolAnnotations:
    return ToolAnnotations(
        title=title,
        readOnlyHint=False,
        destructiveHint=destructive,
        idempotentHint=idempotent,
        openWorldHint=open_world,
    )


TOOL_ANNOTATIONS: dict[str, ToolAnnotations] = {
    # action=delete removes a saved alias
    "alias": _write("Manage notebook aliases", destructive=True, idempotent=True, open_world=False),
    # Can include deletes - conservative
    "batch": _write("Batch operations across notebooks", destructive=True, idempotent=False),
    "chat_configure": _write("Configure notebook chat", destructive=False, idempotent=True),
    # Writes a local file
    "chat_export": _write("Export chat transcript", destructive=False, idempotent=True),
    "chat_get": _read("Get chat transcript"),
    "chat_list": _read("List chat sessions"),
    # Creates a new note each call
    "chat_save_to_note": _write("Save chat as note", destructive=False, idempotent=False),
    "collection_create": _write("Create collection", destructive=False, idempotent=False),
    "collection_delete": _write("Delete collection", destructive=True, idempotent=True),
    # Replaces full notebook list - can drop members
    "collection_edit": _write("Edit collection", destructive=True, idempotent=True),
    "collection_list": _read("List collections"),
    "collection_set_emoji": _write("Set collection emoji", destructive=False, idempotent=True),
    # May add chat history in notebooks
    "cross_notebook_query": _read("Query multiple notebooks"),
    # Writes local files
    "download_all_artifacts": _write("Download all artifacts", destructive=False, idempotent=True),
    # Writes a local file
    "download_artifact": _write("Download artifact", destructive=False, idempotent=True),
    # Creates a new Google file each call
    "export_artifact": _write(
        "Export artifact to Docs/Sheets", destructive=False, idempotent=False
    ),
    # delete + reorganize (replaces all labels)
    "label": _write("Manage source labels", destructive=True, idempotent=False),
    # Multi-action incl. delete
    "note": _write("Manage notes", destructive=True, idempotent=False),
    "notebook_create": _write("Create notebook", destructive=False, idempotent=False),
    # Permanent
    "notebook_delete": _write("Delete notebook", destructive=True, idempotent=True),
    "notebook_describe": _read("Describe notebook"),
    "notebook_get": _read("Get notebook"),
    "notebook_list": _read("List notebooks"),
    # May add chat history in notebook
    "notebook_query": _read("Query notebook"),
    # May add chat history in notebook
    "notebook_query_start": _read("Start async query"),
    "notebook_query_status": _read("Get async query status"),
    "notebook_rename": _write("Rename notebook", destructive=False, idempotent=True),
    # Sends invites to people - keep approval
    "notebook_share_batch": _write(
        "Invite collaborators (batch)", destructive=False, idempotent=False
    ),
    # Sends invite to a person - keep approval
    "notebook_share_invite": _write("Invite collaborator", destructive=False, idempotent=False),
    # Exposure risk - keep approval
    "notebook_share_public": _write("Set public link access", destructive=False, idempotent=True),
    "notebook_share_status": _read("Get sharing status"),
    # Arbitrary multi-step - conservative
    "pipeline": _write("Run notebook pipeline", destructive=True, idempotent=False),
    # Local config only
    "profile": _write(
        "Manage account profiles", destructive=False, idempotent=True, open_world=False
    ),
    "refresh_auth": _write("Refresh authentication", destructive=False, idempotent=True),
    # Behaviour unclear - verify in code
    "report": _write("Interact with report elements", destructive=False, idempotent=False),
    "research_import": _write("Import research sources", destructive=False, idempotent=False),
    "research_start": _write("Start research", destructive=False, idempotent=False),
    "research_status": _read("Get research status"),
    # Overwrites stored credentials
    "save_auth_tokens": _write(
        "Save auth cookies", destructive=True, idempotent=True, open_world=False
    ),
    "server_info": _read("Get server info"),
    "source_add": _write("Add source", destructive=False, idempotent=False),
    # Permanent
    "source_delete": _write("Delete source", destructive=True, idempotent=True),
    "source_describe": _read("Describe source"),
    "source_get_content": _read("Get source content"),
    "source_list_drive": _read("List sources with Drive status"),
    "source_rename": _write("Rename source", destructive=False, idempotent=True),
    # Overwrites source content with latest
    "source_sync_drive": _write("Sync Drive sources", destructive=True, idempotent=True),
    "studio_create": _write("Create studio artifact", destructive=False, idempotent=False),
    # Permanent
    "studio_delete": _write("Delete studio artifact", destructive=True, idempotent=True),
    # Alters existing artifact
    "studio_revise": _write("Revise slides", destructive=True, idempotent=False),
    # Read + rename in one tool - worth splitting upstream
    "studio_status": _write("Get studio status / rename", destructive=False, idempotent=True),
    # action=remove deletes saved tags
    "tag": _write("Manage notebook tags", destructive=True, idempotent=True, open_world=False),
    "usage_get": _read("Get usage allowance"),
}

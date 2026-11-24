"""Phase 2 自动生成：24 个缺失契约工具（参数/描述对齐 sdk-tools.d.ts）。

生成脚本: tools/recon/gen_contract_tools.py
不要手改，改脚本后重新生成。
"""
from __future__ import annotations
from typing import Any


def _not_implemented(tool_name: str):
    """契约对齐但功能未实现的工具：返回明确的未实现提示（不编造）。"""
    def _run(**kwargs: Any) -> str:
        return f"[{tool_name}] 契约已对齐，但该工具在本环境无对应后端实现（MCP/通知/引导类）。"
    return _run


CONTRACT_TOOLS: dict[str, dict] = {
    'Artifact': {
        "name": 'Artifact',
        "description": 'Create or update an artifact — a file with special rendering (code, markdown, HTML). Use for deliverables the user will view.',
        "input_schema": {"type": "object", "properties": {"action": {"type": "string", "enum": ["publish", "list", "read", "list_types", "watch", "unwatch", "status", "upload_asset", "list_assets", "read_asset", "delete_asset", "pin", "unpin"], "description": "Omit (or 'publish') to publish file_path. 'list' enumerates artifacts — the user's own by default, see `scope`; only `limit` and `scope` may accompany it. 'read' returns the content of the published artifact at `url` (raw HTML for the user's own; an isolated summary, steered by the optional `prompt`, for one someone else owns, though a page published in this session's own Slack channel can come back in full as untrusted content) — see **Calls**. 'watch', 'unwatch', and 'status' manage live-update subscriptions through which a session keeps track of new versions of an artifact published elsewhere, and those aren't available in this session: 'watch' only reports that — this session does not keep track of new versions — and 'status' lists this session's artifact watches (pass `url` to check one). 'upload_asset' adds one local media, PDF, font, or text file to an existing artifact — pass `url` and `file_path` (or `file_paths` for several in one call). 'list_assets' lists the files in an artifact's asset store (pass `url`; `after` continues a listing), 'read_asset' saves one of them to a local file named by its id (pass `url` and `asset_id`, optionally `out_dir`), and 'delete_asset' permanently removes one (pass `url` and `asset_id`). See **Artifact assets** above. 'pin' adds the artifact at `url` to the user's pinned list in their claude.ai sidebar and 'unpin' removes it (nothing else may accompany either) — private to the user, reversible, and no change to who can see the artifact."}, "file_path": {"type": "string", "description": "Path to the .html file to render. Required to publish (the default action). Use a short, distinctive basename — it is the last-resort title when the HTML has no <title> and no `title` parameter is given. For 'upload_asset', the local image, video, PDF, font, stylesheet (CSS), script (JS), or text (CSV, Markdown, JSON, plain text) file to upload."}, "favicon": {"type": "string", "description": "Deprecated; omit it. Use `icon`."}, "icon": {"type": "string", "description": "One short generic word for the artifact's browser-tab icon, such as chart, calendar, recipe, code or map — a plain signifier, not a product or brand name. Include it on every page's first publish; omit when republishing to keep the current icon, and pass a new one only when the user asks."}, "limit": {"type": "number", "description": "list only: maximum artifacts to return (default 25)."}, "scope": {"type": "string", "enum": ["mine", "shared", "all"], "description": "list only: 'mine' (default) lists artifacts the user owns; 'shared' lists artifacts other people shared with the user; 'all' lists both. Rows are labeled (mine)/(shared) whenever scope is not 'mine'."}, "title": {"type": "string", "description": "Title for the artifact — the name shown in the browser tab and gallery. A short, distinctive noun-phrase name — not a generic label, a summary, or a name with an appended explainer. Prefer a <title> tag at the top of the HTML itself; this parameter fills in only when the file lacks one in the first 8KB of the file, and never overrides the tag. HTML publishes only — Markdown pages keep their filename identity. Content always comes from file_path — there is no inline content parameter."}, "description": {"type": "string", "description": "One-sentence subtitle shown on the gallery card. Say what the page is or does."}, "label": {"type": "string", "description": "A short name for this publish, max 60 chars (e.g. \"Draft to legal\"). Optional — a few words, not a description."}, "url": {"type": "string", "description": "An existing artifact's claude.ai link (claude.ai/artifact/{id} or claude.ai/code/artifact/{uuid}; a chat, project or session link is not one) to update in place. Pass whenever the user wants to update an artifact this conversation did not publish — \"update my artifact\", \"keep the same link\", a pasted artifact URL — and find the URL with action: \"list\" or ask the user for the link if you don't have it; without this, the publish creates a separate artifact instead of updating the existing one. Omit for new artifacts and same-conversation redeploys. Must be an artifact the user owns or was given edit access to (a read of it says \"writer\"). Before publishing to an artifact this conversation has neither read nor published, read it (action: \"read\") and build on what comes back; a publish sent without that read is refused. A refusal that hands you the live version counts as that read: merge your edits into that version and publish that; never resend the refused content unchanged. For 'read' and the other url-addressed actions: the artifact to act on."}, "prompt": {"type": "string", "description": "read only: what to extract from an artifact shared with the user — its content reaches you as an isolated summary answering this. Ignored for artifacts the user owns and for a page published in this session's own Slack channel (raw content is returned); optional."}, "force": {"type": "boolean", "description": "Last-resort overwrite that DISCARDS the newer published version's page — another session's publish, or someone's save from a page that can publish new versions of itself. On a conflict the fix is to merge your changes onto the newer content (handed to you in the rejection, or re-read) and publish again — not force. Pass force:true only when the user has explicitly said to discard that specific version; never to get past a conflict on your own judgment. The tracked baseVersion is still sent; with force:true the server treats it as informational and overwrites, unless it refuses force over a version saved from inside the page. Omit (or false) so a concurrent write conflicts instead of being silently clobbered."}, "pin": {"type": "boolean", "description": "publish only: true also pins the published artifact to the user's claude.ai sidebar once it is published — pass it only when the user asked for that; a pin that fails never fails the publish (the result says so)."}, "out_dir": {"type": "string", "description": "read_asset: directory to save into — default: this artifact’s folder in your scratchpad directory, where saving needs no approval and which you can Read from. read_asset names the file by the asset id plus the extension for its type; saving to any directory other than the default is an ordinary file save the user may be asked to approve."}, "file_paths": {"type": "array", "items": {"type": "object"}, "description": "upload_asset: several local image, video, PDF, font, stylesheet or script files in place of `file_path`, up to 25 in one call, all into the artifact that `url` names; one approval covers the call, and the result lists each file's id and url, or why it was not uploaded. A CSV, Markdown, JSON or plain-text file, a symbolic or hard link, and a file outside the working directory each go in a call of their own with `file_path`."}, "asset_id": {"type": "string", "description": "read_asset and delete_asset: the asset's id (32 hex characters), from a list_assets or upload_asset result."}, "after": {"type": "string", "description": "list_assets only: the `next` value from a previous list_assets result, to continue that listing."}, "capabilities": {"type": "object", "description": "Runtime capabilities this page declares, as {name: config}. The control plane is the authority on valid names and config shapes. An empty object clears any previously stored declaration; omit the field on a redeploy to carry the stored declaration forward unchanged. Before declaring any capability, load the `artifact-capabilities` skill for the current contract and per-capability guidance."}, "contract": {"type": "string", "enum": ["latest"], "description": "The artifact's runtime version. Omit to keep its current version (the default); 'latest' to upgrade; a specific version to pin or roll back. Changing it changes how the published page behaves — pass only when the author explicitly intends the change, never as a side effect of editing."}}},
        "execute": _not_implemented('Artifact'),
    },
    'AskUserQuestion': {
        "name": 'AskUserQuestion',
        "description": 'Ask the user one or more multiple-choice questions to gather preferences or clarify an ambiguous request. Each question has 2-4 options.',
        "input_schema": {"type": "object", "properties": {"questions": {"type": "object", "description": "Questions to ask the user (1-4 questions)"}, "answers": {"type": "object", "description": "User answers collected by the permission component"}, "annotations": {"type": "object", "description": "Optional per-question annotations from the user (e.g., notes on preview selections). Keyed by question text."}, "metadata": {"type": "object", "description": "Optional metadata for tracking and analytics purposes. Not displayed to user."}}, "required": ["questions"]},
        "execute": _not_implemented('AskUserQuestion'),
    },
    'ClaudeDesign': {
        "name": 'ClaudeDesign',
        "description": 'Open or manage Claude Design — a visual design surface/canvas for producing UI mockups and designs.',
        "input_schema": {"type": "object", "properties": {"operation": {"type": "string", "description": "Claude Design action to perform. Call with \"list\" first to discover the available operations and their argument schemas."}, "arguments": {"type": "object", "description": "Action input object (server-validated). Pass {} for operations that take no input."}}, "required": ["arguments", "operation"]},
        "execute": _not_implemented('ClaudeDesign'),
    },
    'EnterPlanMode': {
        "name": 'EnterPlanMode',
        "description": 'Enter plan mode: a read-only research phase where you explore the codebase and design an approach without making changes.',
        "input_schema": {"type": "object", "properties": {}},
        "execute": _not_implemented('EnterPlanMode'),
    },
    'ExitPlanMode': {
        "name": 'ExitPlanMode',
        "description": 'Exit plan mode and present the plan to the user for approval before executing.',
        "input_schema": {"type": "object", "properties": {"allowedPrompts": {"type": "array", "items": {"type": "object"}, "description": "Deprecated: no longer used."}, "k": {"type": "object"}}, "required": ["k"]},
        "execute": _not_implemented('ExitPlanMode'),
    },
    'ListMcpResources': {
        "name": 'ListMcpResources',
        "description": 'List the resources exposed by connected MCP (Model Context Protocol) servers.',
        "input_schema": {"type": "object", "properties": {"server": {"type": "string", "description": "Optional server name to filter resources by"}}},
        "execute": _not_implemented('ListMcpResources'),
    },
    'Mcp': {
        "name": 'Mcp',
        "description": 'Invoke a tool provided by a connected MCP (Model Context Protocol) server.',
        "input_schema": {"type": "object", "properties": {"k": {"type": "object"}}, "required": ["k"]},
        "execute": _not_implemented('Mcp'),
    },
    'Monitor': {
        "name": 'Monitor',
        "description": 'Monitor a long-running process or condition and get notified when it changes.',
        "input_schema": {"type": "object", "properties": {"description": {"type": "string", "description": "Short human-readable description of what you are monitoring (shown in notifications)."}, "timeout_ms": {"type": "number", "description": "Kill the monitor after this deadline. Default 300000ms. Deadlines above 1800000ms are capped to 1800000ms. You are notified at expiry and can re-arm."}, "command": {"type": "string", "description": "Shell command or script. Each stdout line is an event; exit ends the watch."}, "ws": {"type": "object", "description": "WebSocket to open. Each text frame is an event; binary frames are reported as a placeholder line. Socket close ends the watch. Cannot be combined with command."}}, "required": ["description", "timeout_ms"]},
        "execute": _not_implemented('Monitor'),
    },
    'OfferChromeSetup': {
        "name": 'OfferChromeSetup',
        "description": 'Offer the user help setting up the Chrome browser extension / browser automation.',
        "input_schema": {"type": "object", "properties": {"reason": {"type": "string", "description": "A short phrase naming what the task needs the user's own browser for."}}},
        "execute": _not_implemented('OfferChromeSetup'),
    },
    'Projects': {
        "name": 'Projects',
        "description": 'Manage Projects — organize work into named projects with associated context and files.',
        "input_schema": {"type": "object", "properties": {"method": {"type": "string", "enum": ["project_info", "project_read", "project_search", "project_write", "project_delete", "project_memory_list", "project_memory_read"]}, "path": {"type": "string", "description": "project_read/project_write/project_delete: doc path. project_write: an existing path is replaced in place; a new bare filename (no \"/\") is namespaced to \"claude/<name>\". project_memory_read: memory file path as listed by project_memory_list."}, "content": {"type": "string", "description": "project_write: inline doc text. Mutually exclusive with local_path. Use local_path for anything you have on disk."}, "local_path": {"type": "string", "description": "project_write: a file inside the working directory to upload. The tool reads, encodes, and uploads directly — contents never enter your context. Mutually exclusive with content."}, "present_to_user": {"type": "boolean", "description": "project_write: true marks this doc as the file the user needs to see — the deliverable they asked for or must act on. Defaults to false; leave it unset for routine saves, notes, and bulk writes."}, "query": {"type": "string", "description": "project_search: knowledge-base query"}, "n": {"type": "number", "description": "project_search: number of hits (default 5)"}}, "required": ["method"]},
        "execute": _not_implemented('Projects'),
    },
    'ProposeGoal': {
        "name": 'ProposeGoal',
        "description": 'Propose a goal for the current session for the user to confirm.',
        "input_schema": {"type": "object", "properties": {"condition": {"type": "string", "description": "The completion condition to propose, written so a separate evaluator can verify it from the conversation (e.g. \"all tests in test/auth pass (bun test exits 0)\"). At most 500 characters — the user must be able to read the whole condition in the approval dialog."}, "ask_user": {"type": "boolean", "description": "Whether to ask the user for approval before the goal is set. Defaults to true — an approval dialog is shown. Set false ONLY when the user's own words in this conversation stated this outcome as what they want; the goal is then set directly, with a visible notice in the transcript, and the user can clear it with /goal clear."}}, "required": ["condition"]},
        "execute": _not_implemented('ProposeGoal'),
    },
    'ProposeSkills': {
        "name": 'ProposeSkills',
        "description": 'Propose new skills to be created based on the current workflow, for the user to review and adopt.',
        "input_schema": {"type": "object", "properties": {"proposals": {"type": "object", "description": "@minItems 1"}}, "required": ["proposals"]},
        "execute": _not_implemented('ProposeSkills'),
    },
    'PushNotification': {
        "name": 'PushNotification',
        "description": 'Send a push notification to the user (mobile/desktop).',
        "input_schema": {"type": "object", "properties": {"message": {"type": "string", "description": "The notification body. Keep it under 200 characters; mobile OSes truncate."}, "status": {"type": "string", "enum": ["proactive"]}}, "required": ["message", "status"]},
        "execute": _not_implemented('PushNotification'),
    },
    'ReadMcpResource': {
        "name": 'ReadMcpResource',
        "description": 'Read the contents of a specific resource exposed by an MCP server.',
        "input_schema": {"type": "object", "properties": {"server": {"type": "string", "description": "The MCP server name"}, "uri": {"type": "string", "description": "The resource URI to read"}}, "required": ["server", "uri"]},
        "execute": _not_implemented('ReadMcpResource'),
    },
    'ReadMcpResourceDir': {
        "name": 'ReadMcpResourceDir',
        "description": 'Read a directory listing of resources exposed by an MCP server.',
        "input_schema": {"type": "object", "properties": {"server": {"type": "string", "description": "The MCP server name"}, "uri": {"type": "string", "description": "The directory resource URI to list"}}, "required": ["server", "uri"]},
        "execute": _not_implemented('ReadMcpResourceDir'),
    },
    'ReadNotifications': {
        "name": 'ReadNotifications',
        "description": 'Read pending notifications that were pushed to the user.',
        "input_schema": {"type": "object", "properties": {}},
        "execute": _not_implemented('ReadNotifications'),
    },
    'RefreshMcpTools': {
        "name": 'RefreshMcpTools',
        "description": 'Refresh the tool list from connected MCP servers (after servers change).',
        "input_schema": {"type": "object", "properties": {"server": {"type": "string", "description": "Optional server name: refresh only this server. Omit to refresh all connected servers."}}},
        "execute": _not_implemented('RefreshMcpTools'),
    },
    'RemoteTrigger': {
        "name": 'RemoteTrigger',
        "description": 'Trigger an action on a remote agent/session.',
        "input_schema": {"type": "object", "properties": {"action": {"type": "string", "enum": ["list", "get", "create", "update", "run", "create_webhook_trigger", "list_runs", "get_run_log"]}, "trigger_id": {"type": "string", "description": "Required for get, update, run, and list_runs"}, "session_id": {"type": "string", "description": "Required for get_run_log: a run session id (cse_… or session_…, from list_runs)"}, "cursor": {"type": "string", "description": "next_cursor from a previous list_runs or get_run_log page"}, "body": {"type": "object", "description": "Required for create and update; optional for run"}}, "required": ["action"]},
        "execute": _not_implemented('RemoteTrigger'),
    },
    'SendFeedback': {
        "name": 'SendFeedback',
        "description": 'Send feedback about Claude Code to Anthropic (bug reports, feature requests).',
        "input_schema": {"type": "object", "properties": {"type": {"type": "string", "enum": ["bug", "idea", "missing_capability"], "description": "What kind of feedback this is."}, "title": {"type": "string", "description": "Short, specific one-line summary of the issue."}, "details": {"type": "string", "description": "Labeled bullets, in order: **What happened:** (observed vs. expected, exact error text if short); **What the user said:** (quoted, or \"User didn't comment; observed by the model.\"); **Repro:** (minimal steps); **Evidence:** (request IDs, timestamps, paths, versions; omit if none); optionally a final **Cause:** only if verified in-session. One to three lines per bullet. No narrative paragraphs, no speculation, no secrets."}, "area": {"type": "string", "description": "Optional short tag naming the part of Claude Code this is about (e.g. \"hooks config\", \"/help\", \"file editing\"). Leave blank if unclear."}, "failure_mode": {"type": "string", "enum": ["instruction_following", "destructive_actions", "code_quality", "repetition_and_looping", "model_regression", "overconfidence_and_hallucination", "context_and_memory", "overeager", "over_correction", "stopping_short", "dispute_or_decline", "subagent_overspawn", "tone_or_preachiness", "excessive_questions", "unwanted_scope", "other"], "description": "When the report is about MODEL BEHAVIOR (not a product bug), the closest failure mode, or `other` when it is a model-behavior issue that fits no listed value. Omit only when the report is a product/tool bug with no model-behavior component."}, "task_category": {"type": "string", "enum": ["code_edit", "debug", "explain", "plan", "shell", "search", "review", "other"], "description": "What kind of task the session was doing when the issue occurred, or `other` when it is a clear task that fits no listed value. Omit only if genuinely unclear."}}, "required": ["details", "title", "type"]},
        "execute": _not_implemented('SendFeedback'),
    },
    'ShowOnboardingRolePicker': {
        "name": 'ShowOnboardingRolePicker',
        "description": "Show the onboarding role picker (first-run experience to select the user's role).",
        "input_schema": {"type": "object", "properties": {}},
        "execute": _not_implemented('ShowOnboardingRolePicker'),
    },
    'TaskCreate': {
        "name": 'TaskCreate',
        "description": 'Create a new background task in the task list.',
        "input_schema": {"type": "object", "properties": {"subject": {"type": "string", "description": "A brief title for the task"}, "description": {"type": "string", "description": "What needs to be done"}, "activeForm": {"type": "string", "description": "Present continuous form shown in spinner when in_progress (e.g., \"Running tests\")"}, "metadata": {"type": "object", "description": "Arbitrary metadata to attach to the task"}}, "required": ["description", "subject"]},
        "execute": _not_implemented('TaskCreate'),
    },
    'TaskGet': {
        "name": 'TaskGet',
        "description": 'Get the details of a single task by its id.',
        "input_schema": {"type": "object", "properties": {"taskId": {"type": "string", "description": "The ID of the task to retrieve"}}, "required": ["taskId"]},
        "execute": _not_implemented('TaskGet'),
    },
    'TaskList': {
        "name": 'TaskList',
        "description": 'List all tasks (with their status) in the current task list.',
        "input_schema": {"type": "object", "properties": {}},
        "execute": _not_implemented('TaskList'),
    },
    'TaskUpdate': {
        "name": 'TaskUpdate',
        "description": "Update an existing task's status, description, or result.",
        "input_schema": {"type": "object", "properties": {"taskId": {"type": "string", "description": "The ID of the task to update"}, "subject": {"type": "string", "description": "New subject for the task"}, "description": {"type": "string", "description": "New description for the task"}, "activeForm": {"type": "string", "description": "Present continuous form shown in spinner when in_progress (e.g., \"Running tests\")"}, "status": {"type": "string", "enum": ["pending", "in_progress", "completed", "deleted"], "description": "New status for the task"}, "addBlocks": {"type": "array", "items": {"type": "string"}, "description": "Task IDs that this task blocks"}, "addBlockedBy": {"type": "array", "items": {"type": "string"}, "description": "Task IDs that block this task"}, "owner": {"type": "string", "description": "New owner for the task"}, "metadata": {"type": "object", "description": "Metadata keys to merge into the task. Set a key to null to delete it."}}, "required": ["taskId"]},
        "execute": _not_implemented('TaskUpdate'),
    },
}

# 共 24 个契约工具

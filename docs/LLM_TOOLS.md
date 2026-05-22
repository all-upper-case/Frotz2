# LLM Tool Operations

This document defines the intended engine-side tool vocabulary for Frotz2. These are not manual approval prompts. They are structured operations the LLM can request, the engine can validate, and the debug/audit views can optionally explain.

## Goals

- Give the LLM a small, memorable set of clearly documented operations.
- Protect the engine from typos, malformed fields, impossible state, and ambiguous targets.
- Preserve compatibility with the current `Description` and `Location` update style while moving toward canonical tool names.
- Produce turn reports that show what happened without interrupting normal play.

## Visibility Model

Tool calls should normally apply automatically after validation.

- `quiet`: apply valid calls silently and show narration.
- `summary`: show compact warnings for rejected, partial, or expensive turns.
- `debug`: show accepted/rejected tool calls and reasons.
- `audit`: retain full request, response, pre-state, post-state, and validation details.

Manual approval should be reserved for explicit repair workflows, risky bulk edits, or future settings where the player deliberately asks for approval mode.

## Canonical Operations

### `describe_entity`

Create or update an entity description.

Required fields:

```json
{
  "tool": "describe_entity",
  "target": "entity id, exact name, or alias",
  "description": "New description text"
}
```

Optional fields:

```json
{
  "aliases": ["short name", "alternate reference"],
  "entity_type": "item|body_part|character|room|player",
  "visibility": "visible|hidden"
}
```

Compatibility aliases: `Description`, `create_item`, `update_item`.

### `move_entity`

Move an existing entity to a new location or owner/container.

Required fields:

```json
{
  "tool": "move_entity",
  "target": "entity id, exact name, or alias",
  "location": "here|inventory|worn|body|void|nowhere|room id|character id|character name"
}
```

Compatibility aliases: `Location`.

### `create_entity`

Create a new non-character entity with a stable ID, display name, description, aliases, type, and initial location.

Required fields:

```json
{
  "tool": "create_entity",
  "name": "display name",
  "description": "Initial description",
  "entity_type": "item|body_part",
  "location": "here|inventory|worn|body|void|room id|character id|character name"
}
```

Optional fields:

```json
{
  "aliases": ["short name"],
  "visible": true,
  "carryable": true
}
```

### `update_player`

Update player-specific state without relying on ambiguous names like `self`.

Required fields:

```json
{
  "tool": "update_player",
  "description": "Updated player description"
}
```

Optional fields can later include mood/status fields once the state model supports them.

### `create_character`

Create or update a character/NPC as a first-class entity.

Required fields:

```json
{
  "tool": "create_character",
  "name": "display name",
  "description": "Character description"
}
```

Optional fields:

```json
{
  "aliases": ["short name"],
  "location": "here|room id|void"
}
```

### `update_character`

Update an existing character without treating them as an item.

Required fields:

```json
{
  "tool": "update_character",
  "target": "character id, exact name, or alias",
  "description": "Updated character description"
}
```

### `set_entity_visibility`

Reveal or hide an entity without moving it.

Required fields:

```json
{
  "tool": "set_entity_visibility",
  "target": "entity id, exact name, or alias",
  "visible": true
}
```

### `append_memory`

Add compact narrative memory without changing physical state.

Required fields:

```json
{
  "tool": "append_memory",
  "summary": "One short continuity note"
}
```

Compatibility alias: `narrative_summary_update` outside `state_updates`.

## Validation Rules

Every tool call should produce a status object in the turn report.

Common accepted statuses:

- `accepted`: applied exactly as requested.
- `accepted_with_repair`: applied after a safe compatibility repair, such as mapping `Description` to `describe_entity`.

Common rejected statuses:

- `invalid_schema`: required fields were missing or invalid.
- `unknown_tool`: tool name was not recognized.
- `missing_target`: target did not resolve to an existing entity and the tool cannot create one.
- `ambiguous_target`: target matched multiple entities and needs disambiguation.
- `invalid_location`: requested location is not allowed or does not exist.
- `invalid_entity_type`: requested operation is not valid for that entity type.
- `rejected_error_response`: provider returned an error-shaped response.

Ignored statuses:

- `ignored_duplicate`: requested change was already true.
- `ignored_empty`: requested change had no meaningful content.

## Turn Report Shape

A future turn report should look roughly like this:

```json
{
  "turn_id": "turn_00123",
  "transparency_level": "summary",
  "operation": "dm_turn",
  "requested_tools": 3,
  "accepted_tools": 2,
  "rejected_tools": 1,
  "warnings": ["One move target was ambiguous."],
  "tool_results": [
    {
      "tool": "describe_entity",
      "target": "silver key",
      "status": "accepted",
      "entity_id": "item_key"
    },
    {
      "tool": "move_entity",
      "target": "key",
      "status": "ambiguous_target",
      "matches": ["item_key", "item_rusty_key"]
    }
  ]
}
```

## Implementation Notes

- Keep the existing prompt output compatible until the new tool dispatcher exists.
- Build the dispatcher as engine code, not prompt-only convention.
- Prefer resolving by stable IDs first, exact names second, aliases third, and partial matches last.
- Ambiguous partial matches should not mutate state; they should create pending ambiguity for the player or a repair flow.
- Use the turn packet as the source of truth for what the LLM is allowed to reference.

# LLM Tool Operations

This document defines the intended engine-side tool vocabulary for Frotz2. These are not manual approval prompts. They are structured operations the LLM can request, the engine can validate, and the debug/audit views can optionally explain.

## Goals

- Give the LLM a small, memorable set of clearly documented operations.
- Protect the engine from typos, malformed fields, impossible state, and ambiguous targets.
- Preserve compatibility with the current `Description` and `Location` update style while moving toward canonical tool names.
- Produce turn reports that show what happened without interrupting normal play.
- Make ownership and body/worn/held distinctions explicit for both the player and NPCs.
- Keep the saved game state synchronized with the narrative: if the model narrates a persistent physical change, the State Manager should request the matching tool operation after the Narrator writes the prose.

## Current Runtime Support

`WorldManager.apply_outcome()` now writes a compact `tool_results` list back onto each processed outcome. This is the runtime dispatcher/report model, still growing operation by operation.

Currently covered:

- compatibility alias reporting for legacy `Description` and `Location` updates
- accepted/repaired reports for item descriptions, item creation, item movement, player description updates, character create/update/movement, visibility updates, room description/creation, room connections, and `append_memory`
- rejected reports for malformed updates, unknown tool names, missing move targets, missing owners, missing owner slots, invalid owner slots, missing rooms, missing directions, empty descriptions, invalid locations, and missing placement fields
- duplicate/no-op reporting in several first-pass paths, such as unchanged player descriptions, unchanged character descriptions, unchanged visibility, and schema-level duplicate list cleanup
- recent-turn storage of compact tool results so later prompts can see what the engine accepted or rejected
- basic frontend turn-report display so rejected/ignored tool results are visible after a turn
- transactional item movement so invalid destinations do not remove the item from its previous valid location
- explicit non-carryable fixture/furniture/scenery support through `entity_type` and `carryable: false`

Still pending:

- fuller duplicate/no-op detection across every tool path
- fuller ambiguous target and ambiguous owner reporting
- polished frontend transparency controls for quiet/summary/debug/audit views
- richer non-present entity handling beyond `void`/`nowhere`/offscreen placement
- Matrix editing for rooms, exits, characters, player state, and narrative memory

## Narrative-State Synchronization

Frotz2 now uses a narrative-first split for ordinary free-form turns. The Narrator writes player-facing prose only. The State Manager then treats tools as the persistence layer for the story. Narration can describe events freely, but any concrete fact that should remain true after the turn must be represented through a State Manager tool operation.

Common required mappings:

- Player takes or receives an item: `move_entity` with `owner: "player"` and `slot: "held"`.
- Player drops or sets down an item: `move_entity` with `location: "here"`.
- Player wears an item: `move_entity` with `owner: "player"` and `slot: "worn"`.
- Player removes a worn item but keeps it: `move_entity` with `owner: "player"` and `slot: "held"`.
- Player body changes persistently: `create_entity` or `describe_entity` with `owner: "player"` and `slot: "body"`, plus `update_player` when the overall player description changes.
- NPC carries, wears, or has a body-part entity: `move_entity` or `create_entity` with the NPC as `owner` and `slot` set to `held`, `worn`, or `body`.
- A new persistent object appears: `create_entity`.
- An object becomes hidden or visible: `set_entity_visibility`.
- A new NPC is present: `create_character`, using `location` when the character should appear somewhere specific.
- An existing NPC enters, leaves, follows, waits in, or moves to a concrete place: `move_character`.
- A durable fact has no direct physical state yet: `append_memory`.
- A concrete room or named area becomes established: `describe_room`.
- A concrete path, doorway, hallway, stairway, or direction connects rooms: `connect_rooms`.

Character room movement now has first-class support through `move_character`, but broader NPC state still needs future refinement around schedules, offscreen intent, following behavior, and ambiguity handling.

## Visibility Model

Tool calls should normally apply automatically after validation.

- `quiet`: apply valid calls silently and show narration.
- `summary`: show compact warnings for rejected, partial, or expensive turns.
- `debug`: show accepted/rejected tool calls and reasons.
- `audit`: retain full request, response, pre-state, post-state, and validation details.

Manual approval should be reserved for explicit repair workflows, risky bulk edits, or future settings where the player deliberately asks for approval mode.

## Location And Ownership Model

The current engine has several partially overlapping ideas: room items, player inventory, worn items, body parts, character items, and void/non-present objects. The canonical tool vocabulary should make these distinctions explicit without becoming fussy.

Use these fields consistently:

- `location`: where an entity is in the world when it is not owned by a person. Allowed values are `here`, a room ID/name, `void`, or `nowhere`.
- `owner`: the player or NPC who owns, wears, carries, or has the entity as a body part. Use `player`, a character ID, an exact character name, or a resolvable alias.
- `slot`: the relationship between an owned entity and its owner. Allowed values are `held`, `worn`, and `body`.

Slot meanings:

- `held`: inventory/possessions; the entity is carried or held by the owner.
- `worn`: clothing, gear, jewelry, or other worn/attached-but-removable objects.
- `body`: a body part or inherent part of the owner.

Rules:

- `owner` and `slot` travel together. If a tool call names an NPC or player as the owner, it should also provide `slot`.
- `body` should normally pair with `entity_type: "body_part"`.
- `worn` should not imply `held`; if an item is worn, it belongs in the worn slot.
- `void` and `nowhere` are not owners and must not be combined with `owner` or `slot`.
- For compatibility, legacy player locations `inventory`, `worn`, and `body` map to `owner: "player"` with slots `held`, `worn`, and `body` respectively.
- If a target owner matches multiple characters, the engine should reject the call as `ambiguous_target` rather than guessing.

Examples:

```json
{
  "tool": "move_entity",
  "target": "silver ring",
  "owner": "Mara",
  "slot": "worn"
}
```

```json
{
  "tool": "create_entity",
  "name": "left hand",
  "description": "A steady left hand.",
  "entity_type": "body_part",
  "owner": "Mara",
  "slot": "body"
}
```

```json
{
  "tool": "move_entity",
  "target": "brass lantern",
  "location": "void"
}
```

## Room And Map Model

Rooms live in `world.data["rooms"]` and are connected through each room's `exits` dictionary. The State Manager can now create/update named rooms and connect them through a limited room toolset.

Rules:

- Prefer semantic room names and IDs for meaningful rooms, such as Kitchen or Back Patio.
- Use `describe_room` when the narration establishes a persistent named room or area.
- Use `connect_rooms` when the narration establishes a concrete path, doorway, hallway, stairway, or cardinal direction.
- Unknown/stub rooms can still exist as placeholders created from `new_exits`; Architect or the State Manager can later fill them in.
- Room descriptions should include obvious exits naturally in prose.

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

Compatibility aliases: `Description`, `update_item`.

### `move_entity`

Move an existing entity to a world location or to a player/NPC ownership slot.

Required fields for a room/void move:

```json
{
  "tool": "move_entity",
  "target": "entity id, exact name, or alias",
  "location": "here|void|nowhere|room id|room name"
}
```

Required fields for a person/NPC move:

```json
{
  "tool": "move_entity",
  "target": "entity id, exact name, or alias",
  "owner": "player|character id|character name|character alias",
  "slot": "held|worn|body"
}
```

Compatibility aliases: `Location`. Legacy `location` values of `inventory`, `worn`, and `body` mean the player slots `held`, `worn`, and `body`.

### `create_entity`

Create a new non-character entity with a stable ID, display name, description, aliases, type, and initial placement.

Required fields for a room/void entity:

```json
{
  "tool": "create_entity",
  "name": "display name",
  "description": "Initial description",
  "entity_type": "item|body_part|fixture|furniture|scenery",
  "location": "here|void|room id|room name"
}
```

Required fields for a player/NPC-owned entity:

```json
{
  "tool": "create_entity",
  "name": "display name",
  "description": "Initial description",
  "entity_type": "item|body_part",
  "owner": "player|character id|character name|character alias",
  "slot": "held|worn|body"
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

For furniture, built-ins, large appliances, doors, windows, tubs, counters, beds, couches, tables, fixtures, or scenery, use `entity_type: "fixture"`, `"furniture"`, or `"scenery"` and `carryable: false`.

### `describe_room`

Create or update a room description. This is the canonical room-state operation for named rooms or areas that the narration establishes as persistent.

Required fields for creating or updating a room:

```json
{
  "tool": "describe_room",
  "target": "room id, exact room name, or omitted when name is supplied",
  "name": "Kitchen",
  "description": "A clean kitchen with stainless appliances."
}
```

Optional fields:

```json
{
  "exits": {
    "south": "Living Room",
    "east": "Pantry"
  }
}
```

Notes:

- If `target` or `name` resolves to an existing room, that room is updated.
- If no room resolves, the engine creates a semantic room ID from the supplied name.
- Descriptions are stripped of generated inventory lines before being stored as the room's base description.
- Exits supplied as a dictionary are connected bidirectionally when possible.

### `connect_rooms`

Connect two rooms through a concrete exit/path.

Required fields:

```json
{
  "tool": "connect_rooms",
  "from": "here|room id|room name",
  "direction": "north|south|east|west|up|down",
  "to": "room id or room name"
}
```

Optional fields:

```json
{
  "to_name": "Kitchen",
  "bidirectional": true
}
```

Notes:

- If the destination room does not exist, the engine creates it with a semantic room ID.
- By default, the opposite exit is added on the destination room.
- Use this when narration establishes a concrete path, doorway, hallway, stairway, or directional relationship.

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
  "location": "here|room id|room name|void|nowhere|offscreen|absent"
}
```

### `update_character`

Update an existing character without treating them as an item. A description, aliases, or location may be supplied.

Example:

```json
{
  "tool": "update_character",
  "target": "character id, exact name, or alias",
  "description": "Updated character description",
  "location": "nowhere"
}
```

### `move_character`

Move an existing character between rooms or remove them from present room lists.

Use this whenever narration establishes that an NPC enters, leaves, follows, waits in, or moves to a concrete location.

Required fields:

- `tool`: `move_character`
- `target`: character id, exact name, or alias
- `location`: `here`, room id, room name, `void`, `nowhere`, `offscreen`, `absent`, or equivalent non-present language

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

Compatibility alias: `entry` inside `state_updates`, and `narrative_summary_update` outside `state_updates`.

## Validation Rules

Every tool call should produce a status object in the turn report.

Common accepted statuses:

- `accepted`: applied exactly as requested.
- `accepted_with_repair`: applied after a safe compatibility repair, such as mapping `Description` to `describe_entity`.

Common rejected statuses:

- `invalid_schema`: required fields were missing or invalid.
- `unknown_tool`: tool name was not recognized.
- `missing_target`: target did not resolve to an existing entity and the tool cannot create one.
- `missing_owner`: owner did not resolve to an existing player or character.
- `missing_slot`: owner was provided without a valid held/worn/body slot.
- `missing_room`: room reference was missing or did not resolve where required.
- `missing_direction`: a room-connection operation did not include a valid direction.
- `ambiguous_target`: target matched multiple entities and needs disambiguation.
- `ambiguous_owner`: owner matched multiple characters and needs disambiguation.
- `invalid_location`: requested location is not allowed or does not exist.
- `invalid_slot`: requested slot is not allowed for the owner or entity type.
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

- Keep the existing prompt output compatible while the dispatcher is filled in operation by operation.
- Build the dispatcher as engine code, not prompt-only convention.
- Prefer resolving by stable IDs first, exact names second, aliases third, and partial matches last.
- Ambiguous partial matches should not mutate state; they should create pending ambiguity for the player or a repair flow.
- Use the turn packet as the source of truth for what the LLM is allowed to reference.
- Keep recent full-turn context separate from compact `append_memory` summaries. The full-turn buffer is for immediate continuity; memory summaries are for long-range continuity.

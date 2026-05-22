# LLM JSON Contracts

Frotz2 asks the model for JSON objects and validates the response before mutating world state. The validation is intentionally lightweight: it rejects error-shaped or clearly malformed responses, while `WorldManager` still owns schema repair for older saves and normal state defaults.

The model-facing tool vocabulary is documented separately in `docs/LLM_TOOLS.md`. Those tool operations are intended to apply automatically after engine validation, with toggleable visibility levels for summary/debug/audit views. They are not intended to require manual approval for every ordinary state update.

The per-turn context packet is documented in `docs/TURN_CONTEXT.md`. It should carry the authoritative current state, exact player command, recent full turns, and compact narrative memory into each DM turn.

## Shared Rules

- The response must be a JSON object.
- Responses with an `error` field are rejected before state mutation.
- `state_updates` must be a list when present. Missing or null `state_updates` becomes an empty list where the contract allows it.
- `new_exits` must be a list when present. Missing or null `new_exits` becomes an empty list where the contract allows it.
- Required string fields must be present and non-empty.
- Tool calls should use canonical names from `docs/LLM_TOOLS.md` once the dispatcher exists; compatibility aliases remain supported during migration.
- The turn packet should be treated as higher priority than older prose memory when they disagree.

## Genesis

Used by `LLMInterface.generate_genesis()` during `/reset`.

Required fields:

```json
{
  "intro_text": "Opening narration shown to the player.",
  "starting_room_name": "Name of the first room.",
  "starting_room_description": "Base description of the first room.",
  "player_description": "Initial player description.",
  "narrative_thread": "Compact starting situation summary.",
  "blueprint": "Short world plan for future expansion.",
  "new_exits": ["north"],
  "state_updates": []
}
```

If validation fails, `/reset` returns a readable `Genesis Failed: ...` response and does not initialize a new world.

## Room Generation

Used by `LLMInterface.generate_room()` when the player moves into an unexplored room stub.

Required fields:

```json
{
  "room_name": "Name of the generated room.",
  "room_description": "Base room description.",
  "new_exits": ["south"],
  "blueprint_update": "Optional updated world plan.",
  "state_updates": []
}
```

If validation fails, the player is moved back to the previous room and the save file is updated to avoid leaving them inside an unfinished room stub.

## Turn Handling

Used by `LLMInterface.process_turn()` for free-form player actions and major Matrix reality-shift narration.

Required fields:

```json
{
  "narrative": "The player-facing response.",
  "narrative_summary_update": "Optional compact memory update.",
  "state_updates": []
}
```

If validation fails, no state updates are applied and the route returns a readable failure response with the current HUD state.

## Fixer

Used by the Matrix editor's AI-assisted item-description rewrite workflow.

Required fields:

```json
{
  "description": "Replacement item description."
}
```

`WorldManager.god_mode_update()` validates fixer output with `validate_fix_response()` before changing item descriptions. Valid fixer output is applied normally. Error-shaped, non-object, or missing-description output is rejected and logged in the Matrix continuity message without changing the existing item description.

# Turn Context Contract

The model should not rely on compact memory summaries alone to understand what is happening. Each DM turn should receive a structured packet that combines the current authoritative state, the exact player command, recent full-turn transcript, and compact long-range memory.

## Goals

- Improve immediate continuity without a large token increase.
- Keep world state authoritative and inspectable.
- Separate short-range turn context from long-range narrative memory.
- Make tool-call validation and turn reports easier to reason about.

## Current Runtime Status

Batch 1 added a first `WorldManager.get_turn_packet()` helper and includes that packet at the top of the formatted prompt context. It captures the current room, player state, visible room entities, present characters, pending ambiguity state, recent full turns, and narrative memory. The app still formats the packet into the existing text context dump rather than passing a separate structured object all the way through the LLM interface.

Ordinary free-form turns now use a narrative-first split:

1. The Narrator receives the current turn context and writes prose-only output.
2. The State Manager receives the authoritative before-state, player action, narrator output, and tool contract.
3. The State Manager compiles durable claims into `state_updates`, warnings, unsupported claims, and narrative memory updates.
4. The engine validates and applies accepted operations.
5. Compact tool results are stored into recent-turn continuity.

## Recommended Packet Shape

```json
{
  "operation": "dm_turn",
  "turn_id": "turn_00123",
  "player_command": "open the brass box",
  "current_state": {
    "room": {
      "id": "room_attic",
      "name": "Attic",
      "description": "A quiet attic with a low ceiling.",
      "exits": ["down"]
    },
    "player": {
      "description": "The current player description.",
      "inventory": ["brass key"],
      "worn": [],
      "body": []
    },
    "present_entities": [
      {
        "id": "item_box",
        "name": "brass box",
        "type": "item",
        "location": "room_attic",
        "visible": true,
        "aliases": ["box"]
      }
    ],
    "present_characters": [
      {
        "id": "npc_mara",
        "name": "Mara",
        "description": "A calm traveler.",
        "held": ["lantern"],
        "worn": ["silver ring"],
        "body": ["left hand"]
      }
    ],
    "pending_ambiguity": null
  },
  "recent_full_turns": [
    {
      "player_command": "look at the box",
      "narrative": "The brass box is small and locked.",
      "accepted_tools": [
        {"tool": "describe_entity", "target": "brass box", "status": "accepted"}
      ],
      "warnings": []
    }
  ],
  "narrative_memory": [
    "The player found the attic after climbing the ladder."
  ],
  "tool_contract": "See docs/LLM_TOOLS.md"
}
```

## Context Layers

Use three different layers on purpose:

- `current_state`: authoritative facts the engine believes right now.
- `recent_full_turns`: the last few full player commands, model outputs, accepted tools, rejected tools, and warnings.
- `narrative_memory`: compact summaries created by `append_memory` for long-range continuity.

The recommended default is the last three full turns. That should usually be enough to preserve immediate intent, pronouns, unresolved references, and the model's last visible narration. If a turn is unusually large, the engine can truncate older full turns first and preserve the latest command/output pair.

## Prompting Rule

The turn packet should be treated as higher priority than prose memory. If the packet says an entity is in the void, worn by an NPC, or present in the room, that is the current truth even if older narrative memory implies something different.

## Storage Rule

Recent full turns should be saved with the game state or rebuilt from turn reports. Debug-only files like `last_turn_debug.txt` are useful for development, but they should not be the only source of runtime continuity.

## Validation Rule

The LLM may narrate freely, but physical state changes should come through the documented tools. The engine should record which proposed tool calls were accepted, repaired, rejected, or ignored, then feed that compact result into the next turn's `recent_full_turns`.

## Auditor Context

Audit mode should not always send one fixed giant context bundle. The runtime now exposes selectable context sections so the user can choose a quick, normal, or deep audit, or manually select categories.

Current categories:

- active lore
- full save JSON
- rendered main-model context dump
- player state
- current room
- rooms/exits/map
- items/entities
- characters/NPCs
- narrative memory
- recent turns
- core prompts
- runtime tool contract
- tool documentation
- debug-log exclusion note

The rendered context dump intentionally overlaps with other categories and should mostly be reserved for prompt/context debugging. For state consistency audits, the raw save sections are usually a cleaner source of truth.

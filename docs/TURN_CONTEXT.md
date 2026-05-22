# Turn Context Contract

The model should not rely on compact memory summaries alone to understand what is happening. Each DM turn should receive a structured packet that combines the current authoritative state, the exact player command, recent full-turn transcript, and compact long-range memory.

## Goals

- Improve immediate continuity without a large token increase.
- Keep world state authoritative and inspectable.
- Separate short-range turn context from long-range narrative memory.
- Make tool-call validation and turn reports easier to reason about.

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

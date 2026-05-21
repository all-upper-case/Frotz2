# Architecture Notes

Frotz2 is a small Flask app organized around a browser terminal, a persistent world model, and an LLM interface that returns structured JSON.

## Runtime Flow

1. `templates/index.html` loads the terminal UI and `static/script.js`.
2. On page load, the frontend calls `/get_state`.
3. If no save exists, the frontend calls `/reset`, which asks `LLMInterface.generate_genesis()` to build the initial world from `lore.txt`.
4. Player commands go to `/command`.
5. Simple commands are resolved deterministically. Movement may either enter an existing room or trigger LLM room generation for an unexplored stub.
6. Free-form commands call `process_ai_turn()`, which sends lore, narrative history, and a world context dump to the LLM.
7. The LLM response is parsed as JSON and applied through `WorldManager.apply_outcome()`.
8. Updated state is saved under `saves/<world_name>.json` and returned to the UI.

## Core Modules

### `main.py`

Owns HTTP routes and high-level game flow. It decides whether a command is deterministic, movement-related, model-management, debug-related, or an LLM turn.

Important route groups:

- Gameplay: `/`, `/get_state`, `/reset`, `/command`
- Models: `/models`, `/set_model`
- State editor: `/get_god_state`, `/god_update`
- Debug: `/get_debug`
- Local helper workflow: `/update-files`

### `world_manager.py`

Owns persisted game state. It repairs older save schemas, manages room/item/player structures, resolves movement, creates room stubs, applies LLM state updates, and emits compact context for the LLM.

Key data areas:

- `player`: current room, inventory, worn/body objects, description
- `rooms`: room descriptions, exits, visible items, characters
- `items`: item descriptions, aliases, visibility, carryability
- `characters`: NPC data and carried items
- `narrative_log`: compact memory of previous turns
- `meta`: token usage and other counters

### `llm_interface.py`

Owns API calls and response parsing. It uses prompt templates from `system_prompts.py`, requests JSON output, tracks token usage, and writes debug artifacts.

The current backend is Venice-compatible. `VENICE_API_KEY` is preferred, with `MISTRAL_API_KEY` retained as a legacy fallback.

### Frontend

The frontend is deliberately lightweight:

- `static/script.js` handles startup, command submission, HUD rendering, model commands, debug display, local settings, and the state editor modal.
- `static/style.css` provides the CRT theme, clean dark theme, responsive layout, HUD, and modal styling.

## Generated State And Artifacts

The engine creates or updates files while running:

- `saves/*.json` for world state
- `backups/*.json` for reset backups
- `debug_log.txt` and `debug_logs/*.txt` for LLM outputs
- `last_turn_debug.txt` for recent prompt/response inspection

Existing artifacts remain in the repo as historical context. New runtime artifacts are ignored by `.gitignore` so the repository stays easier to navigate.

## Design Tensions

- The app is both a game engine and a personal authoring/debugging workspace.
- The LLM can invent state, so `WorldManager` includes normalization and schema-repair behavior.
- Debug artifacts are useful while tuning prompts, but they can contain sensitive prompts, world state, or generated content.
- Dev helper endpoints are convenient for private local/Replit workflows, but they should stay out of public deployment paths.
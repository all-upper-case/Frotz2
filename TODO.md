# TODO

A practical backlog for turning the current prototype into a tidier personal engine. The broader product direction now lives in `docs/STEWARDSHIP_ROADMAP.md`, the planned LLM tool vocabulary lives in `docs/LLM_TOOLS.md`, and the turn-context packet lives in `docs/TURN_CONTEXT.md`.

## Recently Completed

- Added root project docs plus architecture and workflow notes.
- Added `docs/LLM_CONTRACTS.md` for expected model response shapes.
- Added `docs/STEWARDSHIP_ROADMAP.md` for the long-term stewardship direction.
- Added `docs/LLM_TOOLS.md` for canonical LLM tool operations, compatibility aliases, validation statuses, visibility levels, and player/NPC ownership slots.
- Added `docs/TURN_CONTEXT.md` for the planned authoritative turn packet and recent full-turn transcript strategy.
- Clarified that tool-call transparency is toggleable observability, not mandatory approval for every normal state change.
- Added lightweight LLM response validation for genesis, room generation, and turn narration before state mutation.
- Added a pytest smoke-test baseline for app import, uninitialized routes, no-key reset behavior, deterministic commands, LLM contracts, and save/load roundtrips.
- Hardened the frontend debug modal empty/error states.
- Reworked Matrix editor details rendering to avoid injecting item aliases/descriptions through string-built HTML.
- Removed duplicated debug-modal click-handler logic.
- Renamed package metadata away from starter-template defaults.
- Updated `.gitignore` so future runtime saves/debug logs stay local unless intentionally added.

## Current Priority: Consistency And Tool Robustness

- Wire `validate_fix_response()` into the Matrix AI fixer path in `world_manager.py` with focused tests for accepted and rejected fixer outputs.
- Implement the first canonical tool dispatcher that maps compatibility aliases like `Description` and `Location` to typed engine operations.
- Implement player/NPC ownership slots for `held`, `worn`, and `body` so moving or creating an entity on a character is never ambiguous.
- Add per-tool validation statuses: accepted, accepted_with_repair, invalid_schema, unknown_tool, missing_target, missing_owner, missing_slot, ambiguous_target, ambiguous_owner, invalid_location, invalid_slot, invalid_entity_type, ignored_duplicate, and ignored_empty.
- Implement resolvable disambiguation for visible items, with tests for duplicate names and overlapping words.
- Add structured turn packets from `WorldManager` and document their contract.
- Add a recent full-turn buffer, separate from compact narrative memory, and include it in each DM turn prompt.
- Extend lookup/state handling to characters and non-present entities after the visible-item path is stable.

## Documentation

- Add examples for authoring safe lore files and switching between `LoreBooks/` entries.
- Keep `docs/LLM_CONTRACTS.md`, `docs/LLM_TOOLS.md`, and `docs/TURN_CONTEXT.md` in sync as model-backed workflows are added.
- Keep `README.md` focused on setup, project shape, and everyday usage.

## Repository Hygiene

- Decide whether historical saves and debug logs should remain in the repo or move to a private archive.
- Keep generated saves, debug logs, and last-turn artifacts out of future commits.
- Consider moving long-lived example saves into `examples/` if they are useful fixtures.
- Run `poetry lock` or an equivalent dependency refresh in an environment with Poetry available so the lock file includes the dev test dependency.

## Engine Behavior

- Run the new pytest suite in a Python-enabled environment and fix any failures found there.
- Split command parsing from Flask route handlers once command behavior grows.
- Add safer handling for malformed or partial LLM JSON responses inside `LLMInterface` if provider behavior changes.
- Consider a world export/import command for moving saves between machines or deployments.

## Frontend

- Add transparency controls for quiet, summary, debug, and audit modes once turn reports exist.
- Add command history with up/down arrow recall.
- Improve visual styling for frontend error messages so failures read as deliberate UI states.
- Consider separating Matrix editor logic into its own frontend module if it keeps growing.

## Product Roadmap

- Add running token and cost accounting for input tokens, output tokens, total tokens, and estimated costs.
- Revamp inventory, body parts, worn items, NPC possessions, void/non-present entities, and player-vs-NPC distinctions through the world-state manager work.
- Add better undo, repair, and edit workflows for player actions and model outputs.
- Research Venice.ai docs before adding UI controls for temperature, max output tokens, reasoning intensity, and related params.
- Add clearer scenario creation, save slots, load flows, and export/import.
- Add better transparency into tool-call accuracy, success/failure, completeness, and consistency warnings.
- Build a stronger world-state manager after the current behavior has test coverage.

## Local Workflow

- Keep dev helper endpoints private to trusted local/Replit environments.
- Require `DEVTOOLS_TOKEN` in any environment that can be reached from another machine.

## Possible Refactors

- Move route groups into blueprints once the app grows beyond a single-file Flask entrypoint.
- Introduce dataclasses or lightweight schemas for player, room, item, and LLM output structures.
- Move debug artifact writing behind a small logger/helper so it can be toggled by environment.
- Make save directory, lore file, and debug paths configurable.

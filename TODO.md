# TODO

A practical backlog for turning the current prototype into a tidier personal engine. The broader product direction now lives in `docs/STEWARDSHIP_ROADMAP.md`, the planned LLM tool vocabulary lives in `docs/LLM_TOOLS.md`, and the turn-context packet lives in `docs/TURN_CONTEXT.md`.

## Recently Completed

- Added root project docs plus architecture and workflow notes.
- Added `docs/LLM_CONTRACTS.md` for expected model response shapes.
- Added `docs/STEWARDSHIP_ROADMAP.md` for the long-term stewardship direction.
- Added `docs/LLM_TOOLS.md` for canonical LLM tool operations, compatibility aliases, validation statuses, visibility levels, and player/NPC ownership slots.
- Added `docs/TURN_CONTEXT.md` for the planned authoritative turn packet and recent full-turn transcript strategy.
- Added a bounded `recent_turns` buffer to save data and included recent full turns in the DM context dump.
- Added initial player/NPC ownership slots for `held`, `worn`, and `body`, including legacy NPC `items` compatibility.
- Added support for `move_entity` and `create_entity` payloads that use `owner` plus `slot`.
- Extended visible-item lookup and context dumps to include present NPC held/worn/body entities.
- Added neutral tests for recent-turn recording, NPC held/worn/body placement, and context-dump visibility.
- Added the first `WorldManager.apply_outcome()` tool-result reporting pass for accepted/repaired/rejected state updates.
- Added recent-turn storage/display of compact tool results so the next prompt can see what the engine actually accepted.
- Added focused tests for accepted legacy aliases, missing move targets, missing owner slots, and recent-turn tool-result context.
- Clarified that tool-call transparency is toggleable observability, not mandatory approval for every normal state change.
- Added lightweight LLM response validation for genesis, room generation, and turn narration before state mutation.
- Wired Matrix AI fixer responses through `validate_fix_response()` so malformed/error-shaped fixer output is rejected before item descriptions change.
- Added focused tests for accepted and rejected Matrix AI fixer responses.
- Added a pytest smoke-test baseline for app import, uninitialized routes, no-key reset behavior, deterministic commands, LLM contracts, and save/load roundtrips.
- Hardened the frontend debug modal empty/error states.
- Reworked Matrix editor details rendering to avoid injecting item aliases/descriptions through string-built HTML.
- Removed duplicated debug-modal click-handler logic.
- Renamed package metadata away from starter-template defaults.
- Updated `.gitignore` so future runtime saves/debug logs stay local unless intentionally added.

## Current Priority: Consistency And Tool Robustness

- Expand the canonical tool dispatcher beyond item/player updates to first-class character updates, visibility updates, stricter room/location validation, duplicate detection, and ambiguity reporting.
- Tighten player/NPC ownership slot validation so rejected owner/slot moves are visible in frontend turn reports, not only stored in recent-turn context.
- Add remaining per-tool validation statuses: ambiguous_target, ambiguous_owner, invalid_entity_type, ignored_duplicate, and fuller invalid_location coverage.
- Implement resolvable disambiguation for visible items, with tests for duplicate names and overlapping words.
- Promote the current context dump into a structured turn packet object before formatting it for prompts.
- Extend lookup/state handling to non-present entities after the visible-item and present-character paths are stable.

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

- Run the new pytest suite in a Python-enabled environment and fix any failures found there. Python is not installed on the current work PC, so local execution has intentionally not been used.
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

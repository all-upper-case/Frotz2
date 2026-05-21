# TODO

A practical backlog for turning the current prototype into a tidier personal engine.

## Recently Completed

- Added root project docs plus architecture and workflow notes.
- Added `docs/LLM_CONTRACTS.md` for expected model response shapes.
- Added lightweight LLM response validation for genesis, room generation, and turn narration before state mutation.
- Added a pytest smoke-test baseline for app import, uninitialized routes, no-key reset behavior, deterministic commands, LLM contracts, and save/load roundtrips.
- Hardened the frontend debug modal empty/error states.
- Reworked Matrix editor details rendering to avoid injecting item aliases/descriptions through string-built HTML.
- Removed duplicated debug-modal click-handler logic.
- Renamed package metadata away from starter-template defaults.
- Updated `.gitignore` so future runtime saves/debug logs stay local unless intentionally added.

## Documentation

- Add examples for authoring safe lore files and switching between `LoreBooks/` entries.
- Expand `docs/LLM_CONTRACTS.md` if new model-backed workflows are added.
- Keep `README.md` focused on setup, project shape, and everyday usage.

## Repository Hygiene

- Decide whether historical saves and debug logs should remain in the repo or move to a private archive.
- Keep generated saves, debug logs, and last-turn artifacts out of future commits.
- Consider moving long-lived example saves into `examples/` if they are useful fixtures.
- Run `poetry lock` or an equivalent dependency refresh in an environment with Poetry available so the lock file includes the dev test dependency.

## Engine Behavior

- Run the new pytest suite in a Python-enabled environment and fix any failures found there.
- Wire `validate_fix_response()` into the Matrix AI fixer path in `world_manager.py` with focused tests for accepted and rejected fixer outputs.
- Split command parsing from Flask route handlers once command behavior grows.
- Add safer handling for malformed or partial LLM JSON responses inside `LLMInterface` if provider behavior changes.
- Consider a world export/import command for moving saves between machines or deployments.

## Frontend

- Add command history with up/down arrow recall.
- Improve visual styling for frontend error messages so failures read as deliberate UI states.
- Consider separating Matrix editor logic into its own frontend module if it keeps growing.

## Local Workflow

- Keep dev helper endpoints private to trusted local/Replit environments.
- Require `DEVTOOLS_TOKEN` in any environment that can be reached from another machine.

## Possible Refactors

- Move route groups into blueprints once the app grows beyond a single-file Flask entrypoint.
- Introduce dataclasses or lightweight schemas for player, room, item, and LLM output structures.
- Move debug artifact writing behind a small logger/helper so it can be toggled by environment.
- Make save directory, lore file, and debug paths configurable.

# TODO

A practical backlog for turning the current prototype into a tidier personal engine.

## Documentation

- Promote useful notes from `backups/` into root docs when they are still accurate.
- Keep `README.md` focused on setup, project shape, and everyday usage.
- Add examples for authoring safe lore files and switching between `LoreBooks/` entries.
- Document the expected LLM JSON contracts in one place.

## Repository Hygiene

- Decide whether historical saves and debug logs should remain in the repo or move to a private archive.
- Keep generated saves, debug logs, and last-turn artifacts out of future commits.
- Consider moving long-lived example saves into `examples/` if they are useful fixtures.
- Rename package metadata away from the starter-template defaults.

## Engine Behavior

- Add smoke tests for app import, `/get_state`, `/reset` failure behavior when no API key is present, and basic deterministic commands.
- Split command parsing from Flask route handlers once command behavior grows.
- Make the LLM response schema explicit and validate it before applying state updates.
- Add safer handling for malformed or partial LLM JSON responses.
- Consider a world export/import command for moving saves between machines or deployments.

## Frontend

- Remove duplicated modal click-handler code in `static/script.js`.
- Escape user-provided item names/descriptions before injecting them into Matrix editor HTML.
- Add command history with up/down arrow recall.
- Improve empty/error states for model listing, debug payloads, and failed turns.
- Consider separating Matrix editor logic into its own frontend module if it keeps growing.

## Local Workflow

- Keep dev helper endpoints private to trusted local/Replit environments.
- Require `DEVTOOLS_TOKEN` in any environment that can be reached from another machine.
- Add a short `docs/WORKFLOWS.md` later if the ChatGPT/Replit update flow should be preserved as a first-class workflow.

## Possible Refactors

- Move route groups into blueprints once the app grows beyond a single-file Flask entrypoint.
- Introduce dataclasses or lightweight schemas for player, room, item, and LLM output structures.
- Move debug artifact writing behind a small logger/helper so it can be toggled by environment.
- Make save directory, lore file, and debug paths configurable.
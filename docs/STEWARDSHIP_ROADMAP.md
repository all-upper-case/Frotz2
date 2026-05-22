# Stewardship Roadmap

This roadmap is the working product direction for Frotz2. The goal is not just to add features, but to turn the prototype into a reliable personal interactive-fiction engine with strong state continuity, transparent LLM behavior, and better authoring tools.

## Guiding Principle

Frotz2 should treat the world state as the source of truth, and the LLM as a narrator and proposer of structured changes. The engine should know what exists, where it is, who owns it, what just happened, what the model tried to change, and whether those changes succeeded.

## Phase 1: Consistency And State Integrity

This is the current priority.

- Build a resolvable disambiguation flow for overlapping item/entity names.
- Persist pending ambiguity state so follow-up answers like `1`, `second`, or a more specific noun phrase can resolve the original command.
- Expand entity lookup beyond visible items so characters/NPCs, worn objects, body-part entities, inventory, room contents, and void/non-present entities have consistent handling.
- Add a structured turn packet from `WorldManager` that captures current room, visible entities, player state, present characters, pending ambiguity, recent narrative memory, and the exact command being processed.
- Feed that turn packet into LLM prompts as the authoritative state for each turn.
- Improve tests around duplicate names, overlapping words, entity ownership, void items, NPC-held items, and malformed LLM state updates.

## Phase 2: World-State Manager

The current dictionaries work, but the engine needs a clearer state model before it grows much further.

- Introduce a consistent entity model for player, NPCs, rooms, items, body parts, worn objects, inventory objects, and void/non-present objects.
- Separate stable identity from display names and aliases.
- Track ownership and containment explicitly: player inventory, player worn, player body, room contents, NPC inventory, NPC worn, NPC body, void, and nowhere.
- Create a single state-query layer for questions like `what can the player see?`, `what can the player refer to?`, `where is this entity?`, and `who owns this?`.
- Make the Matrix editor read from and write through that state-query layer instead of hand-rolling its own location logic.

## Phase 3: Tool-Call Transparency

The player should be able to see whether the model's proposed state changes were complete, valid, and actually applied.

- Record each LLM response as a turn report with requested tool calls, accepted changes, rejected changes, and warnings.
- Surface a compact version of that report in the debug modal.
- Add explicit status fields for tool-call success, partial success, ignored updates, unknown targets, ambiguous targets, and validation failures.
- Track when the LLM invents impossible state or omits required state updates.
- Add tests for accepted, rejected, and partially applied tool-call batches.

## Phase 4: Editing, Undo, And Repair

Manual correction should become a first-class workflow rather than an emergency hatch.

- Add save snapshots before each player turn and before Matrix edits.
- Add undo for the last turn, including narrative log and entity state.
- Add a clear `repair turn` or `revise last output` workflow that lets the player correct the model without manually editing JSON.
- Add a safer Matrix fixer path with `validate_fix_response()` applied before item descriptions are changed.
- Consider a turn history UI showing prompt, model response, accepted changes, rejected changes, and resulting state.

## Phase 5: Scenario And Save Management

Creating scenarios and managing game states should feel like using the game, not like juggling files.

- Add a scenario selector backed by `LoreBooks/` and active `lore.txt` generation.
- Add scenario metadata: name, genre, description, preferred model parameters, and starting notes.
- Add save slots with friendly names, timestamps, scenario references, and token totals.
- Add export/import for saves and scenarios.
- Keep the existing file-based workflow intact for Replit and power-user editing.

## Phase 6: Token And Cost Accounting

The engine already records total tokens, but it needs a clearer ledger.

- Track cumulative input tokens, output tokens, total tokens, and estimated cost.
- Store token usage by turn and by operation type: genesis, room generation, DM turn, fixer, model listing, and repair.
- Add configurable model pricing data, initially manual and later provider-aware if Venice exposes reliable pricing metadata.
- Show session and lifetime totals in the HUD or debug panel.
- Flag unusually expensive turns.

## Phase 7: LLM Controls

Model settings should be visible and adjustable without code edits.

- Research Venice.ai request parameters before changing the runtime contract.
- Add UI controls for model, temperature, max output tokens, reasoning effort/intensity, and other supported options.
- Persist per-scenario defaults while allowing temporary per-session overrides.
- Include model settings in turn debug reports so behavior is explainable later.
- Validate requested params before sending them to the provider.

## Phase 8: Interface Polish

Once the state layer is more trustworthy, improve the daily feel of the app.

- Add command history and better command recall.
- Improve error styling so failures are legible but not alarming.
- Split the Matrix editor into clearer panels for player, NPCs, room contents, void, and turn report.
- Make debug views easier to scan.
- Keep the terminal feel, but reduce friction for scenario management and state repair.

## Near-Term Implementation Order

1. Wire the remaining fixer validation path safely.
2. Implement resolvable disambiguation for visible items, with tests.
3. Add the first structured turn packet and document its contract.
4. Extend lookup/state handling to characters and non-present entities.
5. Add turn reports for LLM tool-call transparency.
6. Begin the world-state manager refactor only after the above behavior is covered by tests.

## Non-Goals For Now

- Do not remove historical saves or debug logs without an explicit cleanup decision.
- Do not redesign the whole frontend before the state model is more reliable.
- Do not overfit prompts before the engine can accurately describe its own state.
- Do not assume Venice parameters without checking current provider docs first.

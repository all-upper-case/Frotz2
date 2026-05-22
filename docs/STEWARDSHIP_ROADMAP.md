# Stewardship Roadmap

This roadmap is the working product direction for Frotz2. It includes the original stability/TODO work and the newer product direction around consistency, cost tracking, scenario management, LLM controls, and stronger world-state tooling. The goal is not just to add features, but to turn the prototype into a reliable personal interactive-fiction engine with strong state continuity, transparent LLM behavior, and better authoring tools.

## Guiding Principle

Frotz2 should treat the world state as the source of truth, and the LLM as a narrator plus a caller of clearly documented engine tools. The LLM should propose structured operations, the engine should validate and apply safe operations automatically, and the player should be able to inspect what happened at the right level of detail without being forced to approve every ordinary change.

Tool visibility is observability, not a mandatory approval gate. Most turns should flow automatically. Manual intervention belongs in repair, undo, debug, or high-risk workflows.

## Transparency Levels

The engine should support toggleable levels of visibility/intrusiveness:

- `quiet`: normal play; show only narration and standard HUD state.
- `summary`: show compact notices for partial success, ignored updates, high token cost, or consistency warnings.
- `debug`: show the turn report with requested tool calls, accepted changes, rejected changes, warnings, model settings, and token usage.
- `audit`: preserve full prompt/response/state snapshots for deep debugging and repair workflows.

The default should be `quiet` or `summary`, not a stream of approval prompts.

## Phase 1: Consistency And State Integrity

This is the current priority.

- Build a resolvable disambiguation flow for overlapping item/entity names.
- Persist pending ambiguity state so follow-up answers like `1`, `second`, or a more specific noun phrase can resolve the original command.
- Expand entity lookup beyond visible items so characters/NPCs, worn objects, body-part entities, inventory, room contents, and void/non-present entities have consistent handling.
- Add explicit ownership slots for both the player and NPCs: held, worn, and body.
- Add a structured turn packet from `WorldManager` that captures current room, visible entities, player state, present characters, pending ambiguity, recent full turns, recent narrative memory, and the exact command being processed.
- Feed that turn packet into LLM prompts as the authoritative state for each turn.
- Keep recent full-turn transcript separate from compact `append_memory` summaries. The transcript preserves immediate continuity; summaries preserve long-range continuity.
- Improve tests around duplicate names, overlapping words, entity ownership, void items, NPC-held items, NPC-worn items, NPC body parts, and malformed LLM state updates.

## Phase 2: Robust LLM Tooling

The model needs a small, clear tool surface with typo-resistant names and engine-side validation. Prompt text alone is not enough.

- Define canonical tool operations such as `describe_entity`, `move_entity`, `create_entity`, `update_player`, `create_character`, `update_character`, `set_entity_visibility`, and `append_memory`.
- Keep legacy names like `Description` and `Location` as compatibility aliases while steering prompts and docs toward canonical operations.
- Validate each requested tool call before applying it: required fields, known target IDs or resolvable aliases, allowed locations, entity type rules, ownership slots, and owner constraints.
- Return structured per-tool statuses: accepted, rejected, ignored, ambiguous, missing_target, missing_owner, missing_slot, invalid_location, invalid_slot, invalid_schema, and repaired_alias.
- Store those statuses in the turn report for optional display.
- Add tests for valid calls, typo aliases, missing required fields, unknown targets, ambiguous targets, NPC ownership, void movement, and body/worn/held distinctions.

## Phase 3: World-State Manager

The current dictionaries work, but the engine needs a clearer state model before it grows much further.

- Introduce a consistent entity model for player, NPCs, rooms, items, body parts, worn objects, inventory objects, and void/non-present objects.
- Separate stable identity from display names and aliases.
- Track ownership and containment explicitly: player held, player worn, player body, room contents, NPC held, NPC worn, NPC body, void, and nowhere.
- Create a single state-query layer for questions like `what can the player see?`, `what can the player refer to?`, `where is this entity?`, and `who owns this?`.
- Make the Matrix editor read from and write through that state-query layer instead of hand-rolling its own location logic.

## Phase 4: Tool-Call Reports And Consistency Diagnostics

The player should be able to see whether the model's proposed state changes were complete, valid, and actually applied, at the chosen transparency level.

- Record each LLM response as a turn report with requested tool calls, accepted changes, rejected changes, warnings, and token usage.
- Surface a compact version of that report only when the current transparency level calls for it.
- Track when the LLM invents impossible state, omits expected state updates, targets ambiguous entities, contradicts the authoritative turn packet, or forgets recent full-turn context.
- Add a debug view that can show prompt, response, accepted/rejected tool calls, model settings, recent full-turn context, and resulting state.
- Add tests for accepted, rejected, partially applied, and warning-only tool-call batches.

## Phase 5: Editing, Undo, And Repair

Manual correction should become a first-class workflow rather than an emergency hatch.

- Add save snapshots before each player turn and before Matrix edits.
- Add undo for the last turn, including narrative log and entity state.
- Add a clear `repair turn` or `revise last output` workflow that lets the player correct the model without manually editing JSON.
- Add a safer Matrix fixer path with `validate_fix_response()` applied before item descriptions are changed.
- Consider a turn history UI showing prompt, model response, accepted changes, rejected changes, and resulting state.

## Phase 6: Scenario And Save Management

Creating scenarios and managing game states should feel like using the game, not like juggling files.

- Add a scenario selector backed by `LoreBooks/` and active `lore.txt` generation.
- Add scenario metadata: name, genre, description, preferred model parameters, and starting notes.
- Add save slots with friendly names, timestamps, scenario references, and token totals.
- Add export/import for saves and scenarios.
- Keep the existing file-based workflow intact for Replit and power-user editing.

## Phase 7: Token And Cost Accounting

The engine already records total tokens, but it needs a clearer ledger.

- Track cumulative input tokens, output tokens, total tokens, and estimated cost.
- Store token usage by turn and by operation type: genesis, room generation, DM turn, fixer, model listing, and repair.
- Add configurable model pricing data, initially manual and later provider-aware if Venice exposes reliable pricing metadata.
- Show session and lifetime totals in the HUD or debug panel.
- Flag unusually expensive turns.

## Phase 8: LLM Controls

Model settings should be visible and adjustable without code edits.

- Research Venice.ai request parameters before changing the runtime contract.
- Add UI controls for model, temperature, max output tokens, reasoning effort/intensity, and other supported options.
- Persist per-scenario defaults while allowing temporary per-session overrides.
- Include model settings in turn debug reports so behavior is explainable later.
- Validate requested params before sending them to the provider.

## Phase 9: Interface Polish

Once the state layer is more trustworthy, improve the daily feel of the app.

- Add command history and better command recall.
- Improve error styling so failures are legible but not alarming.
- Split the Matrix editor into clearer panels for player, NPCs, room contents, void, and turn report.
- Make debug views easier to scan.
- Keep the terminal feel, but reduce friction for scenario management and state repair.

## Near-Term Implementation Order

1. Document the turn packet and ownership-slot contract.
2. Wire the remaining fixer validation path safely.
3. Implement canonical ownership slots for player/NPC held, worn, and body entities.
4. Implement resolvable disambiguation for visible items, with tests.
5. Add the first structured turn packet and recent-full-turn buffer.
6. Extend lookup/state handling to characters and non-present entities.
7. Add turn reports and transparency levels.
8. Begin the world-state manager refactor only after the above behavior is covered by tests.

## Non-Goals For Now

- Do not require manual approval for every normal LLM state update.
- Do not remove historical saves or debug logs without an explicit cleanup decision.
- Do not redesign the whole frontend before the state model is more reliable.
- Do not overfit prompts before the engine can accurately describe its own state.
- Do not assume Venice parameters without checking current provider docs first.

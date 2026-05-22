# Handoff Status

This file exists so a brand-new Codex chat can resume stewardship of Frotz2 from the repository alone, without needing access to prior chat history.

Treat this as an operator brief, not just a summary. A future session should be able to read this file, read the current roadmap/TODO/docs, inspect the code, and continue making good decisions without re-deriving the project's intent.

## Executive Summary

Frotz2 is a personal interactive-fiction engine with LLM-driven narration and state updates. The current stewardship direction is to turn it from a clever prototype into a reliable, continuity-aware engine.

The highest-value current theme is consistency:

- consistent entity lookup
- consistent turn-to-turn awareness
- consistent ownership and containment rules
- consistent tool naming and validation
- consistent visibility into what the model tried to do versus what the engine actually accepted

The project is not in a broad feature-rush phase. The active posture is to harden foundations while preserving the existing creative workflow.

## Stewardship Context

Frotz2 is being developed under a repo-stewardship workflow:

- Prefer direct, focused commits to `main`.
- Prioritize stability, consistency, maintainability, and continuity before broad new features.
- Preserve the user's private Replit/ChatGPT workflow, including `/update-files`.
- Do not feature `/update-files` in general-facing docs beyond private workflow notes.
- Do not delete historical tracked saves or debug logs unless a future cleanup pass explicitly decides to do so.
- Favor small coherent batches over sweeping rewrites.
- Keep docs current as the work advances; `TODO.md` should stay alive rather than becoming stale ceremony.

## User Preferences And Working Style

These matter because they are not fully recoverable from code alone:

- The user wants Codex to take creative and technical lead on the repo.
- The user does not want passive brainstorming in place of progress; when a good next step is visible, do it.
- The user values robust, low-drama engineering more than flashy features.
- The user wants the repo to become increasingly self-explanatory so future sessions can pick up with little friction.
- The user is comfortable with direct repo changes and wants momentum, but not careless breakage.
- The user explicitly does not want ordinary LLM state updates gated behind constant manual approvals.
- The user wants tool-call transparency to be adjustable in intensity rather than all-or-nothing.
- The user wants the system to preserve the private lore/adult workflow without turning shared docs/tests into explicit-content-heavy artifacts.

## Working Constraints

These matter for future sessions even though they are not obvious from source code alone:

- The current work PC does not have Python installed.
- The user prefers GitHub-first work and wants to avoid local actions that leave persistent residue on their machine.
- Read-only inspection and transient checks are acceptable; local dependency installs, local repo checkouts, or artifact-producing local runs are not preferred on this machine.
- Test files should still be added normally, but local execution may not be available in the current environment.
- If verification is needed, prefer GitHub-side review, Replit, CI, or another Python-enabled environment over trying to force local setup on this PC.

## Product Direction

The current top priority is game-state consistency.

Most important current goals:

- Resolve ambiguous references when multiple entities share matching words.
- Improve the model's awareness of what is currently happening on each turn.
- Make entity ownership and containment explicit for player and NPC held, worn, and body entities.
- Keep tool use clear, consistent, typo-resistant, and engine-validated.
- Make tool-call visibility toggleable rather than requiring manual approval for ordinary changes.

Important clarifications from the user:

- Tool transparency should support levels like quiet, summary, debug, and audit.
- Transparency must not turn ordinary state updates into constant approval prompts.
- Recent full-turn context is valuable and worth a small token cost.
- Future work should use judgment from the stewardship plan and TODO, not just chase the last-mentioned feature.
- The user has additional medium-term interests in token/cost accounting, world-state management, better scenario/save UX, better repair/undo flows, richer LLM controls, and stronger tool-call observability.

## Design Philosophy For The Engine

A future session should continue from these assumptions:

- The world state, not the model's prose, is the source of truth.
- The LLM should narrate and propose structured changes, not silently redefine reality through untracked prose alone.
- Prompt quality matters, but prompt wording is not enough; important invariants must be enforced by engine code.
- Compatibility with the current engine matters. Avoid abrupt schema breaks when an adapter or migration step can preserve momentum.
- Prefer explicit ownership/containment rules over fuzzy location rules.
- Prefer bounded context with strong structure over massive unstructured prompt stuffing.

## Implemented So Far

The following is already in the repo and should be treated as the current base state:

- Project docs and roadmap were added and organized.
- `docs/LLM_CONTRACTS.md` documents current JSON response expectations.
- `docs/LLM_TOOLS.md` documents canonical engine-side tool vocabulary.
- `docs/TURN_CONTEXT.md` documents the intended turn packet shape.
- `docs/STEWARDSHIP_ROADMAP.md` holds the medium-term product direction.
- `TODO.md` is the active working backlog and should be kept current.
- `llm_contracts.py` now contains canonical tool constants, slot normalization, and lightweight response validation.
- `world_manager.py` now stores a bounded `recent_turns` buffer in save data.
- `world_manager.py` now supports initial `owner` plus `slot` handling for `move_entity` and `create_entity`, alongside legacy `Location` behavior.
- `world_manager.py` now exposes NPC held, worn, and body entities in context dumps and visible-item lookup.
- `main.py` now records recent AI turns after DM turns and major reality-shift narration.
- Neutral pytest coverage was added for contracts, smoke behavior, save/load, recent-turn recording, and NPC ownership-slot behavior.

## Architectural Reality At Handoff Time

The codebase is in a transitional state:

- The docs now define a clearer canonical model than the runtime fully enforces.
- The runtime still carries compatibility behavior for legacy `Description` and `Location` updates.
- The current implementation has started to separate room items, player held/worn/body items, and NPC held/worn/body items, but it is not yet a fully unified state model.
- The prompt layer, validation layer, and application layer are closer than before, but they are not yet fully aligned.

This is normal for the repo's current phase. The next work should reduce this mismatch incrementally rather than trying to replace everything at once.

## Current Known Gaps

These are the most relevant remaining gaps at handoff time:

- `system_prompts.py` still speaks mostly in legacy `Description` / `Location` language and has not yet been fully migrated to the canonical tool vocabulary.
- The engine still lacks a proper dispatcher that validates and reports per-tool outcomes before mutation.
- Ambiguity handling is still shallow and currently asks a one-off question rather than storing resolvable pending ambiguity state.
- `validate_fix_response()` still needs to be wired into the Matrix fixer path with focused tests.
- The turn packet exists as a documented target, but the runtime still mostly uses formatted text dumps rather than a structured packet object.
- Tests have been added but may not have been run in the user's current PC environment because Python is unavailable there.

## Known Risks And Sharp Edges

A future session should be alert to these risks:

- Prompt/runtime mismatch: the model may still emit legacy-shaped updates even as docs and helpers move toward canonical tools.
- Silent fallback behavior: some current code still tries to be forgiving, which can preserve flow but may hide malformed intent.
- Ambiguous entity lookup: substring matching can still create wrong resolutions or fragile one-off disambiguation.
- State duplication risk: player/NPC slot state and legacy character `items` compatibility can drift if not kept aligned carefully.
- Debug artifacts versus runtime truth: debug files are useful, but they should not become the only source of continuity.

## What Not To Accidentally Break

These are easy places for a future session to over-correct:

- Do not remove support for the user's existing private workflows just because they are inelegant.
- Do not replace compatibility layers before the new path is actually wired end-to-end.
- Do not turn observability into friction by forcing approval prompts for every ordinary turn.
- Do not introduce schema churn that strands old saves unless a migration plan is part of the change.
- Do not let docs drift after changing behavior; the handoff quality depends on docs remaining truthful.

## Decision Heuristics For Future Sessions

If choosing the next task is not obvious, use these heuristics:

- Choose work that reduces state ambiguity before work that adds more content surfaces.
- Choose code paths that make model behavior more legible before adding cosmetic UI layers for that behavior.
- Choose narrow compatibility-preserving steps before large architectural rewrites.
- Choose infrastructure that supports several future features at once over isolated one-off feature work.
- If a change would make saves, prompts, and tool application all line up better, it is probably a strong next step.

## Recommended Near-Term Sequence

If resuming from a new chat, the best next sequence is:

1. Migrate `system_prompts.py` toward the canonical tool vocabulary and ownership-slot rules without breaking compatibility.
2. Implement a first real tool dispatcher with per-tool acceptance/rejection results.
3. Add stored pending-disambiguation state so follow-up inputs can resolve the prior ambiguous command.
4. Wire `validate_fix_response()` into the Matrix fixer path.
5. Continue world-state cleanup only after the above behavior is better validated.

## Practical Guidance For The Next Chat

A future Codex session should probably begin by doing this:

1. Read `TODO.md` and this file first.
2. Re-open `docs/LLM_TOOLS.md`, `docs/TURN_CONTEXT.md`, and `docs/STEWARDSHIP_ROADMAP.md`.
3. Inspect the current versions of `world_manager.py`, `main.py`, `llm_contracts.py`, and `system_prompts.py`.
4. Compare documented intent versus actual runtime behavior.
5. Pick the smallest next change that improves consistency and closes one of the known gaps above.

## Repo As Source Of Truth

A new chat should use these files first:

- `TODO.md`
- `docs/STEWARDSHIP_ROADMAP.md`
- `docs/LLM_TOOLS.md`
- `docs/TURN_CONTEXT.md`
- `docs/LLM_CONTRACTS.md`
- this file

If those files and the latest code disagree, prefer the code plus `TODO.md`, then update the docs.

## Final Continuity Note

The repo is intentionally being shaped so that future stewardship can be repo-first rather than chat-memory-first. If this file becomes outdated, update it as part of the same batch that changes the project's direction or constraints. The goal is for a new session to inherit judgment, not just information.

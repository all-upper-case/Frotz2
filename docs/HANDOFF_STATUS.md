# Handoff Status

This file exists so a brand-new Codex chat can resume stewardship of Frotz2 from the repository alone, without needing access to prior chat history.

## Stewardship Context

Frotz2 is being developed under a repo-stewardship workflow:

- Prefer direct, focused commits to `main`.
- Prioritize stability, consistency, maintainability, and continuity before broad new features.
- Preserve the user's private Replit/ChatGPT workflow, including `/update-files`.
- Do not feature `/update-files` in general-facing docs beyond private workflow notes.
- Do not delete historical tracked saves or debug logs unless a future cleanup pass explicitly decides to do so.

## Working Constraints

These matter for future sessions even though they are not obvious from source code alone:

- The current work PC does not have Python installed.
- The user prefers GitHub-first work and wants to avoid local actions that leave persistent residue on their machine.
- Read-only inspection and transient checks are acceptable; local dependency installs, local repo checkouts, or artifact-producing local runs are not preferred on this machine.
- Test files should still be added normally, but local execution may not be available in the current environment.

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

## Current Known Gaps

These are the most relevant remaining gaps at handoff time:

- `system_prompts.py` still speaks mostly in legacy `Description` / `Location` language and has not yet been fully migrated to the canonical tool vocabulary.
- The engine still lacks a proper dispatcher that validates and reports per-tool outcomes before mutation.
- Ambiguity handling is still shallow and currently asks a one-off question rather than storing resolvable pending ambiguity state.
- `validate_fix_response()` still needs to be wired into the Matrix fixer path with focused tests.
- The turn packet exists as a documented target, but the runtime still mostly uses formatted text dumps rather than a structured packet object.
- Tests have been added but may not have been run in the user's current PC environment because Python is unavailable there.

## Next Best Steps

If resuming from a new chat, the best next sequence is:

1. Migrate `system_prompts.py` toward the canonical tool vocabulary and ownership-slot rules without breaking compatibility.
2. Implement a first real tool dispatcher with per-tool acceptance/rejection results.
3. Add stored pending-disambiguation state so follow-up inputs can resolve the prior ambiguous command.
4. Wire `validate_fix_response()` into the Matrix fixer path.
5. Continue world-state cleanup only after the above behavior is better validated.

## Repo As Source Of Truth

A new chat should use these files first:

- `TODO.md`
- `docs/STEWARDSHIP_ROADMAP.md`
- `docs/LLM_TOOLS.md`
- `docs/TURN_CONTEXT.md`
- `docs/LLM_CONTRACTS.md`
- this file

If those files and the latest code disagree, prefer the code plus `TODO.md`, then update the docs.

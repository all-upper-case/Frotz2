# Local Workflows

These notes describe the personal workflow surfaces that exist around the app. They are intentionally separate from the README so the public setup docs stay focused.

## Running The App

Local development:

```bash
poetry install
poetry run python main.py
```

Replit uses `.replit` to run Gunicorn on port `5000`:

```bash
gunicorn --bind 0.0.0.0:5000 --timeout 120 main:app
```

## Lore And Saves

- The active world seed is `lore.txt`.
- `WorldManager` reads the first `WORLD_NAME:` line and stores the active save at `saves/<world_name>.json`.
- Alternate lore seeds live in `LoreBooks/`.
- Resetting a world moves the current save into `backups/` before generating a fresh state.

Suggested manual loop:

1. Copy or draft a lore seed into `lore.txt`.
2. Run the app.
3. Use `/reset` or the reset button to regenerate the world from the active lore.
4. Preserve any interesting save by copying it into a named archive before another reset.

## Debugging LLM Turns

The backend writes two kinds of debug artifacts:

- `debug_log.txt`: append-only history of LLM outputs and token usage.
- `last_turn_debug.txt`: compact recent prompt/response payloads used by the frontend debug modal.

These are useful while tuning prompts, but they may include full world context and generated content. Keep new debug artifacts out of commits unless they are intentionally curated examples.

## Model Switching

The app supports frontend commands:

- `/models`: list available Venice text models.
- `/model <id>`: switch the in-memory model for the current server process.

The default model can also be set with `VENICE_MODEL`.

## Matrix / World State Editor

The Matrix editor is the in-browser state harmonizer. It can:

- Move items between inventory, worn state, void, and rooms.
- Edit aliases and descriptions.
- Ask the LLM to rewrite an item description based on a correction instruction.

Changes are applied through `/god_update` and saved immediately.

## Devtools

`devtools.py` defines helper routes for trusted local/Replit workflows:

- `/dev` for shortcut-friendly text requests.
- `/devtools` for a simple browser form.
- `/devtools/run` for restricted `fetch.py` commands.
- `/devtools/patch` for dry-running or applying patch blocks.

Set `DEVTOOLS_TOKEN` before using these routes anywhere reachable from outside your trusted environment.
import os
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path

from flask import Blueprint, jsonify, request


devtools_bp = Blueprint("devtools", __name__)
ROOT = Path(__file__).resolve().parent


def _token_ok() -> bool:
    """Require DEVTOOLS_TOKEN only when that Replit env var is set."""
    expected = os.environ.get("DEVTOOLS_TOKEN", "").strip()
    if not expected:
        return True

    json_data = request.get_json(silent=True) if request.is_json else {}
    supplied = (
        request.args.get("token")
        or request.headers.get("X-Devtools-Token")
        or request.form.get("token")
        or (json_data or {}).get("token")
    )
    return supplied == expected


def _run(args, input_text=None, timeout=30):
    proc = subprocess.run(
        args,
        cwd=ROOT,
        input=input_text,
        text=True,
        capture_output=True,
        timeout=timeout,
    )
    return {
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "combined": (proc.stdout or "") + (("\n--- STDERR ---\n" + proc.stderr) if proc.stderr else ""),
    }


def _request_text():
    if request.is_json:
        data = request.get_json(silent=True) or {}
        return data.get("command") or data.get("patch_text") or data.get("text") or ""
    return request.get_data(as_text=True) or ""


def _run_fetch_command(command):
    try:
        parts = shlex.split(command)
    except ValueError as exc:
        return {"combined": f"Could not parse command: {exc}", "returncode": 2}

    if len(parts) < 2:
        return {"combined": "Command must look like: python fetch.py ...", "returncode": 2}

    if parts[0] not in {"python", "python3"}:
        return {"combined": "Only python/python3 commands are allowed.", "returncode": 2}

    script = Path(parts[1]).name
    if script != "fetch.py":
        return {"combined": "Only fetch.py is allowed in run mode. Use dry/apply for patches.", "returncode": 2}

    safe_args = [sys.executable, "fetch.py", *parts[2:]]
    return _run(safe_args, timeout=30)


def _run_patch(patch_text, dry_run=True):
    if "---PATCH---" not in patch_text:
        return {"combined": "No ---PATCH--- block found.", "returncode": 2}

    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        suffix=".txt",
        prefix="devtools_patch_",
        delete=False,
        dir=ROOT,
    ) as tmp:
        tmp.write(patch_text)
        tmp_path = Path(tmp.name)

    try:
        args = [sys.executable, "edit.py", str(tmp_path.name)]
        if dry_run:
            args.append("--dry-run")
        return _run(args, timeout=60)
    finally:
        try:
            tmp_path.unlink()
        except OSError:
            pass


@devtools_bp.route("/dev", methods=["GET", "POST"])
def phone_dev():
    """Compatibility endpoint for iPhone Shortcuts.

    POST plain text to:
      /dev?mode=run   -> run a fetch.py command from the request body
      /dev?mode=dry   -> dry-run a ---PATCH--- block from the request body
      /dev?mode=apply -> apply a ---PATCH--- block from the request body
    """
    if request.method == "GET":
        return devtools_page()

    if not _token_ok():
        return "Forbidden. Check DEVTOOLS_TOKEN.", 403

    mode = (request.args.get("mode") or "run").strip().lower()
    body_text = _request_text().strip()
    if not body_text:
        return "No input provided.", 400

    if mode == "run":
        result = _run_fetch_command(body_text)
    elif mode in {"dry", "dry-run", "dry_run"}:
        result = _run_patch(body_text, dry_run=True)
    elif mode == "apply":
        result = _run_patch(body_text, dry_run=False)
    else:
        return "Unknown mode. Use mode=run, mode=dry, or mode=apply.", 400

    status = 200 if result.get("returncode") == 0 else 500
    return result.get("combined", ""), status, {"Content-Type": "text/plain; charset=utf-8"}


@devtools_bp.route("/devtools", methods=["GET"])
def devtools_page():
    token = request.args.get("token", "")
    if not _token_ok():
        return "Forbidden. Check DEVTOOLS_TOKEN.", 403

    return f'''<!doctype html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Phone Dev Tools</title>
<style>
body {{ font-family: system-ui, -apple-system, BlinkMacSystemFont, sans-serif; background: #111; color: #eee; margin: 0; padding: 16px; }}
textarea, input {{ width: 100%; box-sizing: border-box; background: #1f1f1f; color: #eee; border: 1px solid #444; border-radius: 10px; padding: 12px; font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 14px; }}
textarea {{ min-height: 210px; }}
button {{ width: 100%; margin-top: 10px; padding: 14px; border: 0; border-radius: 12px; background: #2563eb; color: white; font-weight: 700; font-size: 16px; }}
button.secondary {{ background: #444; }}
button.danger {{ background: #dc2626; }}
pre {{ white-space: pre-wrap; word-break: break-word; background: #050505; border: 1px solid #333; border-radius: 10px; padding: 12px; min-height: 160px; }}
.small {{ color: #aaa; font-size: 13px; line-height: 1.4; }}
</style>
</head>
<body>
<h2>Phone Dev Tools</h2>
<p class="small">Paste either a fetch command like <code>python fetch.py main.py --contains "handle_command" --context 40</code>, or paste a full <code>---PATCH---</code> block.</p>
<textarea id="input" placeholder="Paste fetch command or patch block here..."></textarea>
<button onclick="runFetch()">Run Fetch Command</button>
<button class="secondary" onclick="dryRunPatch()">Dry Run Patch</button>
<button class="danger" onclick="applyPatch()">Apply Patch</button>
<h3>Output</h3>
<button class="secondary" onclick="copyOutput()">Copy Output</button>
<pre id="output"></pre>
<script>
const TOKEN = {token!r};
async function postJson(url, body) {{
    body.token = TOKEN;
    const res = await fetch(url, {{ method: "POST", headers: {{ "Content-Type": "application/json" }}, body: JSON.stringify(body) }});
    const data = await res.json().catch(async () => ({{ combined: await res.text() }}));
    document.getElementById("output").textContent = data.combined || JSON.stringify(data, null, 2);
}}
function getInput() {{ return document.getElementById("input").value; }}
async function runFetch() {{ await postJson("/devtools/run", {{ command: getInput() }}); }}
async function dryRunPatch() {{ await postJson("/devtools/patch", {{ patch_text: getInput(), dry_run: true }}); }}
async function applyPatch() {{ if (!confirm("Apply this patch to the codebase?")) return; await postJson("/devtools/patch", {{ patch_text: getInput(), dry_run: false }}); }}
async function copyOutput() {{ const text = document.getElementById("output").textContent; await navigator.clipboard.writeText(text); alert("Copied output."); }}
</script>
</body>
</html>'''


@devtools_bp.route("/devtools/run", methods=["POST"])
def devtools_run():
    if not _token_ok():
        return jsonify({"combined": "Forbidden. Check DEVTOOLS_TOKEN."}), 403

    command = ((request.get_json(silent=True) or {}).get("command") or "").strip()
    if not command:
        return jsonify({"combined": "No command provided."}), 400

    result = _run_fetch_command(command)
    return jsonify(result), 200 if result.get("returncode") == 0 else 500


@devtools_bp.route("/devtools/patch", methods=["POST"])
def devtools_patch():
    if not _token_ok():
        return jsonify({"combined": "Forbidden. Check DEVTOOLS_TOKEN."}), 403

    data = request.get_json(silent=True) or {}
    patch_text = data.get("patch_text", "")
    dry_run = bool(data.get("dry_run", True))

    result = _run_patch(patch_text, dry_run=dry_run)
    return jsonify(result), 200 if result.get("returncode") == 0 else 500

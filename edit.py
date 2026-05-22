#!/usr/bin/env python3
"""Exact, safe code replacement helper for Phone Dev."""
import argparse
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def parse_patches(text):
    patches = []
    for raw in text.split("---PATCH---"):
        raw = raw.strip("\n")
        if not raw.strip():
            continue
        if "---OLD---" not in raw or "---NEW---" not in raw or "---END---" not in raw:
            raise ValueError("Patch is missing ---OLD---, ---NEW---, or ---END--- marker.")
        header, rest = raw.split("---OLD---", 1)
        old, rest = rest.split("---NEW---", 1)
        new, _ = rest.split("---END---", 1)
        info = {"name": "Unnamed patch", "count": 1}
        for line in header.splitlines():
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            key = key.strip().lower()
            value = value.strip()
            if key == "name":
                info["name"] = value
            elif key == "file":
                info["file"] = value
            elif key == "count":
                info["count"] = int(value)
        if "file" not in info:
            raise ValueError("Patch header is missing FILE: path.")
        patches.append({
            "name": info["name"],
            "file": info["file"],
            "count": info["count"],
            "old": old.strip("\n"),
            "new": new.strip("\n"),
        })
    return patches


def compile_python(path):
    if not str(path).endswith(".py"):
        return True
    result = subprocess.run([sys.executable, "-m", "py_compile", str(path)], text=True, capture_output=True)
    if result.returncode != 0:
        print(result.stderr or result.stdout)
        return False
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("patch_file")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-compile", action="store_true")
    args = parser.parse_args()

    patch_text = Path(args.patch_file).read_text(encoding="utf-8")
    patches = parse_patches(patch_text)
    backups = []

    for patch in patches:
        path = Path(patch["file"])
        if not path.exists():
            raise SystemExit(f"File not found: {path}")
        text = path.read_text(encoding="utf-8")
        actual = text.count(patch["old"])
        print(f"PATCH: {patch['name']}")
        print(f"FILE: {path}")
        print(f"Expected matches: {patch['count']}")
        print(f"Actual matches: {actual}")
        if actual != patch["count"]:
            raise SystemExit("Match count mismatch. Refusing to edit.")

    if args.dry_run:
        print("DRY RUN OK. No files changed.")
        return

    try:
        for patch in patches:
            path = Path(patch["file"])
            backup_dir = Path(".edit_backups")
            backup_dir.mkdir(exist_ok=True)
            stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            backup = backup_dir / f"{path.name}.{stamp}.bak"
            shutil.copy2(path, backup)
            backups.append((path, backup))

            text = path.read_text(encoding="utf-8")
            text = text.replace(patch["old"], patch["new"], patch["count"])
            path.write_text(text, encoding="utf-8")
            print(f"Applied: {patch['name']}")

        if not args.no_compile:
            for path, backup in backups:
                if not compile_python(path):
                    shutil.copy2(backup, path)
                    raise SystemExit(f"Python syntax check failed. Restored backup for {path}.")

        print("PATCH APPLY OK.")
    except Exception:
        for path, backup in backups:
            if backup.exists():
                shutil.copy2(backup, path)
        raise


if __name__ == "__main__":
    main()

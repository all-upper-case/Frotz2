#!/usr/bin/env python3
"""Small code fetch helper for Phone Dev."""
import argparse
import ast
from pathlib import Path


def read_lines(path):
    return Path(path).read_text(encoding="utf-8").splitlines()


def print_range(path, lines, start, end):
    start = max(1, start)
    end = min(len(lines), end)
    print(f"--- FETCHED: {path} lines {start}:{end} ---")
    for idx in range(start, end + 1):
        print(f"{idx}: {lines[idx - 1]}")


def find_def(path, name):
    text = Path(path).read_text(encoding="utf-8")
    tree = ast.parse(text)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.name == name:
            return node.lineno, getattr(node, "end_lineno", node.lineno)
    raise SystemExit(f"No function/class named {name!r} found in {path}.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    parser.add_argument("--lines")
    parser.add_argument("--contains")
    parser.add_argument("--context", type=int, default=30)
    parser.add_argument("--nth", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--merge-overlaps", action="store_true")
    parser.add_argument("--def", dest="def_name")
    args = parser.parse_args()

    lines = read_lines(args.path)

    if args.def_name:
        start, end = find_def(args.path, args.def_name)
        print_range(args.path, lines, start, end)
        return

    if args.lines:
        left, right = args.lines.split(":", 1)
        print_range(args.path, lines, int(left), int(right))
        return

    if args.contains:
        matches = [i + 1 for i, line in enumerate(lines) if args.contains in line]
        if not matches:
            raise SystemExit(f"No matches for {args.contains!r} in {args.path}.")
        if args.all:
            ranges = [(m - args.context, m + args.context) for m in matches]
            if args.merge_overlaps:
                merged = []
                for start, end in ranges:
                    if merged and start <= merged[-1][1] + 1:
                        merged[-1] = (merged[-1][0], max(merged[-1][1], end))
                    else:
                        merged.append((start, end))
                ranges = merged
            for start, end in ranges:
                print_range(args.path, lines, start, end)
            return
        match = matches[args.nth - 1]
        print_range(args.path, lines, match - args.context, match + args.context)
        return

    raise SystemExit("Use --def, --lines, or --contains.")


if __name__ == "__main__":
    main()

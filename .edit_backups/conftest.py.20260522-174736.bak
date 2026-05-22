import importlib
import sys

import pytest


@pytest.fixture
def isolated_main(tmp_path, monkeypatch):
    """Import main.py from a temp working directory so tests do not touch real saves."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("VENICE_API_KEY", raising=False)
    monkeypatch.delenv("MISTRAL_API_KEY", raising=False)
    monkeypatch.delenv("VENICE_MODEL", raising=False)

    for module_name in ["main", "world_manager", "llm_interface", "llm_contracts"]:
        sys.modules.pop(module_name, None)

    module = importlib.import_module("main")
    module.app.config.update(TESTING=True)
    return module


@pytest.fixture
def minimal_world():
    return {
        "narrative_log": ["A quiet test begins."],
        "blueprint": "A tiny neutral test world.",
        "meta": {"total_tokens": 0},
        "pending_notifications": [],
        "recent_turns": [],
        "player": {
            "current_room": "room_start",
            "inventory": ["item_lantern"],
            "worn": [],
            "body": [],
            "description": "You are a careful tester.",
            "aliases": ["me", "self", "player"],
        },
        "characters": {
            "npc_curator": {
                "id": "npc_curator",
                "name": "Curator",
                "aliases": ["keeper"],
                "description": "A patient curator watches over the archive.",
                "items": [],
                "held": [],
                "worn": [],
                "body": [],
            }
        },
        "rooms": {
            "room_start": {
                "id": "room_start",
                "name": "Archive",
                "description": "A calm archive lined with labeled drawers.",
                "base_description": "A calm archive lined with labeled drawers.",
                "exits": {"north": "room_north"},
                "items": ["item_key", "item_badge", "item_glove"],
                "characters": ["npc_curator"],
                "visited": True,
            },
            "room_north": {
                "id": "room_north",
                "name": "Reading Room",
                "description": "A quiet reading room with a single desk.",
                "base_description": "A quiet reading room with a single desk.",
                "exits": {"south": "room_start"},
                "items": [],
                "characters": [],
                "visited": False,
            },
        },
        "items": {
            "item_lantern": {
                "id": "item_lantern",
                "name": "brass lantern",
                "aliases": ["lantern"],
                "description": "A polished brass lantern.",
                "carryable": True,
                "visible": True,
            },
            "item_key": {
                "id": "item_key",
                "name": "silver key",
                "aliases": ["key"],
                "description": "A small silver key.",
                "carryable": True,
                "visible": True,
            },
            "item_badge": {
                "id": "item_badge",
                "name": "curator badge",
                "aliases": ["badge"],
                "description": "A simple identification badge.",
                "carryable": True,
                "visible": True,
            },
            "item_glove": {
                "id": "item_glove",
                "name": "linen glove",
                "aliases": ["glove"],
                "description": "A clean linen glove.",
                "carryable": True,
                "visible": True,
            },
        },
    }

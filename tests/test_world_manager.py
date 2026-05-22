from world_manager import WorldManager


class StubFixInterface:
    def __init__(self, response):
        self.response = response

    def generate_fix(self, item_name, current_desc, user_instruction):
        return self.response


def test_world_manager_save_load_roundtrip(tmp_path, monkeypatch, minimal_world):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "lore.txt").write_text("WORLD_NAME: neutral_archive\nA quiet test world.", encoding="utf-8")

    manager = WorldManager()
    manager.data = minimal_world
    manager.save_game()

    loaded = WorldManager()

    assert loaded.world_name == "neutral_archive"
    assert loaded.data["rooms"]["room_start"]["name"] == "Archive"
    assert loaded.data["player"]["inventory"] == ["item_lantern"]


def test_record_turn_keeps_recent_full_turn_context(tmp_path, monkeypatch, minimal_world):
    monkeypatch.chdir(tmp_path)
    manager = WorldManager()
    manager.data = minimal_world
    manager.ensure_schema()

    for idx in range(5):
        manager.record_turn(
            f"test command {idx}",
            {
                "narrative": f"Test output {idx}.",
                "narrative_summary_update": f"Summary {idx}.",
                "state_updates": [{"tool": "Description", "name": "silver key"}],
            },
        )

    assert len(manager.data["recent_turns"]) == 3
    assert manager.data["recent_turns"][0]["input"] == "test command 2"
    assert "Test output 4." in manager.get_recent_turns_context()
    assert "tool=Description" in manager.get_recent_turns_context()


def test_move_entity_can_place_item_in_npc_held_slot(tmp_path, monkeypatch, minimal_world):
    monkeypatch.chdir(tmp_path)
    manager = WorldManager()
    manager.data = minimal_world
    manager.ensure_schema()

    manager.apply_outcome({
        "state_updates": [
            {"tool": "move_entity", "target": "silver key", "owner": "Curator", "slot": "held"}
        ]
    })

    curator = manager.data["characters"]["npc_curator"]
    assert "item_key" in curator["held"]
    assert "item_key" in curator["items"]
    assert "item_key" not in manager.data["rooms"]["room_start"]["items"]


def test_create_entity_can_place_body_part_on_npc(tmp_path, monkeypatch, minimal_world):
    monkeypatch.chdir(tmp_path)
    manager = WorldManager()
    manager.data = minimal_world
    manager.ensure_schema()

    manager.apply_outcome({
        "state_updates": [
            {
                "tool": "create_entity",
                "name": "left hand",
                "description": "A steady left hand.",
                "entity_type": "body_part",
                "owner": "Curator",
                "slot": "body",
            }
        ]
    })

    curator = manager.data["characters"]["npc_curator"]
    body_item_id = curator["body"][0]
    assert manager.data["items"][body_item_id]["name"] == "left hand"
    assert manager.data["items"][body_item_id]["body_part"] is True
    assert manager.data["items"][body_item_id]["carryable"] is False


def test_context_dump_includes_recent_turns_and_npc_slots(tmp_path, monkeypatch, minimal_world):
    monkeypatch.chdir(tmp_path)
    manager = WorldManager()
    manager.data = minimal_world
    manager.ensure_schema()
    manager.apply_outcome({
        "state_updates": [
            {"tool": "Location", "name": "curator badge", "location": "Curator"},
            {"tool": "move_entity", "target": "linen glove", "owner": "Curator", "slot": "worn"},
        ]
    })
    manager.record_turn("look at the curator", {"narrative": "The curator waits beside the drawers."})

    context = manager.get_context_dump()

    assert "[RECENT FULL TURNS]" in context
    assert "look at the curator" in context
    assert "Held: curator badge" in context
    assert "Worn: linen glove" in context


def test_god_mode_fix_accepts_valid_ai_description(tmp_path, monkeypatch, minimal_world):
    monkeypatch.chdir(tmp_path)
    manager = WorldManager()
    manager.data = minimal_world
    manager.ensure_schema()
    ai = StubFixInterface({"description": "A key freshly reconciled with the current scene."})

    message = manager.god_mode_update(
        [{"id": "item_key", "fixInstruction": "Match the current scene."}],
        ai,
    )

    assert manager.data["items"]["item_key"]["description"] == "A key freshly reconciled with the current scene."
    assert "auto-fixed by AI" in message


def test_god_mode_fix_rejects_invalid_ai_description(tmp_path, monkeypatch, minimal_world):
    monkeypatch.chdir(tmp_path)
    manager = WorldManager()
    manager.data = minimal_world
    manager.ensure_schema()
    original_description = manager.data["items"]["item_key"]["description"]
    ai = StubFixInterface({"error": True, "message": "provider failed"})

    message = manager.god_mode_update(
        [{"id": "item_key", "fixInstruction": "Match the current scene."}],
        ai,
    )

    assert manager.data["items"]["item_key"]["description"] == original_description
    assert "auto-fix rejected" in message
    assert "provider failed" in message

from world_manager import WorldManager


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

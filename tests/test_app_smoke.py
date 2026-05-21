def test_app_imports_without_api_key(isolated_main):
    assert isolated_main.app is not None
    assert isolated_main.ai.model


def test_get_state_uninitialized(isolated_main):
    client = isolated_main.app.test_client()

    response = client.get("/get_state")

    assert response.status_code == 200
    assert response.get_json() == {"response": "INITIALIZING_GENESIS", "state": None}


def test_command_uninitialized(isolated_main):
    client = isolated_main.app.test_client()

    response = client.post("/command", json={"input": "look"})

    assert response.status_code == 200
    assert response.get_json()["response"] == "Uninitialized."


def test_reset_without_api_key_does_not_initialize_world(isolated_main):
    client = isolated_main.app.test_client()

    response = client.post("/reset")
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["state"] is None
    assert "Genesis Failed" in payload["response"]
    assert not isolated_main.world.is_initialized()


def test_deterministic_commands_use_existing_world(isolated_main, minimal_world):
    isolated_main.world.data = minimal_world
    client = isolated_main.app.test_client()

    look = client.post("/command", json={"input": "look"}).get_json()
    inventory = client.post("/command", json={"input": "inventory"}).get_json()
    examine = client.post("/command", json={"input": "examine key"}).get_json()

    assert "Archive" in look["response"]
    assert "brass lantern" in inventory["response"]
    assert examine["response"] == "A small silver key."

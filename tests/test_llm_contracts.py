import pytest

from llm_contracts import (
    ContractError,
    normalize_person_slot,
    normalize_state_update,
    normalize_state_updates,
    normalize_tool_name,
    validate_fix_response,
    validate_genesis_response,
    validate_room_response,
    validate_turn_response,
)


def valid_genesis():
    return {
        "intro_text": "You arrive in a quiet archive.",
        "starting_room_name": "Archive",
        "starting_room_description": "Shelves line the walls.",
        "player_description": "You are ready to explore.",
        "narrative_thread": "The archive waits.",
        "blueprint": "A small archive with nearby rooms.",
        "new_exits": ["north"],
        "state_updates": [],
    }


def test_genesis_contract_accepts_valid_payload():
    payload = validate_genesis_response(valid_genesis())

    assert payload["starting_room_name"] == "Archive"
    assert payload["state_updates"] == []


def test_genesis_contract_rejects_missing_required_fields():
    payload = valid_genesis()
    payload.pop("intro_text")

    with pytest.raises(ContractError, match="intro_text"):
        validate_genesis_response(payload)


def test_contracts_reject_error_shaped_payloads():
    with pytest.raises(ContractError, match="No API Key"):
        validate_turn_response({"error": True, "narrative": "No API Key"})


def test_turn_contract_requires_narrative_and_normalizes_updates():
    payload = validate_turn_response({"narrative": "The key clicks."})

    assert payload["narrative"] == "The key clicks."
    assert payload["state_updates"] == []


def test_room_contract_rejects_non_list_state_updates():
    with pytest.raises(ContractError, match="state_updates"):
        validate_room_response({
            "room_name": "Reading Room",
            "room_description": "A desk waits under a lamp.",
            "state_updates": "bad",
        })


def test_fix_contract_requires_description():
    assert validate_fix_response({"description": "A safer description."})["description"]

    with pytest.raises(ContractError, match="description"):
        validate_fix_response({})


def test_tool_name_normalization_accepts_canonical_and_aliases():
    assert normalize_tool_name("describe_entity") == ("describe_entity", False)
    assert normalize_tool_name("Description") == ("describe_entity", True)
    assert normalize_tool_name("Location") == ("move_entity", True)


def test_tool_name_normalization_rejects_unknown_tools():
    with pytest.raises(ContractError, match="unknown tool"):
        normalize_tool_name("teleport_everything")


def test_person_slot_normalization_accepts_canonical_slots():
    assert normalize_person_slot("held") == ("held", False)
    assert normalize_person_slot("worn") == ("worn", False)
    assert normalize_person_slot("body") == ("body", False)


def test_person_slot_normalization_maps_legacy_inventory_to_held():
    assert normalize_person_slot("inventory") == ("held", True)


def test_person_slot_normalization_rejects_unclear_slots():
    with pytest.raises(ContractError, match="invalid slot"):
        normalize_person_slot("pocket-ish")


def test_state_update_normalization_preserves_alias_context():
    update = normalize_state_update({"tool": "Location", "name": "silver key", "location": "here"})

    assert update["tool"] == "move_entity"
    assert update["compatibility_alias"] == "Location"


def test_state_update_normalization_preserves_slot_alias_context():
    update = normalize_state_update({
        "tool": "move_entity",
        "target": "lantern",
        "owner": "Mara",
        "slot": "inventory",
    })

    assert update["slot"] == "held"
    assert update["slot_alias"] == "inventory"


def test_state_update_shape_validation_does_not_rewrite_route_payloads():
    payload = validate_turn_response({
        "narrative": "The key appears.",
        "state_updates": [{"tool": "Description", "name": "silver key", "description": "A small key."}],
    })

    assert payload["state_updates"][0]["tool"] == "Description"


def test_normalize_state_updates_rejects_malformed_updates():
    with pytest.raises(ContractError, match="state update"):
        normalize_state_updates(["bad"])

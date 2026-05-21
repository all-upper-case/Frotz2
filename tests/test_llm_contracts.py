import pytest

from llm_contracts import (
    ContractError,
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

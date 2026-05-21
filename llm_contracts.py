"""
Lightweight validation for model responses before they mutate world state.

The engine still keeps defaults and repair behavior in WorldManager, but route
handlers should reject clearly malformed or error-shaped LLM responses before
calling mutation methods.
"""

from copy import deepcopy


class ContractError(ValueError):
    """Raised when an LLM response cannot safely be applied."""


_REQUIRED_FIELDS = {
    "genesis": (
        "intro_text",
        "starting_room_name",
        "starting_room_description",
        "player_description",
        "narrative_thread",
        "blueprint",
    ),
    "room": ("room_name", "room_description"),
    "turn": ("narrative",),
    "fix": ("description",),
}


def _ensure_mapping(data, contract_name):
    if not isinstance(data, dict):
        raise ContractError(f"{contract_name} response was not a JSON object.")

    if data.get("error"):
        detail = data.get("narrative") or data.get("message") or data.get("error")
        raise ContractError(str(detail))

    return deepcopy(data)


def _ensure_required_strings(data, contract_name):
    missing = []
    for field in _REQUIRED_FIELDS[contract_name]:
        value = data.get(field)
        if not isinstance(value, str) or not value.strip():
            missing.append(field)

    if missing:
        fields = ", ".join(missing)
        raise ContractError(f"{contract_name} response missing required field(s): {fields}.")


def _normalize_list_field(data, field):
    value = data.get(field, [])
    if value is None:
        data[field] = []
        return
    if not isinstance(value, list):
        raise ContractError(f"{field} must be a list.")


def validate_genesis_response(data):
    result = _ensure_mapping(data, "genesis")
    _ensure_required_strings(result, "genesis")
    _normalize_list_field(result, "new_exits")
    _normalize_list_field(result, "state_updates")
    return result


def validate_room_response(data):
    result = _ensure_mapping(data, "room")
    _ensure_required_strings(result, "room")
    _normalize_list_field(result, "new_exits")
    _normalize_list_field(result, "state_updates")
    return result


def validate_turn_response(data):
    result = _ensure_mapping(data, "turn")
    _ensure_required_strings(result, "turn")
    _normalize_list_field(result, "state_updates")
    if "narrative_summary_update" in result and result["narrative_summary_update"] is None:
        result.pop("narrative_summary_update")
    return result


def validate_fix_response(data):
    result = _ensure_mapping(data, "fix")
    _ensure_required_strings(result, "fix")
    return result

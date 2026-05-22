"""
Lightweight validation for model responses before they mutate world state.

The engine still keeps defaults and repair behavior in WorldManager, but route
handlers should reject clearly malformed or error-shaped LLM responses before
calling mutation methods.
"""

from copy import deepcopy


class ContractError(ValueError):
    """Raised when an LLM response cannot safely be applied."""


CANONICAL_TOOLS = {
    "append_memory",
    "create_character",
    "create_entity",
    "describe_entity",
    "move_entity",
    "set_entity_visibility",
    "update_character",
    "update_player",
}

TOOL_ALIASES = {
    "description": "describe_entity",
    "create_item": "describe_entity",
    "update_item": "describe_entity",
    "create_room": "describe_entity",
    "location": "move_entity",
}

TOOL_STATUS = {
    "accepted",
    "accepted_with_repair",
    "ambiguous_target",
    "ignored_duplicate",
    "ignored_empty",
    "invalid_entity_type",
    "invalid_location",
    "invalid_schema",
    "missing_target",
    "rejected_error_response",
    "unknown_tool",
}

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


def _validate_state_updates_shape(data):
    _normalize_list_field(data, "state_updates")
    for update in data["state_updates"]:
        if not isinstance(update, dict):
            raise ContractError("state update must be a JSON object.")
        if not isinstance(update.get("tool"), str) or not update.get("tool", "").strip():
            raise ContractError("state update tool must be a non-empty string.")


def normalize_tool_name(tool_name):
    """Return the canonical tool name plus whether a compatibility alias was used."""
    if not isinstance(tool_name, str) or not tool_name.strip():
        raise ContractError("tool name must be a non-empty string.")

    clean = tool_name.strip().lower()
    canonical = TOOL_ALIASES.get(clean, clean)
    if canonical not in CANONICAL_TOOLS:
        raise ContractError(f"unknown tool: {tool_name}.")
    return canonical, canonical != clean


def normalize_state_update(update):
    """Normalize a single requested state update without applying it."""
    if not isinstance(update, dict):
        raise ContractError("state update must be a JSON object.")

    result = deepcopy(update)
    canonical, used_alias = normalize_tool_name(result.get("tool"))
    result["tool"] = canonical
    if used_alias:
        result["compatibility_alias"] = update.get("tool")
    return result


def normalize_state_updates(updates):
    """Normalize known tool aliases in a state_updates list for future dispatchers/reports."""
    if updates is None:
        return []
    if not isinstance(updates, list):
        raise ContractError("state_updates must be a list.")
    return [normalize_state_update(update) for update in updates]


def validate_genesis_response(data):
    result = _ensure_mapping(data, "genesis")
    _ensure_required_strings(result, "genesis")
    _normalize_list_field(result, "new_exits")
    _validate_state_updates_shape(result)
    return result


def validate_room_response(data):
    result = _ensure_mapping(data, "room")
    _ensure_required_strings(result, "room")
    _normalize_list_field(result, "new_exits")
    _validate_state_updates_shape(result)
    return result


def validate_turn_response(data):
    result = _ensure_mapping(data, "turn")
    _ensure_required_strings(result, "turn")
    _validate_state_updates_shape(result)
    if "narrative_summary_update" in result and result["narrative_summary_update"] is None:
        result.pop("narrative_summary_update")
    return result


def validate_fix_response(data):
    result = _ensure_mapping(data, "fix")
    _ensure_required_strings(result, "fix")
    return result

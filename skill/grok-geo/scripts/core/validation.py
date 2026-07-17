"""JSON Schema validation (draft 2020-12 subset)."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Sequence

from .io_utils import read_json
from .path_utils import schema_path


def validate_against_schema(instance: Any, schema: Dict[str, Any], path: str = "$") -> List[str]:
    errors: List[str] = []

    def err(msg: str) -> None:
        errors.append(f"{path}: {msg}")

    if not isinstance(schema, dict):
        return errors

    if "const" in schema and instance != schema["const"]:
        err(f"expected const {schema['const']!r}")

    if "enum" in schema and instance not in schema["enum"]:
        err(f"value not in enum {schema['enum']}")

    types = schema.get("type")
    if types is not None:
        type_list = types if isinstance(types, list) else [types]
        if not _json_type_matches(instance, type_list):
            err(f"type mismatch, expected {types}, got {type(instance).__name__}")
            return errors

    if instance is None:
        return errors

    if "type" in schema:
        tlist = schema["type"] if isinstance(schema["type"], list) else [schema["type"]]
        if "null" in tlist and instance is None:
            return errors

    if isinstance(instance, dict) and (schema.get("type") == "object" or "properties" in schema or "required" in schema):
        props = schema.get("properties") or {}
        required = schema.get("required") or []
        for key in required:
            if key not in instance:
                err(f"missing required property '{key}'")
        if schema.get("additionalProperties") is False:
            for key in instance:
                if key not in props:
                    err(f"additional property not allowed: '{key}'")
        for key, subschema in props.items():
            if key in instance:
                errors.extend(validate_against_schema(instance[key], subschema, f"{path}.{key}"))
        if "maxProperties" in schema and len(instance) > schema["maxProperties"]:
            err("too many properties")

    if isinstance(instance, list) and (schema.get("type") == "array" or "items" in schema):
        if "maxItems" in schema and len(instance) > schema["maxItems"]:
            err(f"maxItems {schema['maxItems']} exceeded")
        if "minItems" in schema and len(instance) < schema["minItems"]:
            err(f"minItems {schema['minItems']} not met")
        items = schema.get("items")
        if isinstance(items, dict):
            for i, item in enumerate(instance):
                errors.extend(validate_against_schema(item, items, f"{path}[{i}]"))

    if isinstance(instance, str):
        if "minLength" in schema and len(instance) < schema["minLength"]:
            err(f"minLength {schema['minLength']}")
        if "maxLength" in schema and len(instance) > schema["maxLength"]:
            err(f"maxLength {schema['maxLength']}")
        if "pattern" in schema and not re.search(schema["pattern"], instance):
            err(f"pattern mismatch: {schema['pattern']}")
        if schema.get("format") == "uri":
            if not re.match(r"^https?://", instance):
                err("format uri requires http(s)")
        if schema.get("format") == "date":
            if not re.match(r"^\d{4}-\d{2}-\d{2}$", instance):
                err("format date YYYY-MM-DD")

    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        if "minimum" in schema and instance < schema["minimum"]:
            err(f"minimum {schema['minimum']}")
        if "maximum" in schema and instance > schema["maximum"]:
            err(f"maximum {schema['maximum']}")

    return errors


def _json_type_matches(instance: Any, type_list: Sequence[str]) -> bool:
    for t in type_list:
        if t == "object" and isinstance(instance, dict):
            return True
        if t == "array" and isinstance(instance, list):
            return True
        if t == "string" and isinstance(instance, str):
            return True
        if t == "integer" and isinstance(instance, int) and not isinstance(instance, bool):
            return True
        if t == "number" and isinstance(instance, (int, float)) and not isinstance(instance, bool):
            return True
        if t == "boolean" and isinstance(instance, bool):
            return True
        if t == "null" and instance is None:
            return True
    return False


def load_schema(name: str) -> Dict[str, Any]:
    return read_json(schema_path(name))
"""Small stdlib-only JSON Schema 2020-12 subset used by the V1 contracts."""

from __future__ import annotations

import re
import json
from datetime import date
from typing import Any

from .errors import fail


def _type_matches(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "null":
        return value is None
    return False


def _resolve_ref(root: dict[str, Any], ref: str) -> dict[str, Any]:
    if not ref.startswith("#/"):
        fail("SCHEMA_REF_UNSUPPORTED", "V1 schema 只支持本地 $ref。", ref)
    value: Any = root
    for part in ref[2:].split("/"):
        key = part.replace("~1", "/").replace("~0", "~")
        if not isinstance(value, dict) or key not in value:
            fail("SCHEMA_REF_INVALID", "Schema $ref 无法解析。", ref)
        value = value[key]
    if not isinstance(value, dict):
        fail("SCHEMA_REF_INVALID", "Schema $ref 目标不是 object。", ref)
    return value


def validate_schema(instance: Any, schema: dict[str, Any], path: str = "$", root: dict[str, Any] | None = None) -> None:
    root = schema if root is None else root
    if "$ref" in schema:
        validate_schema(instance, _resolve_ref(root, schema["$ref"]), path, root)
        return
    if "const" in schema and instance != schema["const"]:
        fail("SCHEMA_CONST", "值不符合 Schema 固定值。", path)
    if "enum" in schema and instance not in schema["enum"]:
        fail("SCHEMA_ENUM", "值不在 Schema 允许列表中。", path)
    expected = schema.get("type")
    if expected:
        allowed = expected if isinstance(expected, list) else [expected]
        if not any(_type_matches(instance, item) for item in allowed):
            fail("SCHEMA_TYPE", "字段类型不符合 Schema。", path)
    if isinstance(instance, dict):
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        for key in required:
            if key not in instance:
                fail("SCHEMA_REQUIRED", "缺少 Schema 必填字段。", f"{path}.{key}")
        if schema.get("additionalProperties") is False:
            for key in instance:
                if key not in properties:
                    fail("SCHEMA_UNKNOWN_FIELD", "发现 Schema 未声明字段。", f"{path}.{key}")
        for key, child in instance.items():
            if key in properties:
                validate_schema(child, properties[key], f"{path}.{key}", root)
    elif isinstance(instance, list):
        if len(instance) < schema.get("minItems", 0):
            fail("SCHEMA_MIN_ITEMS", "数组元素数量不足。", path)
        if schema.get("uniqueItems"):
            rendered = [json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(",", ":")) for item in instance]
            if len(rendered) != len(set(rendered)):
                fail("SCHEMA_UNIQUE_ITEMS", "数组包含重复元素。", path)
        item_schema = schema.get("items")
        if item_schema:
            for index, child in enumerate(instance):
                validate_schema(child, item_schema, f"{path}[{index}]", root)
    elif isinstance(instance, str):
        if len(instance) < schema.get("minLength", 0):
            fail("SCHEMA_MIN_LENGTH", "字符串长度不足。", path)
        pattern = schema.get("pattern")
        if pattern and re.search(pattern, instance) is None:
            fail("SCHEMA_PATTERN", "字符串不符合 Schema 格式。", path)
        if schema.get("format") == "date":
            try:
                date.fromisoformat(instance)
            except ValueError:
                fail("SCHEMA_DATE", "日期必须为 YYYY-MM-DD。", path)

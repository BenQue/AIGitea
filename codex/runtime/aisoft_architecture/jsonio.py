"""Strict JSON I/O and RFC-8785-inspired deterministic serialization.

The architecture contract intentionally permits only integers, booleans, strings,
arrays, objects and null. Floating point values are rejected so Python's stable
JSON encoding is sufficient for the V1 catalog's canonical bytes.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from .errors import ArchitectureError, Diagnostic, fail

FORBIDDEN_KEY_PARTS = (
    "password",
    "passwd",
    "secret",
    "token",
    "credential",
    "connection_string",
    "database_url",
    "private_key",
)
FORBIDDEN_VALUE_RE = re.compile(
    r"(?:authorization\s*:\s*(?:token|bearer)|[A-Z][A-Z0-9_]*(?:TOKEN|SECRET|PASSWORD)\s*=|"
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----|postgres(?:ql)?://[^/\s:@]+:[^@\s]+@)",
    re.IGNORECASE,
)


def _pairs_no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            fail("JSON_DUPLICATE_KEY", "JSON 包含重复字段。", f"$.{key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    fail("JSON_NON_FINITE_NUMBER", "JSON 不允许 NaN 或 Infinity。", "$", "改用整数或字符串。")


def _reject_floats(value: Any, path: str = "$") -> None:
    if isinstance(value, float):
        fail("JSON_FLOAT_NOT_CANONICAL", "V1 canonical JSON 不允许浮点数。", path)
    if isinstance(value, dict):
        for key, child in value.items():
            _reject_floats(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_floats(child, f"{path}[{index}]")


def _reject_secret_markers(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = key.lower().replace("-", "_")
            if any(marker in normalized for marker in FORBIDDEN_KEY_PARTS):
                fail(
                    "SECRET_FIELD_FORBIDDEN",
                    "架构文件不得包含 Secret 或连接信息字段。",
                    f"{path}.{key}",
                    "只保留脱敏 metadata；凭据应留在既有 Secret 管理边界。",
                )
            _reject_secret_markers(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_secret_markers(child, f"{path}[{index}]")
    elif isinstance(value, str) and FORBIDDEN_VALUE_RE.search(value):
        fail(
            "SECRET_VALUE_FORBIDDEN",
            "架构文件疑似包含 Secret 值。",
            path,
            "删除凭据，只保留脱敏 metadata。",
        )


def loads_strict(raw: str, source: str = "<memory>") -> Any:
    try:
        value = json.loads(
            raw,
            object_pairs_hook=_pairs_no_duplicates,
            parse_constant=_reject_constant,
        )
    except ArchitectureError:
        raise
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ArchitectureError(
            Diagnostic("JSON_INVALID", f"strict JSON 解析失败：第 {exc.lineno} 行第 {exc.colno} 列。", source)
        ) from None
    _reject_floats(value)
    _reject_secret_markers(value)
    return value


def load_json(path: str | Path) -> Any:
    candidate = Path(path)
    if candidate.suffix.lower() in {".yaml", ".yml"}:
        fail(
            "YAML_NOT_SUPPORTED",
            "V1 只接受 strict JSON，不接受 YAML。",
            str(candidate),
            "迁移为 .aisoft/architecture.json；新增 YAML parser 必须另建平台 Change。",
        )
    try:
        return loads_strict(candidate.read_text(encoding="utf-8"), str(candidate))
    except OSError as exc:
        raise ArchitectureError(Diagnostic("FILE_READ_FAILED", "无法读取架构文件。", str(candidate))) from exc


def canonical_bytes(value: Any) -> bytes:
    _reject_floats(value)
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
    ).encode("utf-8")


def sha256_value(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def write_canonical(path: str | Path, value: Any) -> None:
    Path(path).write_bytes(canonical_bytes(value))

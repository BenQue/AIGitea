"""Shared fail-closed validation for sensitive release fields."""

from __future__ import annotations

from collections.abc import Mapping
import re

from .errors import ContractError


SENSITIVE_KEY = re.compile(
    r"(?:^|[_-])(?:auth|authorization|token|password|secret|credential|"
    r"connection[_-]?string|certificate|ssh[_-]?key)(?:$|[_-])",
    re.IGNORECASE,
)
ENV_REFERENCE = re.compile(
    r"^\$\{[A-Za-z_][A-Za-z0-9_]*(?::\?required)?\}$"
)


def is_external_environment_reference(value: object) -> bool:
    return isinstance(value, str) and ENV_REFERENCE.fullmatch(value) is not None


def reject_sensitive_compose_fields(
    value: object,
    context: str = "normalized Compose model",
) -> None:
    """Reject sensitive fields except strict service environment references."""
    _reject_sensitive_compose_fields(value, context, (), "")


def _reject_sensitive_compose_fields(
    value: object,
    context: str,
    path: tuple[str | int, ...],
    display_path: str,
) -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            key_text = str(key)
            field_path = (
                f"{display_path}.{key_text}" if display_path else key_text
            )
            if SENSITIVE_KEY.search(key_text) and not _allowed_sensitive_environment(
                path, nested
            ):
                raise ContractError(
                    f"{context} contains forbidden sensitive field {field_path}"
                )
            _reject_sensitive_compose_fields(
                nested,
                context,
                (*path, key_text),
                field_path,
            )
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            field_path = f"{display_path}[{index}]"
            _reject_sensitive_compose_fields(
                nested,
                context,
                (*path, index),
                field_path,
            )


def _allowed_sensitive_environment(
    parent_path: tuple[str | int, ...], value: object
) -> bool:
    return (
        len(parent_path) == 3
        and parent_path[0] == "services"
        and isinstance(parent_path[1], str)
        and bool(parent_path[1])
        and parent_path[2] == "environment"
        and is_external_environment_reference(value)
    )

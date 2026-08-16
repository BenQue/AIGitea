"""Fail-closed, no-echo secret scanning primitives for handoff payloads."""

from __future__ import annotations

from pathlib import Path
import re

from .contract import CompanyDeliveryError, contains_sensitive_text


CHUNK_BYTES = 1024 * 1024
SCAN_OVERLAP = 512
IDENTIFIER = r"[A-Za-z_][A-Za-z0-9_]*"
EXTERNAL_ENV_REFERENCE = re.compile(
    rf"^\$\{{{IDENTIFIER}(?::\?required)?\}}$"
)


def is_external_environment_reference(value: object) -> bool:
    """Return true only for the platform's complete Compose reference subset."""

    return (
        isinstance(value, str)
        and EXTERNAL_ENV_REFERENCE.fullmatch(value) is not None
    )


def mask_source_placeholders(value: str) -> str:
    """Mask only exact, audited source placeholders before generic text checks."""

    placeholder = (
        r"(?:%[A-Za-z]|\$"
        + IDENTIFIER
        + r"|\$\{"
        + IDENTIFIER
        + r"(?::\?required)?\}|\$\(<\"\$"
        + IDENTIFIER
        + r"\"\)|<[^>\s]+>)"
    )
    patterns = (
        re.compile(
            rf"(?i)authorization\s*:\s*(?:bearer|token)\s+{placeholder}"
        ),
        re.compile(
            rf"(?i)(?:password|passwd|pwd|token|secret|api[_-]?key)"
            rf"\s*[:=]\s*[\"']?{placeholder}[\"']?"
        ),
    )
    for pattern in patterns:
        value = pattern.sub("SECRET_PLACEHOLDER", value)
    return re.sub(
        rf"\$\{{{IDENTIFIER}(?::\?required)?\}}",
        "SECRET_PLACEHOLDER",
        value,
    )


def scan_source_text(path: Path) -> None:
    """Scan one regular source payload without ever returning rejected bytes."""

    carry = ""
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(CHUNK_BYTES), b""):
                text = carry + chunk.decode("latin-1")
                if contains_sensitive_text(mask_source_placeholders(text)):
                    raise CompanyDeliveryError(
                        "SENSITIVE_CONTENT",
                        "bundle contains forbidden sensitive content",
                    )
                carry = text[-SCAN_OVERLAP:]
    except CompanyDeliveryError:
        raise
    except OSError as exc:
        raise CompanyDeliveryError(
            "UNSAFE_PATH", "bundle payload cannot be read"
        ) from exc

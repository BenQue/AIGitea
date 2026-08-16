"""Fail-closed, no-echo secret scanning primitives for handoff payloads."""

from __future__ import annotations

import base64
import binascii
from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass
import json
import math
from pathlib import Path, PurePosixPath
import re
import stat
import tarfile
from typing import BinaryIO

from aisoft_release.security import (
    SENSITIVE_KEY,
    is_external_environment_reference as release_external_reference,
)
from aisoft_release.transport import VerifiedArchiveGraph

from .contract import CompanyDeliveryError, contains_sensitive_text


CHUNK_BYTES = 1024 * 1024
SCAN_OVERLAP = 512
MAX_SIGNATURE_WINDOW_BYTES = 64 * 1024
MAX_JSON_BYTES = 8 * 1024 * 1024
MAX_INNER_MEMBERS = 200_000
MAX_INNER_MEMBER_BYTES = 2 * 1024 * 1024 * 1024
MAX_EXPANDED_BYTES = 8 * 1024 * 1024 * 1024
IDENTIFIER = r"[A-Za-z_][A-Za-z0-9_]*"
EXTERNAL_ENV_REFERENCE = re.compile(
    rf"^\$\{{{IDENTIFIER}(?::\?required)?\}}$"
)
_AUDITED_SOURCE_MARKER = re.compile(
    r"(?m)(?:^|[;{}]\s*)(?:async\s+)?(?:function|const|let|var|class|"
    r"import|export|return|if|for|while)\b|=>|/\*|//|"
    r"[{,]\s*[A-Za-z_$][A-Za-z0-9_$.-]*\s*:|"
    r"\[\s*[A-Za-z_$][A-Za-z0-9_$.-]*\s*(?:,|\])"
)
_SOURCE_LITERAL_KEY = (
    r"(?:authorization|connection[_-]?string|credential|database[_-]?url|"
    r"password|passwd|pwd|private[_-]?key|ssh[_-]?key|token|secret|"
    r"api[_-]?key)"
)
_RUNTIME_SENSITIVE_KEY = re.compile(rf"^{_SOURCE_LITERAL_KEY}$", re.IGNORECASE)
_SOURCE_LITERAL_ASSIGNMENTS = (
    re.compile(
        rf"(?i)[\"']?{_SOURCE_LITERAL_KEY}[\"']?\s*[:=]\s*"
        r'"((?:\\.|[^"\\])*)"'
    ),
    re.compile(
        rf"(?i)[\"']?{_SOURCE_LITERAL_KEY}[\"']?\s*[:=]\s*"
        r"'((?:\\.|[^'\\])*)'"
    ),
    re.compile(
        rf"(?i)[\"']?{_SOURCE_LITERAL_KEY}[\"']?\s*[:=]\s*"
        r"`((?:\\.|[^`\\])*)`"
    ),
)


def is_external_environment_reference(value: object) -> bool:
    """Return true only for the platform's complete Compose reference subset."""

    return (
        release_external_reference(value)
        and isinstance(value, str)
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


def scan_bundle_payloads(
    root: Path,
    *,
    archive_path: Path,
    archive_graph: VerifiedArchiveGraph,
) -> None:
    """Dispatch every payload, treating only the verified image archive specially."""

    scanned_archive = False
    for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()):
        try:
            metadata = path.lstat()
        except OSError as exc:
            raise CompanyDeliveryError(
                "UNSAFE_PATH", "bundle payload is unavailable"
            ) from exc
        if stat.S_ISDIR(metadata.st_mode):
            continue
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
            raise CompanyDeliveryError(
                "UNSAFE_PATH",
                "bundle payload must be a regular non-symlink file",
            )
        if path == archive_path:
            scan_image_archive(path, archive_graph)
            scanned_archive = True
        else:
            scan_source_text(path)
    if not scanned_archive:
        _blocked()


def scan_image_archive(path: Path, graph: VerifiedArchiveGraph) -> None:
    """Scan the canonical reachable Docker/OCI graph without extracting it."""

    budget = _ScanBudget()
    try:
        with tarfile.open(path, mode="r:*") as archive:
            regular: dict[str, tarfile.TarInfo] = {}
            for member in archive:
                name = _safe_outer_name(member.name)
                if member.isfile():
                    if name in regular:
                        _blocked()
                    regular[name] = member
            expected = {member.name: member for member in graph.members}
            if set(regular) != set(expected):
                _blocked()
            for member in graph.members:
                actual = regular[member.name]
                if actual.size != member.size:
                    _blocked()
                handle = archive.extractfile(actual)
                if handle is None:
                    _blocked()
                if member.kind == "layer":
                    _scan_layer(handle, budget)
                elif member.kind in {"image-config", "metadata"}:
                    _scan_outer_payload(
                        handle,
                        actual.size,
                        runtime_context=member.kind == "image-config",
                    )
                else:
                    _blocked()
    except CompanyDeliveryError:
        raise
    except (OSError, tarfile.TarError, UnicodeError, ValueError):
        _blocked()


@dataclass
class _ScanBudget:
    members: int = 0
    expanded_bytes: int = 0


class _HighConfidenceScanner:
    _pem_begin = re.compile(
        rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"
    )
    _pem = re.compile(
        rb"-----BEGIN (?P<label>(?:RSA |EC |OPENSSH )?PRIVATE KEY)-----"
        rb"[ \t]*\r?\n(?P<body>[A-Za-z0-9+/=\r\n \t]{40,65536}?)"
        rb"-----END (?P=label)-----"
    )
    _known_github_prefix = re.compile(rb"\bgh[pousr]_[A-Za-z0-9]{20,}\b")
    _jwt = re.compile(
        rb"\b[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\."
        rb"[A-Za-z0-9_-]{16,}\b"
    )
    _credential_url = re.compile(
        rb"(?i)(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis|amqp)://"
        rb"[^/\s:@]+:(?P<credential>[^/\s]+)@[^/\s]+"
    )
    _authorization = re.compile(
        rb"(?i)authorization\s*:\s*(?:bearer|token)\s+(\S+)"
    )

    def __init__(self) -> None:
        self._carry = b""

    def feed(self, chunk: bytes) -> None:
        window = self._carry + chunk
        if self._known_github_prefix.search(window) is not None:
            _sensitive()
        if self._jwt.search(window) is not None:
            _sensitive()
        for match in self._pem.finditer(window):
            body = re.sub(rb"\s+", b"", match.group("body"))
            if len(body) < 40 or len(body) % 4 != 0:
                continue
            try:
                decoded = base64.b64decode(body, validate=True)
            except (binascii.Error, ValueError):
                continue
            if len(decoded) >= 32:
                _sensitive()
        for match in self._credential_url.finditer(window):
            if _looks_like_credential_material(match.group("credential")):
                _sensitive()
        for match in self._authorization.finditer(window):
            if _looks_like_credential_material(match.group(1)):
                _sensitive()
        starts = list(self._pem_begin.finditer(window))
        if starts:
            last_start = starts[-1].start()
            candidate = window[last_start:]
            if len(candidate) > MAX_SIGNATURE_WINDOW_BYTES:
                if _pem_candidate_body(candidate) is not None:
                    _blocked()
                self._carry = window[-MAX_SIGNATURE_WINDOW_BYTES:]
            else:
                self._carry = candidate
        else:
            self._carry = window[-MAX_SIGNATURE_WINDOW_BYTES:]

    def finish(self) -> None:
        for match in self._pem_begin.finditer(self._carry):
            candidate = self._carry[match.start():]
            body = _pem_candidate_body(candidate)
            if body is not None and len(re.sub(rb"\s+", b"", body)) >= 40:
                _blocked()
        self._carry = b""


def _pem_candidate_body(candidate: bytes) -> bytes | None:
    header_end = candidate.find(b"-----", len(b"-----BEGIN "))
    if header_end < 0:
        return None
    body_start = header_end + len(b"-----")
    if candidate[body_start:body_start + 2] == b"\r\n":
        body_start += 2
    elif candidate[body_start:body_start + 1] == b"\n":
        body_start += 1
    else:
        return None
    body = candidate[body_start:]
    end_marker = body.find(b"-----END ")
    if end_marker >= 0:
        body = body[:end_marker]
    if re.fullmatch(rb"[A-Za-z0-9+/=\r\n \t]*", body) is None:
        return None
    return body


class _EnvironmentCandidate:
    _assignment = re.compile(
        r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_.-]*)\s*[:=]\s*(.*)$"
    )
    _section = re.compile(r"^\s*\[[^\]\r\n]+\]\s*$")

    def __init__(self) -> None:
        self._buffer = bytearray()
        self.candidate = True
        self.entries = 0
        self.sensitive = False

    def feed(self, chunk: bytes) -> None:
        if not self.candidate:
            return
        self._buffer.extend(chunk)
        if len(self._buffer) > MAX_JSON_BYTES and b"\n" not in self._buffer:
            self.candidate = False
            self._buffer.clear()
            return
        while True:
            newline = self._buffer.find(b"\n")
            if newline < 0:
                break
            line = bytes(self._buffer[:newline])
            del self._buffer[: newline + 1]
            self._line(line)
            if not self.candidate:
                self._buffer.clear()
                return

    def finish(self) -> None:
        if self.candidate and self._buffer:
            self._line(bytes(self._buffer))
        self._buffer.clear()
        if self.entries == 0:
            self.candidate = False

    def _line(self, payload: bytes) -> None:
        try:
            line = payload.decode("utf-8").strip()
        except UnicodeDecodeError:
            self.candidate = False
            return
        if not line or line.startswith(("#", ";")):
            return
        if self._section.fullmatch(line) is not None:
            return
        match = self._assignment.fullmatch(line)
        if match is None:
            self.candidate = False
            return
        self.entries += 1
        key, value = match.groups()
        if _is_runtime_sensitive_key(key) and _is_concrete_value(value):
            self.sensitive = True


def _scan_layer(handle: BinaryIO, budget: _ScanBudget) -> None:
    try:
        prefix = handle.peek(6)[:6]
    except (AttributeError, OSError):
        _blocked()
    if prefix.startswith(b"\x1f\x8b"):
        mode = "r|gz"
    elif prefix.startswith((b"BZh", b"\xfd7zXZ", b"\x28\xb5\x2f\xfd")):
        _blocked()
    else:
        mode = "r|"
    names: set[str] = set()
    try:
        with tarfile.open(fileobj=handle, mode=mode) as layer:
            for member in layer:
                budget.members += 1
                if budget.members > MAX_INNER_MEMBERS:
                    _blocked()
                name = _safe_inner_name(
                    member.name, directory=member.isdir()
                )
                if name in names:
                    _blocked()
                names.add(name)
                if member.size < 0 or member.size > MAX_INNER_MEMBER_BYTES:
                    _blocked()
                if member.isdir():
                    continue
                if member.issym() or member.islnk():
                    scanner = _HighConfidenceScanner()
                    scanner.feed(member.linkname.encode("utf-8", errors="strict"))
                    scanner.finish()
                    continue
                if not member.isfile():
                    _blocked()
                budget.expanded_bytes += member.size
                if budget.expanded_bytes > MAX_EXPANDED_BYTES:
                    _blocked()
                member_handle = layer.extractfile(member)
                if member_handle is None:
                    _blocked()
                _scan_inner_payload(member_handle, member.size)
    except CompanyDeliveryError:
        raise
    except (OSError, tarfile.TarError, UnicodeError, ValueError):
        _blocked()


def _scan_outer_payload(
    handle: BinaryIO, declared_size: int, *, runtime_context: bool
) -> None:
    if declared_size < 0 or declared_size > MAX_JSON_BYTES:
        _blocked()
    payload = handle.read(MAX_JSON_BYTES + 1)
    if len(payload) != declared_size or len(payload) > MAX_JSON_BYTES:
        _blocked()
    scanner = _HighConfidenceScanner()
    scanner.feed(payload)
    scanner.finish()
    _scan_structured_payload(
        payload,
        strict_candidate=True,
        runtime_context=runtime_context,
    )


def _scan_inner_payload(handle: BinaryIO, declared_size: int) -> None:
    scanner = _HighConfidenceScanner()
    environment = _EnvironmentCandidate()
    retained = bytearray()
    read_bytes = 0
    while True:
        chunk = handle.read(CHUNK_BYTES)
        if not chunk:
            break
        read_bytes += len(chunk)
        if read_bytes > declared_size:
            _blocked()
        scanner.feed(chunk)
        environment.feed(chunk)
        if len(retained) <= MAX_JSON_BYTES:
            remaining = MAX_JSON_BYTES + 1 - len(retained)
            retained.extend(chunk[:remaining])
    if read_bytes != declared_size:
        _blocked()
    scanner.finish()
    environment.finish()
    if environment.candidate and environment.sensitive:
        _sensitive()
    if read_bytes <= MAX_JSON_BYTES:
        _scan_structured_payload(bytes(retained))
    elif bytes(retained).lstrip()[:1] in {b"{", b"["}:
        _blocked()


def _scan_structured_payload(
    payload: bytes,
    *,
    strict_candidate: bool = False,
    runtime_context: bool = False,
) -> None:
    stripped = payload.lstrip()
    if not stripped:
        return
    if not _looks_like_json_document(stripped):
        return
    if len(payload) > MAX_JSON_BYTES:
        _blocked()
    try:
        value = json.loads(
            payload.decode("utf-8"), object_pairs_hook=_unique_object
        )
    except UnicodeDecodeError:
        _blocked()
    except json.JSONDecodeError:
        if strict_candidate:
            _blocked()
        text = payload.decode("utf-8")
        normalized = _remove_trailing_json_commas(text)
        if normalized != text:
            try:
                value = json.loads(
                    normalized, object_pairs_hook=_unique_object
                )
            except json.JSONDecodeError:
                value = None
            except ValueError:
                _blocked()
            else:
                _scan_json_value(
                    value,
                    context="runtime"
                    if runtime_context
                    else _json_document_context(value),
                )
                return
        _scan_source_literal_assignments(text)
        if _AUDITED_SOURCE_MARKER.search(text) is None:
            _blocked()
        return
    except ValueError:
        _blocked()
    _scan_json_value(
        value,
        context="runtime" if runtime_context else _json_document_context(value),
    )


def _looks_like_json_document(stripped: bytes) -> bool:
    first = stripped[:1]
    if first not in {b"{", b"["}:
        return False
    remainder = stripped[1:].lstrip()
    if not remainder:
        return True
    if first == b"{":
        return remainder[:1] in {b'"', b"}"}
    return remainder[:1] in {
        b'"',
        b"[",
        b"{",
        b"]",
        b"-",
        b"0",
        b"1",
        b"2",
        b"3",
        b"4",
        b"5",
        b"6",
        b"7",
        b"8",
        b"9",
        b"f",
        b"n",
        b"t",
    }


def _remove_trailing_json_commas(value: str) -> str:
    output: list[str] = []
    index = 0
    in_string = False
    escaped = False
    changed = False
    while index < len(value):
        character = value[index]
        if in_string:
            output.append(character)
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
            index += 1
            continue
        if character == '"':
            in_string = True
            output.append(character)
            index += 1
            continue
        if character == ",":
            following = index + 1
            while following < len(value) and value[following].isspace():
                following += 1
            if following < len(value) and value[following] in "]}":
                changed = True
                index += 1
                continue
        output.append(character)
        index += 1
    return "".join(output) if changed else value


def _scan_source_literal_assignments(value: str) -> None:
    for pattern in _SOURCE_LITERAL_ASSIGNMENTS:
        for match in pattern.finditer(value):
            if _looks_like_credential_material(match.group(1)):
                _sensitive()


def _scan_json_value(value: object, *, context: str) -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            key_text = str(key)
            child_context = _json_child_context(key_text, nested, context)
            if (
                child_context == "runtime"
                and key_text.lower() in {"env", "environment"}
                and isinstance(nested, list)
            ):
                for entry in nested:
                    if not isinstance(entry, str) or "=" not in entry:
                        _blocked()
                    name, environment_value = entry.split("=", 1)
                    if SENSITIVE_KEY.search(name) and _is_concrete_value(
                        environment_value
                    ):
                        _sensitive()
            if _is_runtime_sensitive_key(key_text) and isinstance(
                nested, (str, bytes)
            ):
                if not _is_concrete_value(nested):
                    pass
                elif _looks_like_credential_material(nested):
                    _sensitive()
                elif context == "runtime":
                    _sensitive()
                elif context != "source":
                    _blocked()
            _scan_json_value(nested, context=child_context)
    elif isinstance(value, list):
        for nested in value:
            _scan_json_value(nested, context=context)
    elif isinstance(value, (str, bytes)):
        payload = value.encode("utf-8") if isinstance(value, str) else value
        scanner = _HighConfidenceScanner()
        scanner.feed(payload)
        scanner.finish()


def _json_document_context(value: object) -> str:
    if not isinstance(value, Mapping):
        return "generic"
    lowered = {str(key).lower(): nested for key, nested in value.items()}
    if (
        any(
            marker in lowered
            for marker in (
                "$schema",
                "$defs",
                "definitions",
                "openapi",
                "swagger",
            )
        )
        or isinstance(lowered.get("properties"), Mapping)
        or _looks_like_source_map(lowered)
        or any(
            marker in lowered
            for marker in ("locale", "messages", "translations", "i18n")
        )
    ):
        return "source"
    if any(
        marker in lowered and isinstance(lowered[marker], (Mapping, list))
        for marker in (
            "config",
            "runtime",
            "environment",
            "env",
            "credentials",
            "database",
            "datasource",
            "connection",
        )
    ):
        return "runtime"
    return "generic"


def _json_child_context(key: str, value: object, parent: str) -> str:
    if parent in {"runtime", "source"}:
        return parent
    lowered = key.lower()
    if lowered in {
        "$defs",
        "definitions",
        "properties",
        "messages",
        "translations",
        "i18n",
        "examples",
        "example",
        "source",
        "sourcecode",
        "sources",
        "sourcescontent",
    }:
        return "source"
    if lowered in {
        "config",
        "runtime",
        "environment",
        "env",
        "credentials",
        "database",
        "datasource",
        "connection",
    } and isinstance(value, (Mapping, list)):
        return "runtime"
    return parent


def _looks_like_source_map(value: Mapping[str, object]) -> bool:
    return (
        isinstance(value.get("sources"), list)
        and isinstance(value.get("names"), list)
        and isinstance(value.get("mappings"), str)
    )


_KNOWN_TOKEN_TEXT = re.compile(r"^gh[pousr]_[A-Za-z0-9]{20,}$")
_JWT_TEXT = re.compile(
    r"^[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{16,}$"
)
_SOURCE_PLACEHOLDER_TEXT = re.compile(
    rf"^(?:\${IDENTIFIER}|\$\{{{IDENTIFIER}(?::\?required)?\}}|"
    rf"%[A-Za-z]|<[^>\s]+>|\{{{IDENTIFIER}\}}|"
    r"(?:example|placeholder|redacted|changeme|dummy|fixture|test)"
    r"(?:[-_.][A-Za-z0-9_-]+)*)$",
    re.IGNORECASE,
)
_AUTHORIZATION_VALUE_TEXT = re.compile(
    r"^(?:bearer|token)\s+(.+)$", re.IGNORECASE
)
_CREDENTIAL_URL_TEXT = re.compile(
    r"^(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis|amqp)://"
    r"[^/\s:@]+:(?P<credential>[^/\s]+)@[^/\s]+$",
    re.IGNORECASE,
)


def _looks_like_credential_material(value: str | bytes) -> bool:
    if isinstance(value, bytes):
        try:
            value = value.decode("ascii")
        except UnicodeDecodeError:
            return True
    normalized = value.strip().strip("\"'`,;)]}")
    authorization = _AUTHORIZATION_VALUE_TEXT.fullmatch(normalized)
    if authorization is not None:
        normalized = authorization.group(1).strip().strip("\"'`,;)]}")
    credential_url = _CREDENTIAL_URL_TEXT.fullmatch(normalized)
    if credential_url is not None:
        normalized = credential_url.group("credential")
    if not normalized or is_external_environment_reference(normalized):
        return False
    if _SOURCE_PLACEHOLDER_TEXT.fullmatch(normalized) is not None:
        return False
    if _KNOWN_TOKEN_TEXT.fullmatch(normalized) is not None:
        return True
    if _JWT_TEXT.fullmatch(normalized) is not None:
        return True
    if re.fullmatch(r"[A-Fa-f0-9]{32,}", normalized):
        return len(set(normalized.lower())) >= 8
    if len(normalized) < 20 or len(set(normalized)) < 10:
        return False
    classes = sum(
        bool(pattern.search(normalized))
        for pattern in (
            re.compile(r"[a-z]"),
            re.compile(r"[A-Z]"),
            re.compile(r"[0-9]"),
            re.compile(r"[^A-Za-z0-9]"),
        )
    )
    if classes < 3:
        return False
    counts = Counter(normalized)
    entropy = -sum(
        (count / len(normalized)) * math.log2(count / len(normalized))
        for count in counts.values()
    )
    return entropy >= 3.5


def _is_runtime_sensitive_key(value: str) -> bool:
    return (
        SENSITIVE_KEY.search(value) is not None
        or _RUNTIME_SENSITIVE_KEY.fullmatch(value) is not None
    )


def _is_concrete_value(value: str | bytes) -> bool:
    if isinstance(value, bytes):
        try:
            value = value.decode("utf-8")
        except UnicodeDecodeError:
            return True
    normalized = value.strip()
    if (
        len(normalized) >= 2
        and normalized[0] == normalized[-1]
        and normalized[0] in {"\"", "'"}
    ):
        normalized = normalized[1:-1]
    return bool(normalized) and not is_external_environment_reference(normalized)


def _safe_outer_name(name: str) -> str:
    if not name or "\\" in name or "\x00" in name:
        _blocked()
    candidate = PurePosixPath(name)
    if candidate.is_absolute() or any(
        part in {"", ".."} for part in candidate.parts
    ):
        _blocked()
    return str(candidate)


def _safe_inner_name(name: str, *, directory: bool = False) -> str:
    if not name or "\\" in name or "\x00" in name:
        _blocked()
    normalized_input = name[:-1] if directory and name.endswith("/") else name
    candidate = PurePosixPath(normalized_input)
    if (
        candidate.is_absolute()
        or str(candidate) != normalized_input
        or any(part in {"", ".", ".."} for part in candidate.parts)
    ):
        _blocked()
    return str(candidate)


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON field")
        result[key] = value
    return result


def _sensitive() -> None:
    raise CompanyDeliveryError(
        "SENSITIVE_CONTENT", "bundle contains forbidden sensitive content"
    ) from None


def _blocked() -> None:
    raise CompanyDeliveryError(
        "SENSITIVE_SCAN_BLOCKED", "bundle secret scan could not be completed safely"
    ) from None

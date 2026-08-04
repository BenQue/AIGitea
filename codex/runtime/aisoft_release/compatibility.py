"""Strict Docker Engine/Compose/image-store compatibility policy."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date as calendar_date
import json
from pathlib import Path
import re
import stat
from typing import Mapping

from .errors import ContractError, DeploymentError


MATRIX_VERSION = "docker-image-store-compatibility/v1"
VERSION = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
REVISION = re.compile(r"^[0-9]{4}\.[0-9]{2}\.[0-9]+$")
ROW_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")
EVIDENCE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
DATE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
MAX_MATRIX_BYTES = 1024 * 1024


@dataclass(frozen=True)
class DockerCapability:
    engine_version: str
    compose_version: str
    os: str
    architecture: str
    image_store: str


@dataclass(frozen=True)
class CompatibilityDecision:
    matrix_revision: str
    row_id: str
    capability: DockerCapability


@dataclass(frozen=True)
class _Range:
    minimum: tuple[int, int, int]
    maximum_exclusive: tuple[int, int, int]

    def contains(self, value: tuple[int, int, int]) -> bool:
        return self.minimum <= value < self.maximum_exclusive


@dataclass(frozen=True)
class _Row:
    row_id: str
    engine: _Range
    compose: _Range
    os: str
    architecture: str
    image_store: str
    status: str
    has_real_evidence: bool
    remediation: str

    def matches(self, capability: DockerCapability) -> bool:
        return (
            self.os == capability.os
            and self.architecture == capability.architecture
            and self.image_store == capability.image_store
            and self.engine.contains(_parse_version(capability.engine_version, "Engine"))
            and self.compose.contains(_parse_version(capability.compose_version, "Compose"))
        )


def default_compatibility_path() -> Path:
    source = Path(__file__).resolve()
    candidates = (
        source.parents[2] / "compatibility" / "image-stores-v1.json",
        source.parents[3]
        / "docker-release"
        / "compatibility"
        / "image-stores-v1.json",
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise ContractError("Docker image-store compatibility matrix is not installed")


def require_supported(
    capability: DockerCapability, matrix_path: Path | str | None = None
) -> CompatibilityDecision:
    path = Path(matrix_path) if matrix_path is not None else default_compatibility_path()
    revision, rows = _load_matrix(path)
    matches = [row for row in rows if row.matches(capability)]
    if len(matches) != 1:
        raise DeploymentError(
            "Docker runtime capability is not covered by exactly one compatibility row"
        )
    row = matches[0]
    if row.status != "supported":
        raise DeploymentError(
            f"Docker image-store compatibility row {row.row_id} is rejected: "
            + row.remediation
        )
    if not row.has_real_evidence:
        raise ContractError(
            f"supported compatibility row {row.row_id} lacks real E2E evidence"
        )
    return CompatibilityDecision(
        matrix_revision=revision,
        row_id=row.row_id,
        capability=capability,
    )


def _load_matrix(path: Path) -> tuple[str, tuple[_Row, ...]]:
    try:
        if path.is_symlink():
            raise ContractError("Docker compatibility matrix must not be a symlink")
        metadata = path.stat()
        if not stat.S_ISREG(metadata.st_mode):
            raise ContractError("Docker compatibility matrix must be a regular file")
        if metadata.st_size > MAX_MATRIX_BYTES:
            raise ContractError("Docker compatibility matrix exceeds bounded size")
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique)
    except ContractError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise ContractError("Docker compatibility matrix is not valid strict JSON") from exc
    if not isinstance(value, Mapping):
        raise ContractError("Docker compatibility matrix root must be an object")
    _expect_keys(value, {"contract_version", "matrix_revision", "rows"}, "matrix")
    if value.get("contract_version") != MATRIX_VERSION:
        raise ContractError(f"Docker compatibility matrix must use {MATRIX_VERSION}")
    revision = value.get("matrix_revision")
    if not isinstance(revision, str) or not REVISION.fullmatch(revision):
        raise ContractError("Docker compatibility matrix revision is invalid")
    raw_rows = value.get("rows")
    if not isinstance(raw_rows, list) or not raw_rows:
        raise ContractError("Docker compatibility matrix rows must be non-empty")
    rows = tuple(_parse_row(item, index) for index, item in enumerate(raw_rows))
    identifiers = [row.row_id for row in rows]
    if len(identifiers) != len(set(identifiers)):
        raise ContractError("Docker compatibility matrix contains duplicate row IDs")
    return revision, rows


def _parse_row(value: object, index: int) -> _Row:
    context = f"matrix rows[{index}]"
    if not isinstance(value, Mapping):
        raise ContractError(f"{context} must be an object")
    _expect_keys(
        value,
        {
            "row_id",
            "engine",
            "compose",
            "os",
            "architecture",
            "image_store",
            "status",
            "evidence",
            "remediation",
        },
        context,
    )
    row_id = value.get("row_id")
    if not isinstance(row_id, str) or not ROW_ID.fullmatch(row_id):
        raise ContractError(f"{context} row_id is invalid")
    os_name = value.get("os")
    architecture = value.get("architecture")
    image_store = value.get("image_store")
    status = value.get("status")
    if os_name != "linux" or architecture != "amd64":
        raise ContractError(f"{context} supports only linux/amd64")
    if image_store not in {"containerd", "classic"}:
        raise ContractError(f"{context} image_store is invalid")
    if status not in {"supported", "rejected"}:
        raise ContractError(f"{context} status is invalid")
    remediation = value.get("remediation")
    if (
        not isinstance(remediation, str)
        or not remediation.strip()
        or len(remediation) > 512
        or any(ord(character) < 32 for character in remediation)
    ):
        raise ContractError(f"{context} remediation is invalid")
    evidence = value.get("evidence")
    has_real_evidence = _validate_evidence(evidence, context)
    if status == "supported" and not has_real_evidence:
        raise ContractError(f"{context} supported row requires real E2E evidence")
    return _Row(
        row_id=row_id,
        engine=_parse_range(value.get("engine"), context + " engine"),
        compose=_parse_range(value.get("compose"), context + " compose"),
        os=str(os_name),
        architecture=str(architecture),
        image_store=str(image_store),
        status=str(status),
        has_real_evidence=has_real_evidence,
        remediation=remediation,
    )


def _parse_range(value: object, context: str) -> _Range:
    if not isinstance(value, Mapping):
        raise ContractError(f"{context} must be an object")
    _expect_keys(value, {"minimum", "maximum_exclusive"}, context)
    minimum = _parse_version(value.get("minimum"), context + " minimum")
    maximum = _parse_version(value.get("maximum_exclusive"), context + " maximum")
    if minimum >= maximum:
        raise ContractError(f"{context} range is empty or reversed")
    return _Range(minimum=minimum, maximum_exclusive=maximum)


def _validate_evidence(value: object, context: str) -> bool:
    if value is None:
        return False
    if not isinstance(value, Mapping):
        raise ContractError(f"{context} evidence must be an object or null")
    _expect_keys(value, {"kind", "evidence_id", "date", "source"}, context + " evidence")
    if value.get("kind") != "real-e2e":
        raise ContractError(f"{context} evidence kind must be real-e2e")
    evidence_id = value.get("evidence_id")
    date = value.get("date")
    source = value.get("source")
    if not isinstance(evidence_id, str) or not EVIDENCE_ID.fullmatch(evidence_id):
        raise ContractError(f"{context} evidence_id is invalid")
    if not isinstance(date, str) or not DATE.fullmatch(date):
        raise ContractError(f"{context} evidence date is invalid")
    try:
        calendar_date.fromisoformat(date)
    except ValueError as exc:
        raise ContractError(f"{context} evidence date is invalid") from exc
    if not isinstance(source, str) or not source.strip() or len(source) > 512:
        raise ContractError(f"{context} evidence source is invalid")
    return True


def _parse_version(value: object, context: str) -> tuple[int, int, int]:
    if not isinstance(value, str) or not VERSION.fullmatch(value):
        raise ContractError(f"{context} version must be exact major.minor.patch")
    return tuple(int(part) for part in value.split("."))  # type: ignore[return-value]


def _expect_keys(value: Mapping[str, object], expected: set[str], context: str) -> None:
    actual = set(value)
    if actual != expected:
        missing = sorted(expected - actual)
        unknown = sorted(actual - expected)
        detail = []
        if missing:
            detail.append("missing " + ", ".join(missing))
        if unknown:
            detail.append("unknown " + ", ".join(unknown))
        raise ContractError(f"{context} fields are invalid: " + "; ".join(detail))


def _unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON field: {key}")
        result[key] = value
    return result

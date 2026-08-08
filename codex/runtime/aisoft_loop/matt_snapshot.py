"""Deterministic integrity and update classification for vendored Matt skills."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from typing import Mapping


class SnapshotError(ValueError):
    """A Matt snapshot or manifest violates the platform contract."""


CRITICAL_SKILLS = (
    "implement",
    "setup-matt-pocock-skills",
    "to-spec",
    "to-tickets",
    "triage",
)
TOOL_SUFFIXES = frozenset({".js", ".mjs", ".py", ".sh", ".ts"})
CONTROL_LINE_RE = re.compile(
    r"^(?:#{1,6}\s+|\d+[.)]\s+)"
    r"|\b(?:commit|push|merge|rebase|reset|force-push|deploy|permission|"
    r"network|curl|https?://|tool|script|shell|command|execute|tracker|"
    r"issue|ticket|label)\b",
    re.IGNORECASE,
)


def build_manifest(
    snapshot: Path | str,
    *,
    tag: str,
    commit: str,
    tag_object: str,
    source: str = "https://github.com/mattpocock/skills",
    license_name: str = "MIT",
    adapter_contract_version: int = 1,
) -> dict[str, object]:
    root = Path(snapshot).resolve()
    if not root.is_dir() or not (root / "skills").is_dir():
        raise SnapshotError("snapshot must contain a skills directory")
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise SnapshotError("release commit must be a full lowercase SHA")
    if not re.fullmatch(r"[0-9a-f]{40}", tag_object):
        raise SnapshotError("tag object must be a full lowercase SHA")
    license_path = root / "LICENSE"
    if not license_path.is_file():
        raise SnapshotError("snapshot LICENSE is missing")

    skills: list[dict[str, object]] = []
    names: set[str] = set()
    for skill_file in sorted((root / "skills").glob("**/SKILL.md")):
        relative_skill = skill_file.relative_to(root).as_posix()
        name, disable_model = _skill_front_matter(skill_file)
        if name in names:
            raise SnapshotError(f"duplicate skill name: {name}")
        names.add(name)
        directory = skill_file.parent
        tool_files = sorted(
            path.relative_to(directory).as_posix()
            for path in directory.rglob("*")
            if path.is_file()
            and ("scripts" in path.relative_to(directory).parts or path.suffix in TOOL_SUFFIXES)
        )
        skills.append(
            {
                "name": name,
                "path": relative_skill,
                "sha256": _directory_hash(directory),
                "control_sha256": _control_hash(skill_file),
                "disable_model_invocation": disable_model,
                "tool_files": tool_files,
            }
        )
    if not skills:
        raise SnapshotError("snapshot contains no skills")
    return {
        "schema_version": 1,
        "source": source,
        "tag": tag,
        "tag_object": tag_object,
        "commit": commit,
        "license": license_name,
        "license_sha256": _file_hash(license_path),
        "adapter_contract_version": adapter_contract_version,
        "critical_skills": list(CRITICAL_SKILLS),
        "skill_count": len(skills),
        "skills": skills,
    }


def verify_snapshot(
    snapshot: Path | str, manifest: Mapping[str, object]
) -> dict[str, object]:
    required = {
        "schema_version",
        "source",
        "tag",
        "tag_object",
        "commit",
        "license",
        "license_sha256",
        "adapter_contract_version",
        "critical_skills",
        "skill_count",
        "skills",
    }
    if set(manifest) != required:
        raise SnapshotError("manifest must use the exact schema")
    rebuilt = build_manifest(
        snapshot,
        tag=_string(manifest, "tag"),
        commit=_string(manifest, "commit"),
        tag_object=_string(manifest, "tag_object"),
        source=_string(manifest, "source"),
        license_name=_string(manifest, "license"),
        adapter_contract_version=_integer(manifest, "adapter_contract_version"),
    )
    if list(manifest.get("critical_skills", [])) != list(CRITICAL_SKILLS):
        raise SnapshotError("critical skill contract changed")
    declared_skills = manifest.get("skills")
    if not isinstance(declared_skills, list):
        raise SnapshotError("manifest skills must be a list")
    declared_names = {
        str(item.get("name")) for item in declared_skills if isinstance(item, Mapping)
    }
    rebuilt_names = {
        str(item["name"]) for item in rebuilt["skills"] if isinstance(item, Mapping)
    }
    if declared_names != rebuilt_names:
        raise SnapshotError("snapshot skill set does not match manifest")
    if dict(manifest) != rebuilt:
        raise SnapshotError("snapshot content or metadata does not match manifest")
    return {
        "tag": rebuilt["tag"],
        "commit": rebuilt["commit"],
        "skill_count": rebuilt["skill_count"],
        "skill_names": sorted(rebuilt_names),
    }


def classify_update(
    current: Mapping[str, object], candidate: Mapping[str, object]
) -> dict[str, object]:
    current_skills = _skills_by_name(current)
    candidate_skills = _skills_by_name(candidate)
    reasons: list[str] = []
    if set(current_skills) != set(candidate_skills):
        reasons.append("skill set changed")
    for name in sorted(set(current_skills) & set(candidate_skills)):
        before = current_skills[name]
        after = candidate_skills[name]
        if before.get("disable_model_invocation") != after.get(
            "disable_model_invocation"
        ):
            reasons.append(f"invocation policy changed: {name}")
        if before.get("tool_files") != after.get("tool_files"):
            reasons.append(f"tool surface changed: {name}")
        if before.get("control_sha256") != after.get("control_sha256"):
            reasons.append(f"workflow or side-effect contract changed: {name}")
        if name in CRITICAL_SKILLS and before.get("sha256") != after.get("sha256"):
            reasons.append(f"critical skill changed: {name}")
    if current.get("adapter_contract_version") != candidate.get(
        "adapter_contract_version"
    ):
        reasons.append("adapter contract version changed")
    return {
        "classification": "complex" if reasons else "maintenance-candidate",
        "reasons": reasons,
    }


def _skills_by_name(manifest: Mapping[str, object]) -> dict[str, Mapping[str, object]]:
    raw = manifest.get("skills")
    if not isinstance(raw, list):
        raise SnapshotError("manifest skills must be a list")
    result: dict[str, Mapping[str, object]] = {}
    for item in raw:
        if not isinstance(item, Mapping) or not isinstance(item.get("name"), str):
            raise SnapshotError("manifest skill entry is invalid")
        name = str(item["name"])
        if name in result:
            raise SnapshotError(f"duplicate manifest skill: {name}")
        result[name] = item
    return result


def _skill_front_matter(skill_file: Path) -> tuple[str, bool]:
    text = skill_file.read_text(encoding="utf-8")
    match = re.match(r"^---\n([\s\S]*?)\n---(?:\n|$)", text)
    if not match:
        raise SnapshotError(f"skill front matter is missing: {skill_file}")
    name = ""
    disable_model = False
    for line in match.group(1).splitlines():
        if line.startswith("name:"):
            name = line.split(":", 1)[1].strip().strip("'\"")
        if line.startswith("disable-model-invocation:"):
            value = line.split(":", 1)[1].strip().lower()
            if value not in {"true", "false"}:
                raise SnapshotError(f"invalid invocation policy: {skill_file}")
            disable_model = value == "true"
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name):
        raise SnapshotError(f"invalid skill name: {skill_file}")
    return name, disable_model


def _directory_hash(directory: Path) -> str:
    digest = hashlib.sha256()
    files = sorted(path for path in directory.rglob("*") if path.is_file())
    for path in files:
        relative = path.relative_to(directory).as_posix().encode("utf-8")
        digest.update(len(relative).to_bytes(4, "big"))
        digest.update(relative)
        content = path.read_bytes()
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return digest.hexdigest()


def _file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _control_hash(skill_file: Path) -> str:
    lines = [
        line.strip()
        for line in skill_file.read_text(encoding="utf-8").splitlines()
        if CONTROL_LINE_RE.search(line)
    ]
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def _string(manifest: Mapping[str, object], name: str) -> str:
    value = manifest.get(name)
    if not isinstance(value, str) or not value:
        raise SnapshotError(f"manifest {name} must be a non-empty string")
    return value


def _integer(manifest: Mapping[str, object], name: str) -> int:
    value = manifest.get(name)
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise SnapshotError(f"manifest {name} must be a positive integer")
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="matt-snapshot")
    subparsers = parser.add_subparsers(dest="command", required=True)
    verify = subparsers.add_parser("verify")
    verify.add_argument("snapshot", type=Path)
    verify.add_argument("manifest", type=Path)
    compare = subparsers.add_parser("classify")
    compare.add_argument("current", type=Path)
    compare.add_argument("candidate", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "verify":
            manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
            print(json.dumps(verify_snapshot(args.snapshot, manifest), sort_keys=True))
        else:
            current = json.loads(args.current.read_text(encoding="utf-8"))
            candidate = json.loads(args.candidate.read_text(encoding="utf-8"))
            print(json.dumps(classify_update(current, candidate), sort_keys=True))
    except (OSError, UnicodeError, json.JSONDecodeError, SnapshotError) as exc:
        print(f"matt snapshot verification failed: {exc}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""ADR 0001 D3 guard: registered project names stay in their allowed places.

Project names come from the canonical manifests, never from this file. Hits
outside the allow list may only shrink: a new file or a higher count than the
baseline fails; a lower count only prints a note (#368).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GOVERNANCE = Path("codex/config/gitea-governance.json")
ACCESS = Path("codex/config/host-access-broker.json")
BASELINE = Path("codex/config/project-leak-baseline.json")
ALLOWED_PREFIXES = (
    "codex/config/", "codex/vendor/", "docs/changes/", "docs/adr/",
    "docs/governance/", "archive/",
)
ALLOWED_FILES = {"06-运维手册与踩坑集.md"}
ALLOWED_SEGMENTS = {"tests", "fixtures"}


def project_names(root: Path, retired: list[str]) -> list[str]:
    governance = json.loads((root / GOVERNANCE).read_text(encoding="utf-8"))
    repositories = {
        entry["name"] for entry in governance["repositories"]
        if entry.get("classification") == "internal-application"
    }
    names = set(repositories)
    access = json.loads((root / ACCESS).read_text(encoding="utf-8"))
    for project in access["projects"]:
        if project.get("repository") not in repositories:
            continue
        names.add(project["project_id"])
    names.update(retired)
    return sorted({name.lower() for name in names if name})


def allowed(path: str) -> bool:
    if path.startswith(ALLOWED_PREFIXES) or path in ALLOWED_FILES:
        return True
    if path.endswith("_test.go"):
        return True
    return bool(ALLOWED_SEGMENTS.intersection(path.split("/")[:-1]))


def tracked_files(root: Path) -> list[str]:
    output = subprocess.run(
        ["git", "-c", "core.quotepath=off", "ls-files", "-z"],
        cwd=root, check=True, capture_output=True,
    ).stdout
    return [item.decode("utf-8") for item in output.split(b"\0") if item]


def count_hits(root: Path, names: list[str]) -> dict[str, int]:
    hits: dict[str, int] = {}
    for path in tracked_files(root):
        if allowed(path):
            continue
        try:
            text = (root / path).read_text(encoding="utf-8").lower()
        except (UnicodeDecodeError, IsADirectoryError, FileNotFoundError):
            continue
        total = sum(text.count(name) for name in names)
        if total:
            hits[path] = total
    return hits


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--write-baseline", action="store_true")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    baseline = json.loads((root / BASELINE).read_text(encoding="utf-8"))
    names = project_names(root, baseline.get("retired", []))
    hits = count_hits(root, names)
    if args.write_baseline:
        baseline["files"] = dict(sorted(hits.items()))
        (root / BASELINE).write_text(
            json.dumps(baseline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"project-leak baseline written: {len(hits)} files, {sum(hits.values())} hits")
        return 0
    known = baseline.get("files", {})
    failures = []
    for path, count in sorted(hits.items()):
        limit = known.get(path, 0)
        if count > limit:
            failures.append(f"{path}: {count} project-name hits (baseline {limit})")
        elif count < limit:
            print(f"NOTE: {path} dropped to {count} hits (baseline {limit}); tighten with --write-baseline")
    for path in sorted(set(known) - set(hits)):
        print(f"NOTE: {path} has no hits left; tighten with --write-baseline")
    if failures:
        print("FAIL: project names outside ADR 0001 D3 allowed places:", file=sys.stderr)
        for failure in failures:
            print(f"  {failure}", file=sys.stderr)
        return 1
    print(f"PASS: project-leak ({len(hits)} baseline files, {sum(hits.values())} hits)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

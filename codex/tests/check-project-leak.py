#!/usr/bin/env python3
"""ADR 0001 D3 guard: registered project names and site values stay in their allowed places.

Project names come from the canonical manifests, never from this file: every
registered repository except the platform itself, with its project id (#368;
public-test repositories since #396). Site values are the broker manifest's
site segment (#396). Hits outside the allow list may only shrink: a new file
or a higher count than the baseline fails; a lower count only prints a note.
Every baseline file must also be registered in the ADR's D3 exception table (#416).
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[2]
GOVERNANCE = Path("codex/config/gitea-governance.json")
ACCESS = Path("codex/config/host-access-broker.json")
BASELINE = Path("codex/config/project-leak-baseline.json")
ADR = Path("docs/adr/0001-platform-boundary.md")
EXCEPTIONS_HEADING = "#### D3 登记的例外"
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
        if entry.get("classification") != "public-platform"
    }
    names = set(repositories)
    access = json.loads((root / ACCESS).read_text(encoding="utf-8"))
    for project in access["projects"]:
        if project.get("repository") not in repositories:
            continue
        names.add(project["project_id"])
    names.update(retired)
    return sorted({name.lower() for name in names if name})


def site_values(root: Path) -> list[str]:
    """Longest first, so a path or URL is one hit rather than one per account in it."""
    access = json.loads((root / ACCESS).read_text(encoding="utf-8"))
    values = set()
    for value in access.get("site", {}).values():
        parsed = urlparse(value)
        values.add(parsed.netloc if parsed.scheme in {"http", "https"} else value)
    return sorted({value.lower() for value in values if value}, key=lambda v: (-len(v), v))


# Anything Markdown could use to hide or fake a row. The ADR is read without
# rendering, so instead of parsing these the whole file may not contain them.
REGISTER_HEADER = "| 文件 | 理由 |"
REGISTER_SEPARATOR = re.compile(r"\|\s*:?-{3,}:?\s*\|\s*:?-{3,}:?\s*\|")
REGISTER_ROW = re.compile(r"\|\s*`([^`|]+)`\s*\|[^|]*[^|\s][^|]*\|")
HIDING = re.compile(r"```|~~~|<!--|-->|^ {0,3}<[A-Za-z/!?]")


def registered_exceptions(root: Path) -> set[str]:
    """#416: the backticked paths in the first column of the ADR's D3 exception table.

    The register is read strictly instead of rendered: ADR 0001 may contain no
    fence, HTML comment or raw HTML block anywhere; the heading must appear
    exactly once, at column 0; and its section (up to the next heading) may hold
    only prose and one pipe table with rows at column 0. Anything else fails
    closed, so no hidden or example row can register a path."""
    lines = (root / ADR).read_text(encoding="utf-8").splitlines()
    for number, line in enumerate(lines, 1):
        if HIDING.search(line):
            raise ValueError(f"{ADR}:{number}: no fences, HTML comments or raw HTML blocks allowed")
    if lines.count(EXCEPTIONS_HEADING) != 1:
        raise ValueError(f"{ADR}: {EXCEPTIONS_HEADING!r} must appear exactly once")
    tables: list[list[str]] = []
    previous_row = False
    for line in lines[lines.index(EXCEPTIONS_HEADING) + 1:]:
        if line.startswith("#"):
            break
        if re.match(r"( {4}|\t)", line):
            raise ValueError(f"{ADR}: the exception register may not hold indented lines")
        row = line.startswith("|")
        if row and not previous_row:
            tables.append([])
        if row:
            tables[-1].append(line)
        previous_row = row
    if len(tables) != 1:
        raise ValueError(f"{ADR}: the exception register must be exactly one table")
    table = tables[0]
    # A real two-column table: the fixed header, a separator row, then one
    # backticked path and a non-empty reason per row.
    if len(table) < 3 or table[0] != REGISTER_HEADER or not REGISTER_SEPARATOR.fullmatch(table[1]):
        raise ValueError(f"{ADR}: the exception register must start with {REGISTER_HEADER!r} and a separator row")
    paths = set()
    for line in table[2:]:
        match = REGISTER_ROW.fullmatch(line)
        if not match:
            raise ValueError(f"{ADR}: malformed exception row: {line}")
        paths.add(match.group(1))
    return paths


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


def count_hits(root: Path, names: list[str], values: list[str]) -> tuple[dict[str, int], dict[str, int]]:
    hits: dict[str, int] = {}
    site_hits: dict[str, int] = {}
    pattern = re.compile("|".join(map(re.escape, values))) if values else None
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
        site_total = len(pattern.findall(text)) if pattern else 0
        if site_total:
            site_hits[path] = site_total
    return hits, site_hits


def compare(hits: dict[str, int], known: dict[str, int], kind: str) -> list[str]:
    failures = []
    for path, count in sorted(hits.items()):
        limit = known.get(path, 0)
        if count > limit:
            failures.append(f"{path}: {count} {kind} hits (baseline {limit})")
        elif count < limit:
            print(f"NOTE: {path} dropped to {count} {kind} hits (baseline {limit}); "
                  "tighten with --write-baseline")
    for path in sorted(set(known) - set(hits)):
        print(f"NOTE: {path} has no {kind} hits left; tighten with --write-baseline")
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--write-baseline", action="store_true")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    baseline = json.loads((root / BASELINE).read_text(encoding="utf-8"))
    names = project_names(root, baseline.get("retired", []))
    hits, site_hits = count_hits(root, names, site_values(root))
    if args.write_baseline:
        baseline["files"] = dict(sorted(hits.items()))
        baseline["site_files"] = dict(sorted(site_hits.items()))
        (root / BASELINE).write_text(
            json.dumps(baseline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"project-leak baseline written: {len(hits)} files, {sum(hits.values())} hits; "
              f"site {len(site_hits)} files, {sum(site_hits.values())} hits")
        return 0
    failures = compare(hits, baseline.get("files", {}), "project-name")
    failures += compare(site_hits, baseline.get("site_files", {}), "site-value")
    # #416: a baseline entry is only tolerated while the ADR registers it as an exception.
    try:
        registered = registered_exceptions(root)
    except (OSError, UnicodeError, ValueError) as exc:
        registered = set()
        failures.append(f"exception register unreadable: {exc}")
    for path in sorted(set(baseline.get("files", {})) | set(baseline.get("site_files", {}))):
        if path not in registered:
            failures.append(f"{path}: baseline entry not registered in {ADR} {EXCEPTIONS_HEADING}")
    if failures:
        print("FAIL: project names or site values outside ADR 0001 D3 allowed places:",
              file=sys.stderr)
        for failure in failures:
            print(f"  {failure}", file=sys.stderr)
        return 1
    print(f"PASS: project-leak ({len(hits)} baseline files, {sum(hits.values())} hits; "
          f"site {len(site_hits)} files, {sum(site_hits.values())} hits)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

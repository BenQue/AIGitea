"""Credential-free, zero-write check of the Claude-side Matt plugin pin (#355).

Two questions, answered in order:

1. Source: does the marketplace entry in this repository name the same release
   and commit as the vendored snapshot the Codex installer uses? Three places
   must agree, so an upgrade cannot move one of them alone.
2. Installed: is the plugin recorded under the target home the pinned one?

The commit is the key, never the version string: two different commits have
been observed under the same plugin version. The commit is only recorded in
Claude Code's own installed_plugins.json, whose format carries no public
promise, so anything this reader does not recognise is PIN_UNREADABLE rather
than a guess. That file is the only path opened outside this repository.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
PLUGIN = "mattpocock-skills"
MARKETPLACE = "aisoft-platform"
PINNED_ID = f"{PLUGIN}@{MARKETPLACE}"
INSTALLED_SCHEMA = 2

SHA_RE = re.compile(r"[0-9a-f]{40}")
REF_RE = re.compile(r"v[0-9]+(?:\.[0-9]+)*")
INSTALLER_VERSION_RE = re.compile(r'^matt_version="([^"]*)"$', re.MULTILINE)
# Everything echoed from the installed file passes one of these first, so a
# value that is not what its field claims to be is never printed back.
ID_PART_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}")
SCOPE_RE = re.compile(r"[a-z]{1,32}")
VERSION_RE = re.compile(r"[0-9A-Za-z][0-9A-Za-z.+_-]{0,63}")


class SourceMismatch(Exception):
    """The three source-side declarations of the pin do not agree."""


class Unreadable(Exception):
    """The installed record is not in a shape this reader recognises."""


@dataclass(frozen=True)
class Pin:
    ref: str
    sha: str


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    keys = [key for key, _ in pairs]
    if len(set(keys)) != len(keys):
        raise ValueError("duplicate object key")
    return dict(pairs)


def _load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_reject_duplicate_keys)


def _source_json(relative: str) -> dict[str, object]:
    path = ROOT / relative
    try:
        value = _load_json(path)
    except (OSError, ValueError) as error:
        raise SourceMismatch(f"{relative} is not readable JSON ({type(error).__name__})") from error
    if not isinstance(value, dict):
        raise SourceMismatch(f"{relative} is not a JSON object")
    return value


def _repository(url: object) -> str:
    if not isinstance(url, str):
        return ""
    name = url.rstrip("/").lower()
    return name[:-4] if name.endswith(".git") else name


def expected_pin() -> Pin:
    marketplace = _source_json(".claude-plugin/marketplace.json")
    if marketplace.get("name") != MARKETPLACE:
        raise SourceMismatch(f"marketplace name is not {MARKETPLACE}")
    plugins = marketplace.get("plugins")
    if not isinstance(plugins, list):
        raise SourceMismatch("marketplace plugins is not a list")
    entries = [entry for entry in plugins if isinstance(entry, dict) and entry.get("name") == PLUGIN]
    if len(entries) != 1:
        raise SourceMismatch(f"marketplace declares {len(entries)} {PLUGIN} entries, expected exactly 1")
    source = entries[0].get("source")
    if not isinstance(source, dict) or source.get("source") != "url":
        raise SourceMismatch(f"{PLUGIN} entry is not a url source object")
    ref, sha = source.get("ref"), source.get("sha")
    if not isinstance(ref, str) or not REF_RE.fullmatch(ref):
        raise SourceMismatch(f"{PLUGIN} entry ref is not a release tag")
    if not isinstance(sha, str) or not SHA_RE.fullmatch(sha):
        raise SourceMismatch(f"{PLUGIN} entry sha is not a full lowercase commit")

    try:
        installer = (ROOT / "codex/install-skills.sh").read_text(encoding="utf-8")
    except OSError as error:
        raise SourceMismatch("codex/install-skills.sh is not readable") from error
    versions = INSTALLER_VERSION_RE.findall(installer)
    if len(versions) != 1:
        raise SourceMismatch(f"codex/install-skills.sh sets matt_version {len(versions)} times, expected exactly 1")
    if versions[0] != ref:
        raise SourceMismatch(f"entry ref {ref} is not the installer matt_version {versions[0]}")

    manifest_path = f"codex/vendor/mattpocock/{ref}/manifest.json"
    manifest = _source_json(manifest_path)
    if manifest.get("tag") != ref:
        raise SourceMismatch(f"{manifest_path} tag is not {ref}")
    if manifest.get("commit") != sha:
        raise SourceMismatch(f"entry sha {sha} is not the {manifest_path} commit {manifest.get('commit')}")
    if _repository(source.get("url")) != _repository(manifest.get("source")):
        raise SourceMismatch(f"entry url and {manifest_path} source name different repositories")
    return Pin(ref=ref, sha=sha)


@dataclass(frozen=True)
class Record:
    plugin_id: str
    scope: str
    version: str
    commit: str  # a full commit, or the literal "missing"

    def line(self, prefix: str) -> str:
        return f"{prefix}: {self.plugin_id} scope={self.scope} version={self.version} commit={self.commit}"


def _field(entry: dict[str, object], key: str, pattern: re.Pattern[str], absent: str) -> str:
    value = entry.get(key)
    if value is None:
        return absent
    if not isinstance(value, str) or not pattern.fullmatch(value):
        raise Unreadable(f"a {PLUGIN} record has an unrecognised {key}")
    return value


def installed_records(target_home: Path) -> list[Record]:
    path = target_home / ".claude" / "plugins" / "installed_plugins.json"
    if not os.path.lexists(path):
        return []
    if path.is_symlink() or not path.is_file():
        raise Unreadable("installed_plugins.json is not a regular file")
    try:
        data = _load_json(path)
    except (OSError, ValueError) as error:
        raise Unreadable(f"installed_plugins.json is not readable JSON ({type(error).__name__})") from error
    if not isinstance(data, dict):
        raise Unreadable("installed_plugins.json is not a JSON object")
    schema = data.get("version")
    if isinstance(schema, bool) or schema != INSTALLED_SCHEMA:
        raise Unreadable(f"installed_plugins.json schema is not version {INSTALLED_SCHEMA}")
    plugins = data.get("plugins")
    if not isinstance(plugins, dict):
        raise Unreadable("installed_plugins.json plugins is not an object")

    records: list[Record] = []
    for plugin_id, entries in plugins.items():
        name, separator, marketplace = plugin_id.partition("@")
        if name != PLUGIN:
            continue
        if not separator or not ID_PART_RE.fullmatch(marketplace):
            raise Unreadable(f"a {PLUGIN} record has an unrecognised marketplace")
        if not isinstance(entries, list):
            raise Unreadable(f"the {PLUGIN} records are not a list")
        for entry in entries:
            if not isinstance(entry, dict):
                raise Unreadable(f"a {PLUGIN} record is not an object")
            records.append(Record(
                plugin_id=plugin_id,
                scope=_field(entry, "scope", SCOPE_RE, "unknown"),
                version=_field(entry, "version", VERSION_RE, "unknown"),
                commit=_field(entry, "gitCommitSha", SHA_RE, "missing"),
            ))
    return records


def main(argv: list[str]) -> int:
    if len(argv) > 1 or (argv and argv[0].startswith("-") and argv[0] != "--source-only"):
        print("usage: check-plugin-pin.sh [--source-only | <target-home>]", file=sys.stderr)
        return 2
    source_only = argv == ["--source-only"]

    try:
        pin = expected_pin()
    except SourceMismatch as error:
        print(f"PIN_SOURCE_MISMATCH: {error}")
        # Without an agreed pin there is nothing to compare an installation to.
        return 1 if source_only else 2
    if source_only:
        print("PIN_SOURCE_OK")
        print(f"expected: {PINNED_ID} ref={pin.ref} commit={pin.sha}")
        return 0

    target_home = Path(argv[0]) if argv else Path.home()
    try:
        records = installed_records(target_home)
    except Unreadable as error:
        print(f"PIN_UNREADABLE: {error}")
        return 2

    expected = f"expected: {PINNED_ID} ref={pin.ref} commit={pin.sha}"
    if not records:
        print("PIN_NOT_INSTALLED")
        print(expected)
        return 0
    drifted = [record for record in records if record.plugin_id != PINNED_ID or record.commit != pin.sha]
    if drifted:
        print("PIN_DRIFT")
        print(expected)
        for record in drifted:
            print(f"{record.line('DRIFT')} expected={pin.sha}")
        return 1
    print("PIN_CLEAN")
    print(expected)
    for record in records:
        print(record.line("installed"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

"""Read-only report of external skill pack versions (#375; Cursor since #379).

For the human who periodically looks at whether superpowers, Matt or the two
CLIs moved. superpowers follows its official marketplaces and is not pinned;
what this repository records is the last version that went through the 08 §5
adaptation checklist (codex/config/external-skill-adaptation.json). An installed
version newer than that record means the checklist is owed: REVIEW_NEEDED.

Matt is pinned, so its state is whatever skill-for-claude/check-plugin-pin.sh
reports. Nothing here installs, fetches or writes; the only processes started
are `claude --version`, `codex --version` and that pin checker. Formats owned
by Claude Code or Codex carry no public promise: anything unrecognised is
UNKNOWN, never a guess.

Cursor is a usage-layer tool only (ADR 0001 D6). Its marketplace caches Matt
and superpowers outside any platform installer; this report reads the cached
plugin manifests so the same pin and adaptation record cover it. A cached
version says nothing about whether Cursor has it enabled, so the line reads
`cached=`. Cursor lines inform; only REVIEW_NEEDED or UNKNOWN fails the run,
exactly as for superpowers on the other two tools.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess
import sys

try:
    import tomllib
except ImportError:  # pragma: no cover - Python < 3.11
    tomllib = None

ROOT = Path(__file__).resolve().parent.parent.parent
RECORD = ROOT / "codex/config/external-skill-adaptation.json"
PIN_CHECKER = ROOT / "skill-for-claude/check-plugin-pin.sh"
SKILL_INSTALLER = ROOT / "codex/install-skills.sh"
MATT_PACK = "mattpocock-skills"
# Cursor caches each plugin as <marketplace>/<plugin>/<commit>/; the manifest
# name varies with the plugin's packaging, first match wins.
CURSOR_MANIFESTS = (".cursor-plugin/plugin.json", ".claude-plugin/plugin.json", "package.json")
PACK = "superpowers"
CLAUDE_INSTALLED_SCHEMA = 2

VERSION_RE = re.compile(r"[0-9]+(?:\.[0-9]+){1,3}")
ID_PART_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}")
CLI_TIMEOUT_SECONDS = 15


class Unreadable(Exception):
    """A file exists but is not in a shape this reader recognises."""


class RecordInvalid(Exception):
    """The adaptation record in this repository is malformed."""


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    keys = [key for key, _ in pairs]
    if len(set(keys)) != len(keys):
        raise ValueError("duplicate object key")
    return dict(pairs)


def _load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_reject_duplicate_keys)


def _version_key(version: str) -> tuple[int, ...]:
    parts = [int(part) for part in version.split(".")]
    return tuple(parts + [0] * (4 - len(parts)))


def adapted_version() -> str:
    try:
        data = _load_json(RECORD)
    except (OSError, ValueError) as error:
        raise RecordInvalid(f"not readable JSON ({type(error).__name__})") from error
    if not isinstance(data, dict) or set(data) != {"schema_version", PACK}:
        raise RecordInvalid(f"top-level keys must be exactly schema_version and {PACK}")
    if isinstance(data["schema_version"], bool) or data["schema_version"] != 1:
        raise RecordInvalid("schema_version is not 1")
    pack = data[PACK]
    if not isinstance(pack, dict) or set(pack) != {"adapted_version", "issue"}:
        raise RecordInvalid(f"{PACK} keys must be exactly adapted_version and issue")
    version, issue = pack["adapted_version"], pack["issue"]
    if not isinstance(version, str) or not VERSION_RE.fullmatch(version):
        raise RecordInvalid(f"{PACK}.adapted_version is not a dotted numeric version")
    if isinstance(issue, bool) or not isinstance(issue, int) or issue < 1:
        raise RecordInvalid(f"{PACK}.issue is not a positive Issue number")
    return version


def compare(installed: str, adapted: str) -> str:
    if not VERSION_RE.fullmatch(installed):
        return "UNKNOWN"
    have, want = _version_key(installed), _version_key(adapted)
    if have == want:
        return "ADAPTED"
    return "REVIEW_NEEDED" if have > want else "BEHIND"


def _single_version(versions: set[str]) -> str:
    """One recognisable version, or raise: two different ones are ambiguous."""
    if len(versions) != 1:
        raise Unreadable(f"{len(versions)} different {PACK} versions recorded")
    version = next(iter(versions))
    if not VERSION_RE.fullmatch(version):
        raise Unreadable(f"a {PACK} version is not dotted numeric")
    return version


def claude_superpowers(home: Path) -> str | None:
    path = home / ".claude" / "plugins" / "installed_plugins.json"
    if not os.path.lexists(path):
        return None
    if path.is_symlink() or not path.is_file():
        raise Unreadable("installed_plugins.json is not a regular file")
    try:
        data = _load_json(path)
    except (OSError, ValueError) as error:
        raise Unreadable(f"installed_plugins.json is not readable JSON ({type(error).__name__})") from error
    if not isinstance(data, dict):
        raise Unreadable("installed_plugins.json is not a JSON object")
    schema = data.get("version")
    if isinstance(schema, bool) or schema != CLAUDE_INSTALLED_SCHEMA:
        raise Unreadable(f"installed_plugins.json schema is not version {CLAUDE_INSTALLED_SCHEMA}")
    plugins = data.get("plugins")
    if not isinstance(plugins, dict):
        raise Unreadable("installed_plugins.json plugins is not an object")
    versions: set[str] = set()
    for plugin_id, entries in plugins.items():
        name, separator, marketplace = plugin_id.partition("@")
        if name != PACK:
            continue
        if not separator or not ID_PART_RE.fullmatch(marketplace):
            raise Unreadable(f"a {PACK} plugin key has an unrecognised marketplace")
        if not isinstance(entries, list):
            raise Unreadable(f"the {PACK} records are not a list")
        for entry in entries:
            version = entry.get("version") if isinstance(entry, dict) else None
            if not isinstance(version, str):
                raise Unreadable(f"a {PACK} record has no version")
            versions.add(version)
    return _single_version(versions) if versions else None


def _codex_cached_version(home: Path, marketplace: str) -> str | None:
    base = home / ".codex" / "plugins" / "cache" / marketplace / PACK
    if not base.is_dir() or base.is_symlink():
        return None
    versions: set[str] = set()
    try:
        children = sorted(base.iterdir())
    except OSError as error:
        raise Unreadable(f"the cached {PACK} directory is not listable ({type(error).__name__})") from error
    for child in children:
        manifest = child / ".codex-plugin" / "plugin.json"
        if child.is_symlink() or not manifest.is_file():
            continue
        try:
            data = _load_json(manifest)
        except (OSError, ValueError) as error:
            raise Unreadable(f"a cached {PACK} plugin.json is not readable JSON") from error
        version = data.get("version") if isinstance(data, dict) else None
        if not isinstance(version, str):
            raise Unreadable(f"a cached {PACK} plugin.json has no version")
        versions.add(version)
    return _single_version(versions) if versions else None


def codex_superpowers(home: Path, adapted: str) -> str:
    path = home / ".codex" / "config.toml"
    if not os.path.lexists(path):
        return "NOT_INSTALLED config=absent"
    if path.is_symlink() or not path.is_file():
        raise Unreadable("config.toml is not a regular file")
    if tomllib is None:
        raise Unreadable("this Python has no tomllib")
    try:
        config = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise Unreadable(f"config.toml is not readable TOML ({type(error).__name__})") from error
    plugins = config.get("plugins", {})
    marketplaces = config.get("marketplaces", {})
    if not isinstance(plugins, dict) or not isinstance(marketplaces, dict):
        raise Unreadable("config.toml plugins or marketplaces is not a table")
    enabled = []
    for plugin_id, settings in plugins.items():
        name, separator, marketplace = plugin_id.partition("@")
        if name != PACK:
            continue
        if not separator or not ID_PART_RE.fullmatch(marketplace):
            raise Unreadable(f"a {PACK} plugin key has an unrecognised marketplace")
        if not isinstance(settings, dict) or not isinstance(settings.get("enabled", False), bool):
            raise Unreadable(f"the {PACK} plugin setting is not a table with a boolean enabled")
        if settings.get("enabled") is True:
            enabled.append(marketplace)
    if not enabled:
        return f"NOT_INSTALLED enabled=none adapted={adapted}"
    if len(enabled) != 1:
        raise Unreadable(f"{len(enabled)} {PACK} plugins enabled")
    marketplace = enabled[0]
    cached = _codex_cached_version(home, marketplace)
    detail = f"enabled={PACK}@{marketplace}"
    if marketplace in marketplaces and not isinstance(marketplaces[marketplace], dict):
        raise Unreadable("the enabled marketplace entry is not a table")
    if marketplace not in marketplaces:
        return f"NOT_LOADED {detail} marketplace=unregistered cached={cached or 'none'} adapted={adapted}"
    if cached is None:
        return f"UNKNOWN {detail} marketplace=registered cached=none adapted={adapted}"
    return f"{compare(cached, adapted)} {detail} marketplace=registered installed={cached} adapted={adapted}"


def cursor_cached_version(home: Path, plugin: str) -> str | None:
    base = home / ".cursor" / "plugins" / "cache"
    if not os.path.lexists(base):
        return None
    if base.is_symlink() or not base.is_dir():
        raise Unreadable("the Cursor plugin cache is not a directory")
    versions: set[str] = set()
    try:
        marketplaces = sorted(base.iterdir())
        for marketplace in marketplaces:
            directory = marketplace / plugin
            if marketplace.is_symlink() or directory.is_symlink() or not directory.is_dir():
                continue
            for child in sorted(directory.iterdir()):
                if child.is_symlink() or not child.is_dir():
                    continue
                manifest = next((child / name for name in CURSOR_MANIFESTS
                                 if (child / name).is_file() and not (child / name).is_symlink()), None)
                if manifest is None:
                    raise Unreadable(f"a cached Cursor {plugin} has no recognised manifest")
                data = _load_json(manifest)
                version = data.get("version") if isinstance(data, dict) else None
                if not isinstance(version, str):
                    raise Unreadable(f"a cached Cursor {plugin} manifest has no version")
                versions.add(version)
    except (OSError, ValueError) as error:
        raise Unreadable(f"the Cursor {plugin} cache is not readable ({type(error).__name__})") from error
    if not versions:
        return None
    if len(versions) != 1:
        raise Unreadable(f"{len(versions)} different cached Cursor {plugin} versions")
    return next(iter(versions))


def matt_pinned_version() -> str:
    text = SKILL_INSTALLER.read_text(encoding="utf-8")
    match = re.search(r'^matt_version="v([0-9.]+)"$', text, re.M)
    if not match:
        raise RecordInvalid("matt_version is not readable from codex/install-skills.sh")
    return match.group(1)


def cursor_line(home: Path, plugin: str, reference: str, label: str) -> str:
    try:
        cached = cursor_cached_version(home, plugin)
    except Unreadable as error:
        return f"UNKNOWN ({error})"
    if cached is None:
        return f"NOT_INSTALLED {label}={reference}"
    return f"{compare(cached, reference)} cached={cached} {label}={reference}"


def cli_version(name: str) -> str:
    try:
        completed = subprocess.run(
            [name, "--version"], capture_output=True, text=True,
            timeout=CLI_TIMEOUT_SECONDS, check=False, stdin=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        return "NOT_FOUND"
    except (OSError, subprocess.TimeoutExpired):
        return "UNKNOWN"
    match = VERSION_RE.search(completed.stdout) if completed.returncode == 0 else None
    return match.group(0) if match else "UNKNOWN"


def matt_state(home: Path) -> str:
    try:
        completed = subprocess.run(
            ["bash", str(PIN_CHECKER), str(home)], capture_output=True, text=True,
            timeout=CLI_TIMEOUT_SECONDS, check=False, stdin=subprocess.DEVNULL,
        )
    except (OSError, subprocess.TimeoutExpired):
        return "UNKNOWN"
    first = completed.stdout.splitlines()[0] if completed.stdout else ""
    state = first.split(":", 1)[0]
    return state if re.fullmatch(r"PIN_[A-Z_]+", state) else "UNKNOWN"


def main(argv: list[str]) -> int:
    usage = "usage: check-external-skill-versions.sh [--source-only | --home <dir>]"
    if argv == ["--source-only"]:
        source_only, home = True, None
    elif not argv:
        source_only, home = False, Path.home()
    elif len(argv) == 2 and argv[0] == "--home":
        source_only, home = False, Path(argv[1])
    else:
        print(usage, file=sys.stderr)
        return 2

    try:
        adapted = adapted_version()
    except RecordInvalid as error:
        print(f"RECORD_INVALID: {error}")
        return 2
    if source_only:
        print(f"RECORD_OK {PACK} adapted={adapted}")
        return 0
    if not home.is_dir():
        print(f"HOME_MISSING: {home} is not a directory", file=sys.stderr)
        return 2

    clis = [cli_version("claude"), cli_version("codex")]
    lines = [f"CLI claude {clis[0]}", f"CLI codex {clis[1]}"]
    try:
        installed = claude_superpowers(home)
        if installed is None:
            claude = f"NOT_INSTALLED adapted={adapted}"
        else:
            claude = f"{compare(installed, adapted)} installed={installed} adapted={adapted}"
    except Unreadable as error:
        claude = f"UNKNOWN ({error})"
    try:
        codex = codex_superpowers(home, adapted)
    except Unreadable as error:
        codex = f"UNKNOWN ({error})"
    matt = matt_state(home)
    try:
        matt_pin = matt_pinned_version()
    except RecordInvalid as error:
        print(f"RECORD_INVALID: {error}")
        return 2
    cursor_superpowers = cursor_line(home, PACK, adapted, "adapted")
    cursor_matt = cursor_line(home, MATT_PACK, matt_pin, "pinned")
    lines += [f"{PACK.upper()} claude {claude}", f"{PACK.upper()} codex {codex}", f"MATT claude {matt}",
              f"{PACK.upper()} cursor {cursor_superpowers}", f"MATT cursor {cursor_matt}"]

    states = [claude.split()[0], codex.split()[0], cursor_superpowers.split()[0], cursor_matt.split()[0], *clis]
    failing = any(state in {"REVIEW_NEEDED", "UNKNOWN"} for state in states) or matt != "PIN_CLEAN"
    lines.append("RESULT REVIEW_NEEDED" if failing else "RESULT PASS")
    print("\n".join(lines))
    return 1 if failing else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

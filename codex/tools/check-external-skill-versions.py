"""Read-only report of external skill pack versions against the platform pin
(#375; Cursor since #379; pinned on all three tools since #392).

superpowers is pinned by the vendored snapshot that usage/bundle.json declares
(codex/vendor/superpowers/<tag>/). Claude and Codex keep installing it from
their official marketplaces (#392, confirmed by the owner): this report only
compares what they have with the pin. Matt is pinned by codex/install-skills.sh;
its Claude state is whatever skill-for-claude/check-plugin-pin.sh reports.
Cursor is a usage-layer tool with project-level landings only (ADR 0001 D6):
with --repo the report hashes that checkout's .cursor/skills against each
snapshot manifest; the user-level Cursor plugin cache is only an annotation.

Every pack and tool reads PIN_CLEAN, PIN_DRIFT or PIN_NOT_INSTALLED (Cursor
without --repo: NOT_CHECKED). PIN_DRIFT means "this tool is not on the pin: go
through the 08 §5 adaptation checklist first" and fails the run like UNKNOWN;
PIN_NOT_INSTALLED informs. The adaptation record must name the pinned version.

With --capabilities (#408, 08 §7.1) the report ends with one CAPABILITY line
per tool for the minimum capability set (platform skills, Matt pin, superpowers
pin, read-only review CLI, smoke tools) and RESULT follows those three lines:
PASS, KNOWN_EXTERNAL (the only unmet item is registered in KNOWN_EXTERNAL) or
GAP. --capabilities needs --repo: Cursor is read from that checkout only.

Nothing here installs, fetches or writes; the only processes started are
`claude --version`, `codex --version`, the Matt pin checker and, with
--capabilities, `cursor-agent --version` and `cursor-agent status`. Formats owned
by Claude Code, Codex or Cursor carry no public promise: anything unrecognised
is UNKNOWN, never a guess.
"""
from __future__ import annotations

import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys

try:
    import tomllib
except ImportError:  # pragma: no cover - Python < 3.11
    tomllib = None

ROOT = Path(__file__).resolve().parent.parent.parent
RECORD = ROOT / "codex/config/external-skill-adaptation.json"
PIN_CHECKER = ROOT / "skill-for-claude/check-plugin-pin.sh"
BUNDLE = ROOT / "usage/bundle.json"
VENDOR_SOURCE_RE = re.compile(r"^codex/vendor/superpowers/(v[0-9]+\.[0-9]+\.[0-9]+)/manifest\.json$")
SKILL_INSTALLER = ROOT / "codex/install-skills.sh"
MATT_PACK = "mattpocock-skills"
# Cursor caches each plugin as <marketplace>/<plugin>/<commit>/; the manifest
# name varies with the plugin's packaging, first match wins.
CURSOR_MANIFESTS = (".cursor-plugin/plugin.json", ".claude-plugin/plugin.json", "package.json")
CURSOR_SKILLS = ".cursor/skills"
PACK = "superpowers"
CLAUDE_INSTALLED_SCHEMA = 2

SKILL_MANIFEST = ROOT / "skills/skills.manifest"
LOCK_PATH = ".aisoft/platform-usage.lock.json"
SMOKE_TOOLS = ("bash", "python3", "jq", "rg", "git")
# Unmet capability items whose cause lies outside the platform (#408). Key:
# (tool, item, first word of the item state); value: why it is not a GAP.
KNOWN_EXTERNAL = {
    ("codex", "superpowers", "PIN_NOT_INSTALLED"):
        "#392 Codex official marketplace does not offer the pinned version; the platform does not install it",
}

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


def superpowers_pin() -> dict:
    """The snapshot usage/bundle.json declares; the record must name its version."""
    try:
        members = _load_json(BUNDLE)["members"]
        sources = [m["source"] for m in members if m.get("mode") == "vendor" and VENDOR_SOURCE_RE.match(m["source"])]
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise RecordInvalid(f"usage/bundle.json is not readable ({type(error).__name__})") from error
    if len(sources) != 1:
        raise RecordInvalid(f"usage/bundle.json declares {len(sources)} {PACK} snapshots, expected 1")
    try:
        manifest = _load_json(ROOT / sources[0])
        tag, commit = manifest["tag"], manifest["commit"]
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise RecordInvalid(f"the {PACK} snapshot manifest is not readable ({type(error).__name__})") from error
    if tag != VENDOR_SOURCE_RE.match(sources[0]).group(1) or not re.fullmatch(r"[0-9a-f]{40}", str(commit)):
        raise RecordInvalid(f"the {PACK} snapshot manifest does not match its directory")
    return {"version": tag[1:], "commit": commit, "manifest": manifest}


def compare(installed: str, pinned: str) -> str:
    if not VERSION_RE.fullmatch(installed):
        return "UNKNOWN"
    return "PIN_CLEAN" if _version_key(installed) == _version_key(pinned) else "PIN_DRIFT"


def _single_version(versions: set[str]) -> str:
    """One recognisable version, or raise: two different ones are ambiguous."""
    if len(versions) != 1:
        raise Unreadable(f"{len(versions)} different {PACK} versions recorded")
    version = next(iter(versions))
    if not VERSION_RE.fullmatch(version):
        raise Unreadable(f"a {PACK} version is not dotted numeric")
    return version


def claude_superpowers(home: Path) -> tuple[str, str] | None:
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
    commits: set[str] = set()
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
            commit = entry.get("gitCommitSha")
            if not isinstance(commit, str) or not re.fullmatch(r"[0-9a-f]{40}", commit):
                raise Unreadable(f"a {PACK} record has no gitCommitSha")
            versions.add(version)
            commits.add(commit)
    if not versions:
        return None
    if len(commits) != 1:
        raise Unreadable(f"{len(commits)} different {PACK} commits recorded")
    return _single_version(versions), next(iter(commits))


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


def _codex_remote_version(home: Path) -> str | None:
    """Read the official remote layout, never infer activation from a cache.

    The caller requires an explicit enabled declaration. No active-version
    pointer is available here: more than one version is unknown, not 'latest'.
    A missing pack permits legacy fallback; a present but invalid pack does not.
    """
    base = home
    try:
        for part in (".codex", "plugins", "cache", "openai-curated-remote", PACK):
            base /= part
            try:
                mode = base.lstat().st_mode
            except FileNotFoundError:
                return None
            if not stat.S_ISDIR(mode):
                raise Unreadable("the Codex remote plugin path contains a link or non-directory")
        versions = []
        for child in sorted(base.iterdir()):
            # The official cache keeps this installation marker next to the
            # version directories. It is not an active-version pointer.
            if child.name == ".codex-remote-plugin-install.json":
                if not stat.S_ISREG(child.lstat().st_mode):
                    raise Unreadable("the Codex remote install marker is not a regular file")
                continue
            versions.append(child)
        if len(versions) != 1:
            raise Unreadable(f"{len(versions)} Codex remote plugin versions recorded")
        release = versions[0]
        if not VERSION_RE.fullmatch(release.name):
            raise Unreadable("the Codex remote plugin directory is not a numeric version")
        for directory in (release, release / ".codex-plugin"):
            if not stat.S_ISDIR(directory.lstat().st_mode):
                raise Unreadable("the Codex remote plugin version contains a link or non-directory")
        metadata = release / ".codex-plugin/plugin.json"
        if not stat.S_ISREG(metadata.lstat().st_mode):
            raise Unreadable("the Codex remote plugin.json is not a regular file")
        data = _load_json(metadata)
        if not isinstance(data, dict) or data.get("name") != PACK:
            raise Unreadable("the Codex remote plugin.json name is not superpowers")
        version = data.get("version")
        if not isinstance(version, str) or not VERSION_RE.fullmatch(version) or version != release.name:
            raise Unreadable("the Codex remote plugin version does not match its directory")
        return version
    except (OSError, ValueError) as error:
        raise Unreadable(f"the Codex remote plugin is not readable ({type(error).__name__})") from error


def codex_superpowers(home: Path, pinned: str) -> str:
    path = home / ".codex" / "config.toml"
    if not os.path.lexists(path):
        return f"PIN_NOT_INSTALLED config=absent pinned={pinned}"
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
        return f"PIN_NOT_INSTALLED enabled=none pinned={pinned}"
    if len(enabled) != 1:
        raise Unreadable(f"{len(enabled)} {PACK} plugins enabled")
    marketplace = enabled[0]
    detail = f"enabled={PACK}@{marketplace}"
    if marketplace in marketplaces and not isinstance(marketplaces[marketplace], dict):
        raise Unreadable("the enabled marketplace entry is not a table")
    # Codex's built-in remote marketplace need not be registered in the legacy
    # marketplaces table. The configured id was retained when its cache moved.
    if marketplace in {"openai-curated", "openai-curated-remote"}:
        remote = _codex_remote_version(home)
        if remote is not None:
            return (f"{compare(remote, pinned)} {detail} marketplace=builtin "
                    f"layout=openai-curated-remote installed={remote} pinned={pinned}")
    cached = _codex_cached_version(home, marketplace)
    # Enabled but its marketplace unregistered: Codex does not load it (#375).
    if marketplace not in marketplaces:
        return f"PIN_NOT_INSTALLED {detail} marketplace=unregistered cached={cached or 'none'} pinned={pinned}"
    if cached is None:
        return f"PIN_NOT_INSTALLED {detail} marketplace=registered cached=none pinned={pinned}"
    return f"{compare(cached, pinned)} {detail} marketplace=registered installed={cached} pinned={pinned}"


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
            if not os.path.lexists(directory):
                continue
            # Present but not a plain directory is a shape this reader does not
            # recognise: UNKNOWN, never NOT_INSTALLED.
            if marketplace.is_symlink() or directory.is_symlink() or not directory.is_dir():
                raise Unreadable(f"a cached Cursor {plugin} entry is not a plain directory")
            for child in sorted(directory.iterdir()):
                if child.is_symlink() or not child.is_dir():
                    raise Unreadable(f"a cached Cursor {plugin} revision is not a plain directory")
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


def _directory_hash(directory: Path) -> str:
    sys.path.insert(0, str(ROOT / "codex/runtime"))
    try:
        from aisoft_loop.matt_snapshot import _directory_hash as digest
    finally:
        sys.path.pop(0)
    return digest(directory)


def repo_pack_state(repo: Path, manifest: dict) -> str:
    """Hash every pinned skill directory under <repo>/.cursor/skills."""
    base = repo / CURSOR_SKILLS
    if os.path.lexists(base) and (base.is_symlink() or not base.is_dir()):
        raise Unreadable(f"{CURSOR_SKILLS} is not a directory")
    present, differs = 0, []
    for item in manifest["skills"]:
        directory = base / item["name"]
        if not os.path.lexists(directory):
            differs.append(item["name"])
            continue
        present += 1
        if directory.is_symlink() or not directory.is_dir() or any(
                p.is_symlink() for p in directory.rglob("*")) or _directory_hash(directory) != item["sha256"]:
            differs.append(item["name"])
    if present == 0:
        return "PIN_NOT_INSTALLED"
    if differs:
        return f"PIN_DRIFT differs={','.join(sorted(differs))}"
    return f"PIN_CLEAN skills={present}"


def cursor_line(home: Path, repo: Path | None, plugin: str, manifest: dict, pinned: str) -> str:
    try:
        cached = cursor_cached_version(home, plugin) or "none"
    except Unreadable:
        cached = "unknown"
    if repo is None:
        return f"NOT_CHECKED cache={cached} pinned={pinned}"
    try:
        state = repo_pack_state(repo, manifest)
    except Unreadable as error:
        return f"UNKNOWN ({error})"
    except OSError as error:
        return f"UNKNOWN ({CURSOR_SKILLS} is not readable: {type(error).__name__})"
    return f"{state} cache={cached} pinned={pinned}"


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


def _sha256(path: Path) -> str:
    import hashlib
    return hashlib.sha256(path.read_bytes()).hexdigest()


def declared_skills() -> dict[str, set[str]]:
    declared: dict[str, set[str]] = {}
    for line in SKILL_MANIFEST.read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.lstrip().startswith("#"):
            name, targets = line.split()
            declared[name] = set(targets.split(","))
    return declared


def _compare_files(pairs: list[tuple[Path, str]], names: dict[Path, str]) -> str:
    """pairs: (installed path, expected sha256). Every skill missing: NOT_INSTALLED."""
    present, differs = set(), set()
    for path, expected in pairs:
        name = names[path]
        if not os.path.lexists(path):
            differs.add(name)
            continue
        present.add(name)
        if path.is_symlink() or not path.is_file() or _sha256(path) != expected:
            differs.add(name)
    if not present:
        return "PIN_NOT_INSTALLED"
    if differs:
        return f"PIN_DRIFT differs={','.join(sorted(differs))}"
    return f"PIN_CLEAN skills={len(set(names.values()))}"


def maintainer_skills(home: Path, provider: str) -> str:
    """Installed maintainer-layer landing against this checkout's skills/ source."""
    base = home / (".claude/skills" if provider == "claude" else ".agents/skills")
    pairs, names = [], {}
    for name, targets in sorted(declared_skills().items()):
        if provider not in targets:
            continue
        source = ROOT / "skills" / name
        files = [source / "SKILL.md", *sorted((source / "references").glob("*.md"))] if provider == "claude" \
            else sorted(p for p in source.rglob("*") if p.is_file())
        for file in files:
            target = base / name / file.relative_to(source)
            pairs.append((target, _sha256(file)))
            names[target] = name
    return _compare_files(pairs, names)


def cursor_platform_skills(repo: Path) -> str:
    """<repo>/.cursor/skills against the bundle release the project pins (latest without a pin)."""
    releases = _load_json(BUNDLE)["releases"]
    reference, pin = releases[-1], "unpinned"
    lock = repo / LOCK_PATH
    # Only an absent lock falls back to the latest release; a lock that is a
    # link, a directory or unreadable is a shape this reader does not trust.
    if os.path.lexists(lock):
        if lock.is_symlink() or not lock.is_file():
            return f"UNKNOWN ({LOCK_PATH} is not a regular file)"
        data = _load_json(lock)
        version = data.get("bundle_version") if isinstance(data, dict) else None
        matches = [entry for entry in releases if entry["version"] == version]
        if not matches:
            return f"UNKNOWN (pinned bundle {version!r} is not in the release history)"
        reference, pin = matches[0], f"pin={version}"
    declared = declared_skills()
    pairs, names = [], {}
    for member in reference["members"]:
        parts = PurePosixPath(member["source"]).parts
        if member.get("mode") != "skill" or len(parts) < 3 or parts[1] not in declared:
            continue
        if "claude" not in declared[parts[1]] or parts[2] == "agents":
            continue
        target = repo / ".cursor/skills" / PurePosixPath(*parts[1:])
        pairs.append((target, member["sha256"]))
        names[target] = parts[1]
    state = _compare_files(pairs, names)
    return f"{state} {pin}"


def codex_matt(home: Path, pinned: str) -> str:
    """The installed vendor snapshot, every skill in it and every load link."""
    vendor = home / ".agents/vendor/mattpocock"
    current = vendor / "current"
    if not os.path.lexists(current):
        return "PIN_NOT_INSTALLED"
    if not current.is_symlink():
        return "UNKNOWN (vendor/mattpocock/current is not a link)"
    if os.readlink(current) != f"releases/v{pinned}":
        return f"PIN_DRIFT current={os.readlink(current)}"
    release = vendor / "releases" / f"v{pinned}"
    source = ROOT / f"codex/vendor/mattpocock/v{pinned}/manifest.json"
    installed = release / "manifest.json"
    if not installed.is_file() or installed.is_symlink() or _sha256(installed) != _sha256(source):
        return "PIN_DRIFT manifest=differs"
    differs = []
    for item in _load_json(source)["skills"]:
        relative = PurePosixPath(item["path"]).parent
        directory = release / relative
        link = home / ".agents/skills" / item["name"]
        if (not directory.is_dir() or directory.is_symlink() or any(p.is_symlink() for p in directory.rglob("*"))
                or _directory_hash(directory) != item["sha256"]
                or not link.is_symlink() or os.readlink(link) != f"../vendor/mattpocock/current/{relative}"):
            differs.append(item["name"])
    if differs:
        return f"PIN_DRIFT differs={','.join(sorted(differs))}"
    return "PIN_CLEAN"


def cursor_review() -> str:
    version = cli_version("cursor-agent")
    if version in {"NOT_FOUND", "UNKNOWN"}:
        return version
    try:
        completed = subprocess.run(
            ["cursor-agent", "status"], capture_output=True, text=True,
            timeout=CLI_TIMEOUT_SECONDS, check=False, stdin=subprocess.DEVNULL,
        )
    except (OSError, subprocess.TimeoutExpired):
        return "UNKNOWN"
    return "OK" if completed.returncode == 0 and "Logged in" in completed.stdout else "NOT_LOGGED_IN"


def capability_line(tool: str, items: list[tuple[str, str, bool]]) -> tuple[str, str]:
    """items: (name, state, met). Returns (verdict, line)."""
    unmet = [(name, state) for name, state, met in items if not met]
    reasons = [KNOWN_EXTERNAL.get((tool, name, state.split()[0])) for name, state in unmet]
    if not unmet:
        verdict = "PASS"
    elif all(reasons):
        verdict = "KNOWN_EXTERNAL"
    else:
        verdict = "GAP"
    # Met items show their state word; an unmet one carries its whole state.
    detail = " ".join(f"{name}={state.split()[0] if met else '[' + state + ']'}" for name, state, met in items)
    known = "".join(f" ({reason})" for reason in reasons if reason) if verdict == "KNOWN_EXTERNAL" else ""
    return verdict, f"CAPABILITY {tool} {verdict} {detail}{known}"


def capabilities(home: Path, repo: Path, superpowers: dict[str, str], matt_claude: str, matt_pin: str,
                 clis: dict[str, str]) -> list[tuple[str, str]]:
    import shutil
    missing = [tool for tool in SMOKE_TOOLS if shutil.which(tool) is None]
    smoke = "OK" if not missing else f"MISSING {','.join(missing)}"

    def safe(reader, *args) -> str:
        try:
            return reader(*args)
        except (Unreadable, OSError, ValueError, KeyError, TypeError) as error:
            return f"UNKNOWN ({type(error).__name__})"

    def clean(state: str) -> bool:
        return state.split()[0] == "PIN_CLEAN"

    def cli_ok(state: str) -> bool:
        return state not in {"NOT_FOUND", "UNKNOWN"}

    rows = []
    for tool in ("claude", "codex"):
        skills = safe(maintainer_skills, home, tool)
        matt = matt_claude if tool == "claude" else safe(codex_matt, home, matt_pin)
        review = "OK" if cli_ok(clis[tool]) else clis[tool]
        rows.append(capability_line(tool, [
            ("platform-skills", skills, clean(skills)), ("matt", matt, clean(matt)),
            ("superpowers", superpowers[tool], clean(superpowers[tool])),
            ("review", review, review == "OK"), ("smoke", smoke, smoke == "OK"),
        ]))
    cursor_skills = safe(cursor_platform_skills, repo)
    review = cursor_review()
    rows.append(capability_line("cursor", [
        ("platform-skills", cursor_skills, clean(cursor_skills)), ("matt", superpowers["cursor-matt"],
         clean(superpowers["cursor-matt"])), ("superpowers", superpowers["cursor"], clean(superpowers["cursor"])),
        ("review", review, review == "OK"),
    ]))
    return rows


def main(argv: list[str]) -> int:
    usage = ("usage: check-external-skill-versions.sh "
             "[--source-only | [--home <dir>] [--repo <checkout>] | [--home <dir>] --repo <checkout> --capabilities]")
    source_only = argv == ["--source-only"]
    with_capabilities = not source_only and "--capabilities" in argv
    if with_capabilities:
        argv = [arg for arg in argv if arg != "--capabilities"]
        if argv.count("--repo") != 1:
            print(usage, file=sys.stderr)
            return 2
    options: dict[str, Path] = {}
    if not source_only:
        for index in range(0, len(argv), 2):
            pair = argv[index:index + 2]
            if len(pair) != 2 or pair[0] not in {"--home", "--repo"} or pair[0] in options:
                print(usage, file=sys.stderr)
                return 2
            options[pair[0]] = Path(pair[1])
    home, repo = options.get("--home", Path.home()), options.get("--repo")

    try:
        adapted = adapted_version()
        pin = superpowers_pin()
        if adapted != pin["version"]:
            raise RecordInvalid(f"{PACK}.adapted_version {adapted} is not the pinned {pin['version']}")
        matt_pin = matt_pinned_version()
        matt_manifest = _load_json(ROOT / f"codex/vendor/mattpocock/v{matt_pin}/manifest.json")
    except (RecordInvalid, OSError, ValueError) as error:
        print(f"RECORD_INVALID: {error}")
        return 2
    pinned = pin["version"]
    if source_only:
        print(f"RECORD_OK {PACK} adapted={adapted} pinned={pinned} commit={pin['commit']}")
        return 0
    if not home.is_dir():
        print(f"HOME_MISSING: {home} is not a directory", file=sys.stderr)
        return 2
    if repo is not None and not repo.is_dir():
        print(f"REPO_MISSING: {repo} is not a directory", file=sys.stderr)
        return 2

    clis = [cli_version("claude"), cli_version("codex")]
    lines = [f"CLI claude {clis[0]}", f"CLI codex {clis[1]}"]
    try:
        installed = claude_superpowers(home)
        if installed is None:
            claude = f"PIN_NOT_INSTALLED pinned={pinned}"
        else:
            version, commit = installed
            state = compare(version, pinned)
            if state == "PIN_CLEAN" and commit != pin["commit"]:
                state = "PIN_DRIFT"
            same = "pinned" if commit == pin["commit"] else "differs"
            claude = f"{state} installed={version} commit={same} pinned={pinned}"
    except Unreadable as error:
        claude = f"UNKNOWN ({error})"
    try:
        codex = codex_superpowers(home, pinned)
    except Unreadable as error:
        codex = f"UNKNOWN ({error})"
    matt = matt_state(home)
    cursor_superpowers = cursor_line(home, repo, PACK, pin["manifest"], pinned)
    cursor_matt = cursor_line(home, repo, MATT_PACK, matt_manifest, matt_pin)
    lines += [f"{PACK.upper()} claude {claude}", f"{PACK.upper()} codex {codex}", f"MATT claude {matt}",
              f"{PACK.upper()} cursor {cursor_superpowers}", f"MATT cursor {cursor_matt}"]

    if with_capabilities:
        rows = capabilities(home, repo, {"claude": claude, "codex": codex, "cursor": cursor_superpowers,
                                         "cursor-matt": cursor_matt}, matt, matt_pin,
                            {"claude": clis[0], "codex": clis[1]})
        lines += [line for _, line in rows]
        verdicts = {verdict for verdict, _ in rows}
        result = "GAP" if "GAP" in verdicts else "KNOWN_EXTERNAL" if "KNOWN_EXTERNAL" in verdicts else "PASS"
        lines.append(f"RESULT {result}")
        print("\n".join(lines))
        return 1 if result == "GAP" else 0

    states = [claude.split()[0], codex.split()[0], cursor_superpowers.split()[0], cursor_matt.split()[0], *clis]
    failing = any(state in {"PIN_DRIFT", "UNKNOWN"} for state in states) or matt != "PIN_CLEAN"
    lines.append("RESULT REVIEW_NEEDED" if failing else "RESULT PASS")
    print("\n".join(lines))
    return 1 if failing else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

#!/usr/bin/env python3
"""Read-only inventory of the #354 install targets.

Writes nothing: it prints one JSON document to stdout. It opens no credential
file. From provider settings it reads only the Matt plugin keys, and it never
prints installPath or projectPath values.

Usage: inventory.py <target-home> <source-checkout>
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys

ADAPTERS = (
    "aisoft-matt-workflow", "aisoft-platform", "gitea-analyze-change",
    "gitea-development-loop", "gitea-implement-change", "gitea-platform-ops",
    "gitea-spec-plan", "issue-session-flow",
)
MATT_LINK_PREFIX = "../vendor/mattpocock/current/"
CLAUDE_SKILLS = ("aisoft-platform", "issue-session-flow")


def matt_directory_hash(directory: Path) -> str:
    """Same construction as aisoft_loop.matt_snapshot._directory_hash."""
    digest = hashlib.sha256()
    for path in sorted(p for p in directory.rglob("*") if p.is_file()):
        relative = path.relative_to(directory).as_posix().encode("utf-8")
        digest.update(len(relative).to_bytes(4, "big"))
        digest.update(relative)
        content = path.read_bytes()
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return digest.hexdigest()


def tree(path: Path) -> dict:
    """Bytes, permission bits and link text of everything below path."""
    digest = hashlib.sha256()
    files = 0
    for current, directories, names in os.walk(path, followlinks=False):
        directories.sort()
        for name in sorted(directories + names):
            entry = Path(current) / name
            info = entry.lstat()
            relative = entry.relative_to(path).as_posix()
            digest.update(f"{relative}\0{stat.S_IMODE(info.st_mode):o}\0".encode())
            if stat.S_ISLNK(info.st_mode):
                digest.update(b"L" + os.readlink(entry).encode())
            elif stat.S_ISREG(info.st_mode):
                files += 1
                digest.update(b"F" + hashlib.sha256(entry.read_bytes()).digest())
    return {"tree_sha256": digest.hexdigest(), "files": files}


def meta(path: Path) -> dict | None:
    if not (path.exists() or path.is_symlink()):
        return None
    info = path.lstat()
    result = {"mode": f"{stat.S_IMODE(info.st_mode):04o}", "uid": info.st_uid, "gid": info.st_gid}
    if stat.S_ISLNK(info.st_mode):
        result["link"] = os.readlink(path)
    return result


def digest_of(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def git(source: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(source), *args], check=True,
                          capture_output=True, text=True).stdout.strip()


def manifest_summary(path: Path) -> dict | None:
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return {key: data[key] for key in ("tag", "tag_object", "commit", "skill_count")}


def codex_managed(home: Path, source: Path) -> dict:
    agents = home / ".agents"
    skills = agents / "skills"
    vendor = agents / "vendor/mattpocock"
    releases = {}
    for release in sorted((vendor / "releases").glob("*")) if (vendor / "releases").is_dir() else []:
        manifest = json.loads((release / "manifest.json").read_text(encoding="utf-8"))
        matched = sum(
            1 for item in manifest["skills"]
            if matt_directory_hash((release / item["path"]).parent) == item["sha256"]
        )
        pinned = source / "codex/vendor/mattpocock" / release.name
        releases[release.name] = {
            **(meta(release) or {}), **tree(release),
            "manifest": manifest_summary(release / "manifest.json"),
            "skills_matching_manifest": f"{matched}/{manifest['skill_count']}",
            "equals_pinned_source": pinned.is_dir()
            and matt_directory_hash(release) == matt_directory_hash(pinned),
        }
    entries, links, adapters, unrelated = {}, {}, {}, {}
    for entry in sorted(skills.iterdir()) if skills.is_dir() else []:
        record = meta(entry) or {}
        if "link" in record:
            if record["link"].startswith(MATT_LINK_PREFIX):
                links[entry.name] = record["link"]
                record["class"] = "matt-managed-link"
            else:
                unrelated[entry.name] = record
                record["class"] = "external-link"
        else:
            record.update(tree(entry))
            if entry.name in ADAPTERS:
                adapters[entry.name] = record["tree_sha256"]
                record["class"] = "platform-adapter"
            else:
                unrelated[entry.name] = record
                record["class"] = "external"
        entries[entry.name] = record
    top = {entry.name: meta(entry) for entry in sorted(agents.iterdir())} if agents.is_dir() else {}
    for name, record in top.items():
        if name not in {"skills", "vendor"} and (agents / name).is_dir() and "link" not in record:
            record.update(tree(agents / name))
    lock = agents / ".skill-lock.json"
    return {
        "agents_dir": meta(agents), "skills_dir": meta(skills), "top_level": top,
        "pointers": {name: (meta(vendor / name) or {}).get("link") for name in ("current", "previous")},
        "releases": releases,
        "skill_lock_sha256": hashlib.sha256(lock.read_bytes()).hexdigest() if lock.is_file() else None,
        "matt_links": links, "matt_link_count": len(links),
        "adapters": adapters, "entry_count": len(entries),
        "digests": {"matt_links": digest_of(links), "adapters": digest_of(adapters),
                    "unrelated": digest_of(unrelated)},
        "unrelated_count": len(unrelated),
        "entries": entries,
    }


def claude_side(home: Path) -> dict:
    plugins = home / ".claude/plugins"
    result: dict = {"platform_skills": {}}
    for name in CLAUDE_SKILLS:
        path = home / ".claude/skills" / name
        result["platform_skills"][name] = tree(path) if path.is_dir() else None
    installed = plugins / "installed_plugins.json"
    records = []
    if installed.is_file():
        data = json.loads(installed.read_text(encoding="utf-8"))
        for plugin_id, items in sorted(data.get("plugins", {}).items()):
            if plugin_id.startswith("mattpocock-skills@"):
                records += [{"id": plugin_id, "scope": item.get("scope"), "version": item.get("version"),
                             "commit": item.get("gitCommitSha")} for item in items]
        result["installed_plugins_sha256"] = hashlib.sha256(installed.read_bytes()).hexdigest()
    result["matt_records"] = records
    settings = home / ".claude/settings.json"
    if settings.is_file():
        data = json.loads(settings.read_text(encoding="utf-8"))
        result["enabled"] = {key: value for key, value in sorted(data.get("enabledPlugins", {}).items())
                             if key.startswith("mattpocock-skills@")}
        result["extra_known_marketplaces"] = sorted(data.get("extraKnownMarketplaces") or {})
    known = plugins / "known_marketplaces.json"
    if known.is_file():
        data = json.loads(known.read_text(encoding="utf-8"))
        result["marketplaces"] = {name: {"source": item.get("source"), "autoUpdate": item.get("autoUpdate")}
                                  for name, item in sorted(data.items())}
    caches = {}
    for cache in sorted(plugins.glob("cache/*/mattpocock-skills/*")):
        caches[cache.relative_to(plugins / "cache").as_posix()] = {
            **tree(cache), "skill_files": sum(1 for _ in cache.glob("skills/**/SKILL.md"))}
    result["matt_caches"] = caches
    return result


def codex_plugin(home: Path) -> dict:
    result: dict = {}
    config = home / ".codex/config.toml"
    if config.is_file():
        lines = config.read_text(encoding="utf-8").splitlines()
        for index, line in enumerate(lines):
            if line.strip().startswith('[plugins."mattpocock-skills@'):
                result[line.strip()] = lines[index + 1].strip() if index + 1 < len(lines) else ""
    caches = {}
    root = home / ".codex/plugins/cache"
    for cache in sorted(root.glob("*/mattpocock-skills/*")):
        caches[cache.relative_to(root).as_posix()] = {
            **tree(cache), "skill_files": sum(1 for _ in cache.glob("skills/**/SKILL.md"))}
    return {"config_entries": result, "matt_caches": caches}


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__, file=sys.stderr)
        return 2
    home, source = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
    vendor = source / "codex/vendor/mattpocock"
    document = {
        "schema": "aisoft.issue-354.inventory/v1",
        "target_home": str(home),
        "source": {
            "checkout": str(source), "head": git(source, "rev-parse", "HEAD"),
            "cached_origin_main": git(source, "rev-parse", "origin/main"),
            "managed_source_dirty": bool(git(source, "status", "--porcelain", "--", "codex", "skill-for-codex",
                                             "skill-for-claude")),
            "manifests": {path.name: manifest_summary(path / "manifest.json")
                          for path in sorted(vendor.glob("v*"))},
        },
        "codex_managed": codex_managed(home, source),
        "claude": claude_side(home),
        "codex_plugin": codex_plugin(home),
    }
    json.dump(document, sys.stdout, ensure_ascii=False, indent=1, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

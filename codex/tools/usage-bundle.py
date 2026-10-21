"""Versioned platform usage bundle (#377, ADR 0001 D7).

The usage layer (projects) consumes a versioned bundle: the platform usage
contract, the project pointer and change templates, seeds and the platform
skills. usage/bundle.json declares the members and an append-only release
history; every release records the sha256 of each member as it was released.
A project pins one release in .aisoft/platform-usage.lock.json, so platform
commits after that release no longer change what the project is checked
against. Distribution needs no broker operation, Gitea release or tag: the
history table is the version, the digests prove the copy.

  --verify [--baseline-ref REF]  declaration, history and current contents agree;
                                 with REF, releases published there are an
                                 unchanged prefix of the current history
  --release VERSION --today D --compatibility patch|minor|major --notes TEXT
                                 append a release from the current contents
  --build DIR                    export the latest release for a project to copy
                                 (skills land in .claude/, .agents/ and .cursor/;
                                 vendored skill packs per VENDOR_LANDINGS)
  --adopt REPO [--tools LIST]    write the latest release into a clean project
                                 checkout (#402) and report its status; LIST picks
                                 the tool landings (default claude,codex)
  --project-status REPO          platform-pin / tool-provenance /
                                 pointer-sections / change-templates

Only --release writes inside the platform tree (usage/bundle.json); --build
writes only under DIR and --adopt only inside REPO. --project-status never
writes.

The session tool (#402): exact members checked as tool-provenance land under
.aisoft/bin and .aisoft/lib, a copy of the platform tree subset that
codex/tools/aisoft wraps. This script is one of them, so inside a project it
runs from .aisoft/lib with that directory as its platform root; --build and
--adopt write the release history it then reads (.aisoft/lib/usage/bundle.json)
and the provenance aisoft version reports (.aisoft/lib/provenance.json).
"""
from __future__ import annotations

import datetime
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys

DEFAULT_ROOT = Path(__file__).resolve().parent.parent.parent
BUNDLE_PATH = "usage/bundle.json"
BUNDLE_CONTRACT = "aisoft-usage-bundle/v1"
LOCK_CONTRACT = "aisoft-usage-lock/v1"
# Fixed by the v1 contract: moving it would turn every pinned project into an
# unpinned one without any member change or new release.
LOCK_PATH = ".aisoft/platform-usage.lock.json"
LOCK_KEYS = {"contract_version", "bundle_version", "bundle_digest"}
# Optional, written by the project itself (#409): change directories numbered
# below it are registered history. Every lock writer keeps it.
LOCK_LEGACY_KEY = "legacy_changes_before"


def lock_legacy_value(lock: object) -> int | None:
    """The project's legacy threshold, or None when absent or malformed."""
    if not isinstance(lock, dict):
        return None
    value = lock.get(LOCK_LEGACY_KEY)
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        return None
    return value
MODES = ("exact", "pointer", "seed", "skill", "vendor")
CHECKS = ("platform-pin", "tool-provenance", "pointer-sections", "change-templates")
# Every member list must cover these; tool-provenance only exists from the
# release that first ships the session tool on (#402).
REQUIRED_CHECKS = ("platform-pin", "pointer-sections", "change-templates")
COMPATIBILITY = ("patch", "minor", "major")
TOOL_HISTORY = ".aisoft/lib/usage/bundle.json"
TOOL_PROVENANCE = ".aisoft/lib/provenance.json"
TOOL_ROOTS = (".aisoft/bin/", ".aisoft/lib/")
# CI seeds are never adopted: changing a project's CI is not a small change.
ADOPT_SKIPPED_SEEDS = (".gitea/workflows/", "scripts/ci/")
LEGACY_TEMPLATES = ("00-summary.md", "01-spec.md", "02-plan.md", "03-verification.md")
# Tool landings --adopt writes; a project adopts the tools it uses. The broker
# push gate allows at most this many exact paths in one change's git_scope.
TOOL_LANDINGS = {"claude": ".claude/", "codex": ".agents/", "cursor": ".cursor/"}
DEFAULT_TOOLS = ("claude", "codex")
SCOPE_LIMIT = 256
VERSION_RE = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")
POINTER_START = "## 平台声明（常驻指针）"
POINTER_PATH = "## 每 Issue 开发路径"


class BundleError(Exception):
    pass


def usage() -> None:
    print(
        "usage: usage-bundle.sh [--platform-root DIR] --verify [--baseline-ref REF]\n"
        "       usage-bundle.sh [--platform-root DIR] --release VERSION --today YYYY-MM-DD"
        " --compatibility patch|minor|major --notes TEXT\n"
        "       usage-bundle.sh [--platform-root DIR] --build DIR\n"
        "       usage-bundle.sh [--platform-root DIR] --adopt REPO [--tools claude,codex,cursor]\n"
        "       usage-bundle.sh [--platform-root DIR] --project-status REPO",
        file=sys.stderr,
    )
    sys.exit(64)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def extract_pointer(text: str) -> str | None:
    """Same section boundary as aisoft-project-check.sh always used: from the
    platform heading through the per-Issue path section, stopping before the
    next level-two heading after it."""
    lines: list[str] = []
    in_pointer = saw_platform = saw_path = False
    # awk's default record separator is LF only: CR stays part of the line and
    # Unicode line separators are ordinary characters. str.splitlines() would
    # split on both and let content hide behind a U+2028 "line break".
    records = text.split("\n")
    if records and records[-1] == "":
        records.pop()
    for line in records:
        if line == POINTER_START:
            in_pointer = saw_platform = True
        if in_pointer:
            if line == POINTER_PATH:
                saw_path = True
            elif saw_path and line.startswith("## "):
                break
            lines.append(line)
    if not saw_platform or not saw_path:
        return None
    return "\n".join(lines) + "\n"


def pointer_digest(path: Path) -> str:
    pointer = extract_pointer(path.read_bytes().decode("utf-8"))
    if pointer is None:
        raise BundleError(f"{path}: 缺少常驻指针两节")
    return sha256_bytes(pointer.encode("utf-8"))


def canonical_member(member: dict) -> dict:
    keys = ("source", "mode", "target", "check")
    return {key: member[key] for key in keys if member.get(key) is not None}


def released_member(root: Path, member: dict) -> dict:
    """sha256 always covers every distributed byte of the source; a pointer
    member additionally records the digest of its two pointer sections, which
    is what a project's AGENTS.md is checked against."""
    source = root / member["source"]
    record = dict(canonical_member(member), sha256=sha256_bytes(source.read_bytes()))
    if member["mode"] == "pointer":
        record["pointer_sha256"] = pointer_digest(source)
    return record


def compute_bundle_digest(members: list[dict]) -> str:
    payload = [
        {key: m[key] for key in ("source", "mode", "target", "check", "sha256", "pointer_sha256") if key in m}
        for m in members
    ]
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return "sha256:" + sha256_bytes(text.encode("utf-8"))


def version_key(version: str) -> tuple[int, int, int]:
    match = VERSION_RE.match(version)
    if not match:
        raise BundleError(f"版本号不是 MAJOR.MINOR.PATCH：{version!r}")
    return tuple(int(part) for part in match.groups())  # type: ignore[return-value]


def safe_relative(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise BundleError(f"{label} 必须是非空字符串")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or str(path) != value:
        raise BundleError(f"{label} 必须是规范的相对路径：{value!r}")
    return value


def validate_member(member: object, label: str) -> dict:
    if not isinstance(member, dict):
        raise BundleError(f"{label} 必须是对象")
    allowed = {"source", "mode", "target", "check", "sha256", "pointer_sha256"}
    extra = set(member) - allowed
    if extra:
        raise BundleError(f"{label} 有未知字段：{sorted(extra)}")
    safe_relative(member.get("source"), f"{label}.source")
    mode = member.get("mode")
    if mode not in MODES:
        raise BundleError(f"{label}.mode 必须是 {MODES} 之一")
    target = member.get("target")
    check = member.get("check")
    if mode in ("skill", "vendor"):
        if target is not None or check is not None:
            raise BundleError(f"{label}: {mode} 成员没有项目落点，不能有 target 或 check")
        if mode == "vendor":
            vendor_pack(member["source"], label)
    else:
        safe_relative(target, f"{label}.target")
    if mode == "pointer" and check != "pointer-sections":
        raise BundleError(f"{label}: pointer 成员必须归入 pointer-sections")
    if check == "tool-provenance" and (mode != "exact" or not str(target).startswith(TOOL_ROOTS)):
        raise BundleError(f"{label}: tool-provenance 成员必须是 exact，落在 .aisoft/bin/ 或 .aisoft/lib/ 下")
    if mode == "exact" and check is None:
        raise BundleError(f"{label}: exact 成员必须归入一个核对项，不能被静默跳过")
    if mode == "seed" and check is not None:
        raise BundleError(f"{label}: seed 成员不核对，不能有 check")
    if check is not None and check not in CHECKS:
        raise BundleError(f"{label}.check 必须是 {CHECKS} 之一")
    return member


def validate_member_list(members: object, label: str, with_sha: bool) -> list[dict]:
    if not isinstance(members, list) or not members:
        raise BundleError(f"{label} 必须是非空数组")
    sources: set[str] = set()
    targets: set[str] = set()
    for index, member in enumerate(members):
        validate_member(member, f"{label}[{index}]")
        if member["source"] in sources:
            raise BundleError(f"{label}: source 重复 {member['source']}")
        sources.add(member["source"])
        target = member.get("target")
        if target is not None:
            if target in targets:
                raise BundleError(f"{label}: target 重复 {target}")
            targets.add(target)
        digest_keys = ["sha256"] + (["pointer_sha256"] if member["mode"] == "pointer" else [])
        if with_sha:
            for key in digest_keys:
                if not isinstance(member.get(key), str) or not re.fullmatch(r"[0-9a-f]{64}", member[key]):
                    raise BundleError(f"{label}[{index}].{key} 不是 64 位十六进制")
            if member["mode"] != "pointer" and "pointer_sha256" in member:
                raise BundleError(f"{label}[{index}] 只有 pointer 成员记录 pointer_sha256")
        elif "sha256" in member or "pointer_sha256" in member:
            raise BundleError(f"{label}[{index}] 不应记录摘要（只在 releases 里记）")
    covered = {member.get("check") for member in members}
    missing = [check for check in REQUIRED_CHECKS if check not in covered]
    if missing:
        raise BundleError(f"{label}: 缺少归入 {', '.join(missing)} 的成员，核对项不能为空")
    return members  # type: ignore[return-value]


def load_bundle(root: Path) -> dict:
    path = root / BUNDLE_PATH
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        raise BundleError(f"读不懂 {BUNDLE_PATH}：{error}") from error
    return parse_bundle(text)


def parse_bundle(text: str) -> dict:
    try:
        bundle = json.loads(text)
    except ValueError as error:
        raise BundleError(f"读不懂 {BUNDLE_PATH}：{error}") from error
    if not isinstance(bundle, dict):
        raise BundleError(f"{BUNDLE_PATH} 必须是对象")
    if set(bundle) != {"contract_version", "lock_path", "members", "releases"}:
        raise BundleError(f"{BUNDLE_PATH} 的键必须恰好是 contract_version、lock_path、members、releases")
    if bundle["contract_version"] != BUNDLE_CONTRACT:
        raise BundleError(f"contract_version 不受支持：{bundle['contract_version']!r}")
    if bundle["lock_path"] != LOCK_PATH:
        raise BundleError(f"lock_path 在 {BUNDLE_CONTRACT} 中固定为 {LOCK_PATH}")
    validate_member_list(bundle["members"], "members", with_sha=False)
    releases = bundle["releases"]
    if not isinstance(releases, list):
        raise BundleError("releases 必须是数组")
    previous: tuple[int, int, int] | None = None
    tool_shipped = False
    for index, release in enumerate(releases):
        label = f"releases[{index}]"
        base_keys = {"version", "released", "bundle_digest", "members"}
        # #402: notes and compatibility come together, from the release that
        # introduced them on; published releases before it stay byte-identical.
        if not isinstance(release, dict) or set(release) not in (base_keys, base_keys | {"notes", "compatibility"}):
            raise BundleError(f"{label} 的键必须是 version、released、bundle_digest、members（可另带 notes 与 compatibility）")
        if "compatibility" in release:
            if release["compatibility"] not in COMPATIBILITY:
                raise BundleError(f"{label}.compatibility 必须是 {'|'.join(COMPATIBILITY)}")
            if not isinstance(release["notes"], str) or not release["notes"].strip() or "\n" in release["notes"]:
                raise BundleError(f"{label}.notes 必须是一句非空说明")
        key = version_key(release["version"])
        if previous is not None and key <= previous:
            raise BundleError(f"{label}: 版本 {release['version']} 不大于上一个版本，历史只能追加")
        previous = key
        try:
            datetime.date.fromisoformat(release["released"])
        except (TypeError, ValueError) as error:
            raise BundleError(f"{label}.released 不是 YYYY-MM-DD") from error
        validate_member_list(release["members"], f"{label}.members", with_sha=True)
        # #402: once a release ships the session tool, no later release or the
        # declaration may drop it; a project would lose aisoft without a GAP.
        has_tool = any(member.get("check") == "tool-provenance" for member in release["members"])
        if tool_shipped and not has_tool:
            raise BundleError(f"{label}: 之前的版本已带会话工具，不能整项删除 tool-provenance 成员")
        tool_shipped = tool_shipped or has_tool
        if compute_bundle_digest(release["members"]) != release["bundle_digest"]:
            raise BundleError(f"{label}: bundle_digest 与记录的成员摘要不符，历史被改写")
    if tool_shipped and not any(member.get("check") == "tool-provenance" for member in bundle["members"]):
        raise BundleError("members: 已发布的版本带会话工具，不能整项删除 tool-provenance 成员")
    return bundle


def current_members(root: Path, bundle: dict) -> list[dict]:
    result = []
    for member in bundle["members"]:
        source = root / member["source"]
        if not source.is_file():
            raise BundleError(f"成员文件缺失：{member['source']}")
        if member["mode"] == "vendor":
            vendor_snapshot(root, member["source"])
        result.append(released_member(root, member))
    return result


# Vendored skill packs (#392). A vendor member's source is a snapshot's
# manifest.json: it pins every skill directory by hash, so the release digest of
# that one file covers the whole snapshot, and --verify/--build re-check the
# snapshot bytes against it. superpowers lands only in .cursor/skills: Claude and
# Codex take it from their official marketplaces, and a project-level
# .agents/skills copy would be a second source next to the Codex plugin. Matt is
# vendored on Codex anyway, so its project landing includes .agents/skills.
VENDOR_LANDINGS = {
    "mattpocock": (".agents/skills", ".cursor/skills"),
    "superpowers": (".cursor/skills",),
}
VENDOR_SOURCE_RE = re.compile(r"^codex/vendor/([a-z0-9-]+)/(v[0-9]+\.[0-9]+\.[0-9]+)/manifest\.json$")


def vendor_pack(source: str, label: str) -> str:
    match = VENDOR_SOURCE_RE.match(source)
    if not match or match.group(1) not in VENDOR_LANDINGS:
        raise BundleError(f"{label}: vendor 成员必须是 codex/vendor/<{'|'.join(VENDOR_LANDINGS)}>/<vX.Y.Z>/manifest.json")
    return match.group(1)


def vendor_snapshot(root: Path, source: str) -> list[tuple[str, PurePosixPath]]:
    """Verify the snapshot against its manifest; return (skill name, directory)."""
    pack = vendor_pack(source, source)
    sys.path.insert(0, str(DEFAULT_ROOT / "codex/runtime"))
    try:
        from aisoft_loop.matt_snapshot import SnapshotError, verify_snapshot
    finally:
        sys.path.pop(0)
    snapshot = (root / source).parent
    try:
        manifest = json.loads((root / source).read_text(encoding="utf-8"))
        verify_snapshot(snapshot, manifest, pack)
    except (OSError, ValueError, SnapshotError) as error:
        raise BundleError(f"vendor 快照与 manifest 不符：{source}：{error}") from error
    if manifest["tag"] != snapshot.name:
        raise BundleError(f"vendor 快照目录与 tag 不符：{source}")
    return [(item["name"], PurePosixPath(item["path"]).parent) for item in manifest["skills"]]


def git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)


def check_baseline(root: Path, bundle: dict, ref: str) -> None:
    """Self-consistent digests cannot stop someone from rewriting a published
    release and recomputing every hash. The anchor is the history the
    protected branch already carries: whatever releases REF published must
    reappear here unchanged, in order, before any new one."""
    if git(root, "rev-parse", "--verify", "-q", f"{ref}^{{commit}}").returncode != 0:
        raise BundleError(f"基线 {ref} 不存在，无法证明历史只追加")
    listed = git(root, "ls-tree", "--name-only", ref, "--", BUNDLE_PATH)
    if listed.returncode != 0:
        raise BundleError(f"读不出基线 {ref} 的目录树，无法证明历史只追加")
    if listed.stdout.strip() == "":
        return  # the base has no bundle yet: this change is the first release
    shown = git(root, "show", f"{ref}:{BUNDLE_PATH}")
    if shown.returncode != 0:
        raise BundleError(f"读不出基线 {ref}:{BUNDLE_PATH}")
    published = parse_bundle(shown.stdout)["releases"]
    if bundle["releases"][: len(published)] != published:
        raise BundleError(f"{ref} 已发布的版本被改写或删除，历史只能追加")


def verify(root: Path, baseline_ref: str | None = None) -> dict:
    bundle = load_bundle(root)
    if baseline_ref is not None:
        check_baseline(root, bundle, baseline_ref)
    if not bundle["releases"]:
        raise BundleError("还没有发布任何版本；运行 --release")
    latest = bundle["releases"][-1]
    members = current_members(root, bundle)
    if members != latest["members"]:
        changed = sorted(
            {m["source"] for m in members} ^ {m["source"] for m in latest["members"]}
            | {
                m["source"]
                for m in members
                for r in latest["members"]
                if m["source"] == r["source"] and m != r
            }
        )
        raise BundleError(
            f"发布包成员与最新版本 {latest['version']} 不一致：{', '.join(changed)}。"
            "改动成员的变更必须在同一次变更里运行 "
            "bash codex/tools/usage-bundle.sh --release <新版本> --today <YYYY-MM-DD> "
            "--compatibility patch|minor|major --notes <一句话>"
        )
    return bundle


def write_bundle(root: Path, bundle: dict) -> None:
    text = json.dumps(bundle, indent=2, ensure_ascii=False) + "\n"
    (root / BUNDLE_PATH).write_text(text, encoding="utf-8")


def release(root: Path, version: str, today: str, compatibility: str, notes: str) -> None:
    bundle = load_bundle(root)
    key = version_key(version)
    if compatibility not in COMPATIBILITY:
        raise BundleError(f"--compatibility 必须是 {'|'.join(COMPATIBILITY)}")
    if not notes.strip() or "\n" in notes:
        raise BundleError("--notes 必须是一句非空说明")
    try:
        datetime.date.fromisoformat(today)
    except ValueError as error:
        raise BundleError(f"--today 不是 YYYY-MM-DD：{today!r}") from error
    if bundle["releases"] and key <= version_key(bundle["releases"][-1]["version"]):
        raise BundleError(f"新版本 {version} 必须大于最新版本 {bundle['releases'][-1]['version']}")
    members = current_members(root, bundle)
    if bundle["releases"] and members == bundle["releases"][-1]["members"]:
        raise BundleError("成员内容与最新版本相同，不需要发布新版本")
    bundle["releases"].append(
        {
            "version": version,
            "released": today,
            "bundle_digest": compute_bundle_digest(members),
            "members": members,
            "notes": notes.strip(),
            "compatibility": compatibility,
        }
    )
    write_bundle(root, bundle)
    print(f"RELEASED {version} {bundle['releases'][-1]['bundle_digest']}")


def lock_text(bundle: dict, release_entry: dict, legacy_before: int | None = None) -> str:
    lock = {
        "contract_version": LOCK_CONTRACT,
        "bundle_version": release_entry["version"],
        "bundle_digest": release_entry["bundle_digest"],
    }
    if legacy_before is not None:
        lock[LOCK_LEGACY_KEY] = legacy_before
    return json.dumps(lock, indent=2, ensure_ascii=False) + "\n"


# Project-level skill landings (#379, ADR 0001 D6/D8). One source file under
# skills/<name>/ lands once per usage-layer tool. Codex reads .agents/skills;
# Claude and Cursor read the same SKILL.md format without Codex-only metadata
# (agents/). A skill reaches a tool only when skills/skills.manifest declares it
# for that provider; Cursor follows the claude declaration.
SKILL_LANDINGS = (
    ("codex", ".agents/skills", True),
    ("claude", ".claude/skills", False),
    ("claude", ".cursor/skills", False),
)


SKILL_MANIFEST = "skills/skills.manifest"


def skill_targets(root: Path) -> dict[str, set[str]]:
    path = root / SKILL_MANIFEST
    if not path.is_file():
        raise BundleError(f"缺少技能声明 {path}")
    declared: dict[str, set[str]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        fields = line.split()
        targets = set(fields[1].split(",")) if len(fields) == 2 else set()
        if len(fields) != 2 or not targets or not targets <= {"claude", "codex"} or fields[0] in declared:
            raise BundleError(f"技能声明格式错误：{line!r}")
        declared[fields[0]] = targets
    return declared


def skill_landings(source: str, targets: dict[str, set[str]]) -> list[str]:
    parts = PurePosixPath(source).parts
    if len(parts) < 3 or parts[0] != "skills":
        raise BundleError(f"skill 成员必须位于 skills/<name>/ 下：{source}")
    name, rest = parts[1], PurePosixPath(*parts[2:])
    if name not in targets:
        raise BundleError(f"skill 成员 {source} 的技能 {name} 未在 skills/skills.manifest 声明")
    landings = []
    for provider, base, keeps_metadata in SKILL_LANDINGS:
        if provider not in targets[name] or (not keeps_metadata and rest.parts[0] == "agents"):
            continue
        landings.append(f"{base}/{name}/{rest}")
    return landings


def build(root: Path, out: Path) -> None:
    bundle = verify(root)
    latest = bundle["releases"][-1]
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        raise BundleError(f"--build 目录必须不存在或为空：{out}")
    if not any(m["source"] == SKILL_MANIFEST and m["mode"] == "skill" for m in bundle["members"]):
        raise BundleError(f"{SKILL_MANIFEST} 决定技能落点，必须是 skill 成员，否则同一版本可以导出不同目录")
    targets = skill_targets(root)
    vendored: dict[str, str] = {}
    for member in bundle["members"]:
        if member["mode"] != "vendor":
            continue
        pack = vendor_pack(member["source"], member["source"])
        snapshot = (root / member["source"]).parent
        for name, directory in vendor_snapshot(root, member["source"]):
            if name in targets or name in vendored:
                raise BundleError(f"vendor 技能 {name} 与{'平台技能' if name in targets else vendored.get(name, '')}同名，落点冲突")
            vendored[name] = pack
            source_dir = snapshot / directory
            for base in VENDOR_LANDINGS[pack]:
                for path in sorted(source_dir.rglob("*")):
                    if path.is_file():
                        destination = out / "project" / base / name / path.relative_to(source_dir)
                        destination.parent.mkdir(parents=True, exist_ok=True)
                        data = path.read_bytes()
                        destination.write_bytes(data)
                        # The manifest hashes bytes, not modes: derive the mode
                        # from the bytes so one release always exports the same.
                        destination.chmod(0o755 if data.startswith(b"#!") else 0o644)
    for member in bundle["members"]:
        if member["mode"] == "vendor":
            continue
        data = (root / member["source"]).read_bytes()
        if member["source"] == SKILL_MANIFEST:
            # The declaration decides every landing below; it is a member so a
            # release digest covers it, but it has no project copy of its own.
            continue
        if member["mode"] == "skill":
            destinations = [out / "project" / landing for landing in skill_landings(member["source"], targets)]
        else:
            destinations = [out / "project" / member["target"]]
        for destination in destinations:
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
            if member.get("check") == "tool-provenance":
                # Same rule as the vendor landings: the release hashes bytes,
                # so the mode is derived from them and every export agrees.
                destination.chmod(0o755 if data.startswith(b"#!") else 0o644)
    lock_destination = out / "project" / bundle["lock_path"]
    lock_destination.parent.mkdir(parents=True, exist_ok=True)
    lock_destination.write_text(lock_text(bundle, latest), encoding="utf-8")
    if any(member.get("check") == "tool-provenance" for member in latest["members"]):
        write_tool_metadata(root, bundle, latest, out / "project")
    print(f"BUILT {latest['version']} {latest['bundle_digest']}")


def write_tool_metadata(root: Path, bundle: dict, latest: dict, project: Path) -> None:
    """The two generated files next to the session tool. The history copy lets
    a project run --project-status without the platform tree; provenance is
    what aisoft version reports. Neither is a member: both are derived from the
    release itself."""
    history = dict(bundle, releases=bundle["releases"][: bundle["releases"].index(latest) + 1])
    (project / TOOL_HISTORY).parent.mkdir(parents=True, exist_ok=True)
    (project / TOOL_HISTORY).write_text(json.dumps(history, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    head = git(root, "rev-parse", "HEAD")
    provenance = {
        "bundle_version": latest["version"],
        "bundle_digest": latest["bundle_digest"],
        "source_sha": head.stdout.strip() if head.returncode == 0 else "unknown",
    }
    (project / TOOL_PROVENANCE).write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")


def replace_pointer(existing: str, template: str) -> str:
    """Swap the two pointer sections of a project's AGENTS.md for the
    template's, keeping every other line. A file without them gets them right
    after its title line."""
    pointer = extract_pointer(template)
    if pointer is None:
        raise BundleError("AGENTS.md 模板缺少常驻指针两节")
    records = existing.split("\n")
    start = next((i for i, line in enumerate(records) if line == POINTER_START), None)
    if start is None:
        title = 1 if records and records[0].startswith("# ") else 0
        head = "\n".join(records[:title])
        tail = "\n".join(records[title:]).lstrip("\n")
        return (head + "\n\n" if head else "") + pointer + tail
    saw_path = False
    end = len(records)
    for index in range(start, len(records)):
        line = records[index]
        if line == POINTER_PATH:
            saw_path = True
        elif saw_path and line.startswith("## "):
            end = index
            break
    if not saw_path:
        raise BundleError("AGENTS.md 有平台声明节但缺少「每 Issue 开发路径」节，人工处理后再采用")
    before = "\n".join(records[:start])
    after = "\n".join(records[end:])
    return before + ("\n" if before else "") + pointer + after


def refuse_symlinks(repo: Path, relative: str) -> None:
    current = repo
    for part in PurePosixPath(relative).parts:
        current = current / part
        if current.is_symlink():
            raise BundleError(f"--adopt 拒绝经符号链接写入：{current.relative_to(repo).as_posix()}，先人工处理")
        if not current.exists():
            return


def adopt(root: Path, repo: Path, tools: tuple[str, ...] = DEFAULT_TOOLS) -> int:
    """Write the latest release into one clean project checkout, the way a
    person following project-align would copy it, and report the result."""
    unknown = sorted(set(tools) - set(TOOL_LANDINGS))
    if unknown or not tools:
        raise BundleError(f"--tools 只能取 {','.join(TOOL_LANDINGS)}：{','.join(unknown) or '空'}")
    skipped_landings = tuple(base for name, base in TOOL_LANDINGS.items() if name not in tools)
    if git(repo, "rev-parse", "--is-inside-work-tree").stdout.strip() != "true":
        raise BundleError(f"--adopt 目标不是 git 工作树：{repo}")
    if git(repo, "status", "--porcelain", "--untracked-files=all").stdout.strip():
        raise BundleError(f"--adopt 目标工作树不干净，先提交或清理：{repo}")
    bundle = verify(root)
    latest = bundle["releases"][-1]
    import shutil
    import tempfile

    with tempfile.TemporaryDirectory() as scratch:
        export = Path(scratch) / "build"
        build(root, export)
        project = export / "project"
        exported = sorted(path.relative_to(project).as_posix() for path in project.rglob("*") if path.is_file())
        seeds = {member["target"] for member in latest["members"] if member["mode"] == "seed"}
        pointer_target = next(member["target"] for member in latest["members"] if member["mode"] == "pointer")
        written: list[str] = []
        # Nothing is written through a symbolic link: a link inside the
        # checkout would redirect a copy onto another file (CLAUDE.md ->
        # AGENTS.md), one pointing outside would write outside the checkout.
        # Every destination is checked before the first write.
        for relative in exported + [f"{base}x" for base in TOOL_ROOTS]:
            if not (skipped_landings and relative.startswith(skipped_landings)) and not relative.startswith(ADOPT_SKIPPED_SEEDS):
                refuse_symlinks(repo, relative)
        for relative in exported:
            source = project / relative
            destination = repo / relative
            if skipped_landings and relative.startswith(skipped_landings):
                continue
            if relative.startswith(ADOPT_SKIPPED_SEEDS):
                print(f"NOTE\t{relative}\tCI 种子不随采用写入（改 CI 不是 small），需要时另开 Issue")
                continue
            if relative in seeds and destination.exists():
                print(f"KEPT\t{relative}\t种子已存在，保留项目版本")
                continue
            destination.parent.mkdir(parents=True, exist_ok=True)
            if relative == bundle["lock_path"] and destination.is_file():
                # A re-adoption moves the pin but keeps the project's own
                # legacy threshold (#409); dropping it would silently turn
                # registered history back into gaps.
                try:
                    legacy_before = lock_legacy_value(json.loads(destination.read_text(encoding="utf-8")))
                except ValueError:
                    legacy_before = None
                if legacy_before is not None:
                    updated = lock_text(bundle, latest, legacy_before)
                    if updated != destination.read_text(encoding="utf-8"):
                        destination.write_text(updated, encoding="utf-8")
                        written.append(relative)
                        print(f"WROTE\t{relative}\t保留 {LOCK_LEGACY_KEY}={legacy_before}")
                    continue
            if relative == pointer_target and destination.is_file():
                updated = replace_pointer(destination.read_text(encoding="utf-8"), source.read_text(encoding="utf-8"))
                if updated == destination.read_text(encoding="utf-8"):
                    continue
                destination.write_text(updated, encoding="utf-8")
                written.append(relative)
                print(f"WROTE\t{relative}\t只替换常驻指针两节")
                continue
            if destination.is_file() and destination.read_bytes() == source.read_bytes() and (
                destination.stat().st_mode & 0o777 == source.stat().st_mode & 0o777
            ):
                continue
            shutil.copy2(source, destination)
            written.append(relative)
            print(f"WROTE\t{relative}")
        # A tool file a newer release no longer ships must not linger: the
        # project would keep running a module nothing pins any more.
        for base in TOOL_ROOTS:
            directory = repo / base
            if not directory.is_dir():
                continue
            for path in sorted(directory.rglob("*")):
                relative = path.relative_to(repo).as_posix()
                if path.is_file() and relative not in exported:
                    path.unlink()
                    print(f"REMOVED\t{relative}\t不在 {latest['version']} 的会话工具里")
        # Legacy templates stay: the broker's scope gate refuses to delete a
        # non-canonical docs/changes path outside the change's own directory.
        template_dir = repo / "docs/changes/_template"
        for name in LEGACY_TEMPLATES:
            if (template_dir / name).is_file():
                print(f"NOTE\tdocs/changes/_template/{name}\tlegacy 模板保留；语义模板四件套已就位")
    if written:
        ignored = subprocess.run(
            ["git", "-C", str(repo), "check-ignore", "--no-index", "--stdin"],
            input="\n".join(written) + "\n", capture_output=True, text=True,
        )
        for relative in ignored.stdout.splitlines():
            print(f"NOTE\t{relative}\t被 .gitignore 忽略，提交前处理")
    changed = [line for line in git(repo, "status", "--porcelain", "--untracked-files=all").stdout.splitlines() if line]
    print(f"CHANGED\t{len(changed)}\t改动路径数（tools={','.join(tools)}）")
    if len(changed) > SCOPE_LIMIT - 4:
        print(f"NOTE\t{len(changed)}\t加上 change 文档后会超过 broker git_scope 的 {SCOPE_LIMIT} 项上限，减少 --tools 或拆分")
    failures = 0
    for check, result, detail in project_status(root, repo):
        print(f"{check}\t{result}\t{detail}")
        failures += result == "GAP"
    print(f"ADOPTED {latest['version']} {latest['bundle_digest']}")
    return 1 if failures else 0


def project_status(root: Path, repo: Path) -> list[tuple[str, str, str]]:
    bundle = load_bundle(root)
    if not bundle["releases"]:
        raise BundleError("平台还没有发布任何使用发布包版本")
    releases = {entry["version"]: entry for entry in bundle["releases"]}
    latest = bundle["releases"][-1]
    lines: list[tuple[str, str, str]] = []
    reference = latest
    pinned = False
    lock_path = repo / bundle["lock_path"]
    if not lock_path.is_file():
        lines.append(("platform-pin", "GAP", f"缺少 {bundle['lock_path']}，按最新版本 {latest['version']} 核对"))
    else:
        try:
            lock = json.loads(lock_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            lock = None
        if (
            not isinstance(lock, dict)
            or set(lock) - {LOCK_LEGACY_KEY} != LOCK_KEYS
            or (LOCK_LEGACY_KEY in lock and lock_legacy_value(lock) is None)
            or lock.get("contract_version") != LOCK_CONTRACT
        ):
            lines.append(("platform-pin", "GAP", f"{bundle['lock_path']} 格式不受支持，按最新版本核对"))
        elif lock["bundle_version"] not in releases:
            lines.append(("platform-pin", "GAP", f"pin 的版本 {lock['bundle_version']!r} 不在平台发布历史中"))
        elif releases[lock["bundle_version"]]["bundle_digest"] != lock["bundle_digest"]:
            lines.append(("platform-pin", "GAP", f"pin 的摘要与平台记录的 {lock['bundle_version']} 不符"))
        else:
            reference = releases[lock["bundle_version"]]
            pinned = True
    failures: dict[str, list[str]] = {check: [] for check in CHECKS}
    for member in reference["members"]:
        check = member.get("check")
        if check is None:
            continue
        target = repo / member["target"]
        if not target.is_file():
            failures[check].append(f"{member['target']} 缺失")
            continue
        try:
            if member["mode"] == "pointer":
                digest, expected = pointer_digest(target), member["pointer_sha256"]
            else:
                digest, expected = sha256_bytes(target.read_bytes()), member["sha256"]
        except (BundleError, UnicodeDecodeError):
            failures[check].append(f"{member['target']} 缺少常驻指针两节")
            continue
        if digest != expected:
            failures[check].append(f"{member['target']} 与 {reference['version']} 不一致")
    if pinned:
        behind = bundle["releases"][bundle["releases"].index(reference) + 1 :]
        levels = [entry.get("compatibility", "unknown") for entry in behind]
        if failures["platform-pin"]:
            lines.append(("platform-pin", "GAP", "；".join(failures["platform-pin"])))
        elif "major" in levels:
            majors = ", ".join(entry["version"] for entry in behind if entry.get("compatibility") == "major")
            lines.append(("platform-pin", "GAP", f"已 pin {reference['version']}，落后区间含 major（{majors}），需要升级到 {latest['version']}"))
        else:
            lines.append(("platform-pin", "PASS", f"pin {reference['version']}"))
            if behind:
                highest = next((level for level in ("minor", "patch", "unknown") if level in levels), "unknown")
                lines.append((
                    "platform-pin", "NOTE",
                    f"已 pin {reference['version']}，平台最新版本 {latest['version']}，落后区间最高兼容级别 {highest}",
                ))
    lines.extend(tool_provenance(repo, bundle, reference, failures["tool-provenance"]))
    for check in ("pointer-sections", "change-templates"):
        if failures[check]:
            lines.append((check, "GAP", "；".join(failures[check])))
        else:
            lines.append((check, "PASS", reference["version"]))
    return lines


def tool_provenance(repo: Path, bundle: dict, reference: dict, failures: list[str]) -> list[tuple[str, str, str]]:
    """The session tool's bytes are the reference release's (#402). Releases
    before the tool existed have nothing to compare, which is a NOTE: those
    projects run platform tools from a platform checkout, as they always did."""
    if not any(member.get("check") == "tool-provenance" for member in reference["members"]):
        return [("tool-provenance", "NOTE", f"{reference['version']} 早于会话工具，项目内没有 aisoft")]
    # A project without the tool is missing every file; name a few, count the rest.
    problems = failures[:3] + ([f"另有 {len(failures) - 3} 个文件同样不符"] if len(failures) > 3 else [])
    history_path = repo / TOOL_HISTORY
    try:
        history = parse_bundle(history_path.read_text(encoding="utf-8"))["releases"]
    except (OSError, BundleError) as error:
        problems.append(f"{TOOL_HISTORY} 不可读：{error}")
    else:
        prefix = bundle["releases"][: bundle["releases"].index(reference) + 1]
        if history != prefix:
            problems.append(f"{TOOL_HISTORY} 与平台到 {reference['version']} 为止的发布历史不一致")
    try:
        provenance = json.loads((repo / TOOL_PROVENANCE).read_text(encoding="utf-8"))
        if (provenance.get("bundle_version"), provenance.get("bundle_digest")) != (
            reference["version"], reference["bundle_digest"]
        ):
            problems.append(f"{TOOL_PROVENANCE} 的版本与 {reference['version']} 不符")
    except (OSError, ValueError, AttributeError):
        problems.append(f"{TOOL_PROVENANCE} 不可读")
    if problems:
        return [("tool-provenance", "GAP", "；".join(problems))]
    return [("tool-provenance", "PASS", reference["version"])]


def main(argv: list[str]) -> int:
    root = DEFAULT_ROOT
    args = list(argv)
    if len(args) >= 2 and args[0] == "--platform-root":
        root = Path(args[1]).resolve()
        args = args[2:]
    try:
        if args == ["--verify"] or (len(args) == 3 and args[:2] == ["--verify", "--baseline-ref"]):
            bundle = verify(root, args[2] if len(args) == 3 else None)
            latest = bundle["releases"][-1]
            print(f"VERIFIED {latest['version']} {latest['bundle_digest']}")
        elif len(args) >= 2 and args[0] == "--release":
            if len(args) != 8 or args[2] != "--today" or args[4] != "--compatibility" or args[6] != "--notes":
                raise BundleError("--release 必须写成 --release VERSION --today D --compatibility patch|minor|major --notes TEXT（#402 起每个版本都带说明与兼容级别）")
            release(root, args[1], args[3], args[5], args[7])
        elif args[:1] == ["--adopt"] and len(args) in (2, 4) and (len(args) == 2 or args[2] == "--tools"):
            repo = Path(args[1]).resolve()
            if not repo.is_dir():
                usage()
            tools = tuple(args[3].split(",")) if len(args) == 4 else DEFAULT_TOOLS
            return adopt(root, repo, tools)
        elif len(args) == 2 and args[0] == "--build":
            build(root, Path(args[1]))
        elif len(args) == 2 and args[0] == "--project-status":
            repo = Path(args[1])
            if not repo.is_dir():
                usage()
            for check, result, detail in project_status(root, repo):
                print(f"{check}\t{result}\t{detail}")
        else:
            usage()
    except BundleError as error:
        print(f"usage-bundle: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")
    sys.exit(main(sys.argv[1:]))

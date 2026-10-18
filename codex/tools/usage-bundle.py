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
  --release VERSION --today D    append a release from the current contents
  --build DIR                    export the latest release for a project to copy
                                 (skills land in .claude/, .agents/ and .cursor/)
  --project-status REPO          platform-pin / pointer-sections / change-templates

Only --release writes inside the platform tree (usage/bundle.json); --build
writes only under DIR. --project-status never writes.
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
MODES = ("exact", "pointer", "seed", "skill")
CHECKS = ("platform-pin", "pointer-sections", "change-templates")
VERSION_RE = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")
POINTER_START = "## 平台声明（常驻指针）"
POINTER_PATH = "## 每 Issue 开发路径"


class BundleError(Exception):
    pass


def usage() -> None:
    print(
        "usage: usage-bundle.sh [--platform-root DIR] --verify [--baseline-ref REF]\n"
        "       usage-bundle.sh [--platform-root DIR] --release VERSION --today YYYY-MM-DD\n"
        "       usage-bundle.sh [--platform-root DIR] --build DIR\n"
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
    if mode == "skill":
        if target is not None or check is not None:
            raise BundleError(f"{label}: skill 成员没有项目落点，不能有 target 或 check")
    else:
        safe_relative(target, f"{label}.target")
    if mode == "pointer" and check != "pointer-sections":
        raise BundleError(f"{label}: pointer 成员必须归入 pointer-sections")
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
    missing = [check for check in CHECKS if check not in covered]
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
    for index, release in enumerate(releases):
        label = f"releases[{index}]"
        if not isinstance(release, dict) or set(release) != {"version", "released", "bundle_digest", "members"}:
            raise BundleError(f"{label} 的键必须恰好是 version、released、bundle_digest、members")
        key = version_key(release["version"])
        if previous is not None and key <= previous:
            raise BundleError(f"{label}: 版本 {release['version']} 不大于上一个版本，历史只能追加")
        previous = key
        try:
            datetime.date.fromisoformat(release["released"])
        except (TypeError, ValueError) as error:
            raise BundleError(f"{label}.released 不是 YYYY-MM-DD") from error
        validate_member_list(release["members"], f"{label}.members", with_sha=True)
        if compute_bundle_digest(release["members"]) != release["bundle_digest"]:
            raise BundleError(f"{label}: bundle_digest 与记录的成员摘要不符，历史被改写")
    return bundle


def current_members(root: Path, bundle: dict) -> list[dict]:
    result = []
    for member in bundle["members"]:
        source = root / member["source"]
        if not source.is_file():
            raise BundleError(f"成员文件缺失：{member['source']}")
        result.append(released_member(root, member))
    return result


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
            "bash codex/tools/usage-bundle.sh --release <新版本> --today <YYYY-MM-DD>"
        )
    return bundle


def write_bundle(root: Path, bundle: dict) -> None:
    text = json.dumps(bundle, indent=2, ensure_ascii=False) + "\n"
    (root / BUNDLE_PATH).write_text(text, encoding="utf-8")


def release(root: Path, version: str, today: str) -> None:
    bundle = load_bundle(root)
    key = version_key(version)
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
        }
    )
    write_bundle(root, bundle)
    print(f"RELEASED {version} {bundle['releases'][-1]['bundle_digest']}")


def lock_text(bundle: dict, release_entry: dict) -> str:
    lock = {
        "contract_version": LOCK_CONTRACT,
        "bundle_version": release_entry["version"],
        "bundle_digest": release_entry["bundle_digest"],
    }
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


def skill_targets(root: Path) -> dict[str, set[str]]:
    path = root / "skills/skills.manifest"
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
    targets = skill_targets(root)
    for member in bundle["members"]:
        data = (root / member["source"]).read_bytes()
        if member["mode"] == "skill":
            destinations = [out / "project" / landing for landing in skill_landings(member["source"], targets)]
        else:
            destinations = [out / "project" / member["target"]]
        for destination in destinations:
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
    lock_destination = out / "project" / bundle["lock_path"]
    lock_destination.parent.mkdir(parents=True, exist_ok=True)
    lock_destination.write_text(lock_text(bundle, latest), encoding="utf-8")
    print(f"BUILT {latest['version']} {latest['bundle_digest']}")


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
            or set(lock) != {"contract_version", "bundle_version", "bundle_digest"}
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
        if failures["platform-pin"]:
            lines.append(("platform-pin", "GAP", "；".join(failures["platform-pin"])))
        else:
            lines.append(("platform-pin", "PASS", f"pin {reference['version']}"))
            if reference is not latest:
                lines.append(("platform-pin", "NOTE", f"已 pin {reference['version']}，平台最新版本 {latest['version']}"))
    for check in ("pointer-sections", "change-templates"):
        if failures[check]:
            lines.append((check, "GAP", "；".join(failures[check])))
        else:
            lines.append((check, "PASS", reference["version"]))
    return lines


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
        elif len(args) == 4 and args[0] == "--release" and args[2] == "--today":
            release(root, args[1], args[3])
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

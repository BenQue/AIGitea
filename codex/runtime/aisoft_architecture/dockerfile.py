"""Offline, fail-closed Dockerfile FROM checks for declared source inputs.

This deliberately supports a conservative Dockerfile subset. It neither
expands ARG nor loads frontends; results are not builder provenance.
"""

from __future__ import annotations

import errno
import os
from pathlib import Path
import re
import stat
from typing import Any

from .errors import fail


MAX_BYTES = 1024 * 1024
INSTRUCTIONS = frozenset({
    "ADD", "ARG", "CMD", "COPY", "ENTRYPOINT", "ENV", "EXPOSE", "FROM",
    "HEALTHCHECK", "LABEL", "MAINTAINER", "ONBUILD", "RUN", "SHELL",
    "STOPSIGNAL", "USER", "VOLUME", "WORKDIR",
})
DIRECTIVE = re.compile(r"^#\s*(syntax|escape|check)\s*=\s*(.*?)\s*$", re.I)
STABLE_FRONTEND = re.compile(r"docker/dockerfile:1(?:\.[0-9]+){0,2}")
STAGE = re.compile(r"[A-Za-z][A-Za-z0-9_.-]*")
NAME_COMPONENT = r"[a-z0-9]+(?:(?:[._]|__|-+)[a-z0-9]+)*"
HOST_COMPONENT = r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?"
REGISTRY = rf"{HOST_COMPONENT}(?:\.{HOST_COMPONENT})*(?::[0-9]+)?"
IMAGE = re.compile(
    rf"(?:{REGISTRY}/)?{NAME_COMPONENT}(?:/{NAME_COMPONENT})*"
    r":[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}@(sha256:[0-9a-f]{64})"
)


def validate_paths(project: dict[str, Any]) -> None:
    """Give unsafe Dockerfile paths a stable diagnostic before schema regexes."""
    if "dockerfiles" not in project:
        return
    paths = project["dockerfiles"]
    if not isinstance(paths, list) or not paths:
        fail("DOCKERFILE_PATH_INVALID", "dockerfiles 必须为非空路径数组。", "$.dockerfiles")
    seen = set()
    for index, value in enumerate(paths):
        field = f"$.dockerfiles[{index}]"
        if not isinstance(value, str) or not value or value.startswith("/"):
            fail("DOCKERFILE_PATH_INVALID", "必须声明根内相对 POSIX 文件路径。", field)
        segments = value.split("/")
        if ("\\" in value or any(ord(char) < 32 or ord(char) == 127 for char in value)
                or any(segment in {"", ".", ".."} for segment in segments)
                or value in seen):
            fail("DOCKERFILE_PATH_INVALID", "路径有非法片段或重复项。", field)
        # Source inputs must not be credential files, even when explicitly listed.
        if any(segment.lower() in {".git", ".aws", ".ssh", ".runner", "auth.json", ".git-credentials", "credentials"}
               or segment.lower().startswith(".env") for segment in segments):
            fail("DOCKERFILE_PATH_INVALID", "凭据路径不能作为 Dockerfile 输入。", field)
        seen.add(value)


def _read(root: Path, relative: str, field: str) -> str:
    """Open each relative segment without following links, including races.

    dir_fd keeps replacement of a parent directory from redirecting the read.
    O_NONBLOCK prevents a named pipe from blocking before fstat rejects it.
    """
    directory = None
    source = None
    try:
        directory = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        segments = relative.split("/")
        for segment in segments[:-1]:
            metadata = os.stat(segment, dir_fd=directory, follow_symlinks=False)
            if stat.S_ISLNK(metadata.st_mode):
                fail("DOCKERFILE_PATH_INVALID", "Dockerfile 路径链不能含 symlink。", field)
            child = os.open(segment, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory)
            os.close(directory)
            directory = child
        metadata = os.stat(segments[-1], dir_fd=directory, follow_symlinks=False)
        if stat.S_ISLNK(metadata.st_mode):
            fail("DOCKERFILE_PATH_INVALID", "Dockerfile 不能为 symlink。", field)
        if (not stat.S_ISREG(metadata.st_mode) or not metadata.st_mode & 0o444
                or metadata.st_size > MAX_BYTES):
            fail("DOCKERFILE_READ_FAILED", "Dockerfile 必须为可读且不超过 1 MiB 的普通 UTF-8 文件。", field)
        source = os.open(segments[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
        metadata = os.fstat(source)
        if not stat.S_ISREG(metadata.st_mode) or not metadata.st_mode & 0o444 or metadata.st_size > MAX_BYTES:
            fail("DOCKERFILE_READ_FAILED", "Dockerfile 不是可核验的普通文件。", field)
        with os.fdopen(source, "rb") as stream:
            source = None
            data = stream.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            fail("DOCKERFILE_READ_FAILED", "Dockerfile 超过 1 MiB。", field)
        return data.decode("utf-8")
    except OSError as exc:
        code = "DOCKERFILE_PATH_INVALID" if exc.errno == errno.ELOOP else "DOCKERFILE_READ_FAILED"
        fail(code, "Dockerfile 路径或文件不可读取；未输出系统异常。", field)
    except UnicodeError:
        fail("DOCKERFILE_READ_FAILED", "Dockerfile 必须为 UTF-8。", field)
    finally:
        if source is not None:
            os.close(source)
        if directory is not None:
            os.close(directory)


def _instructions(content: str, field: str) -> list[tuple[int, str, str]]:
    escape = "\\"
    header = True
    directives = set()
    pending = ""
    start = 0
    result = []
    # split only physical LF: Unicode line separators must not invent FROM lines.
    for number, physical in enumerate(content.split("\n"), 1):
        line = physical.removesuffix("\r").strip(" \t")
        location = f"{field}:line[{number}]"
        directive = DIRECTIVE.fullmatch(line) if header else None
        if directive:
            key, value = directive.groups()
            key = key.lower()
            if key in directives or key == "check":
                fail("DOCKERFILE_SYNTAX_UNSUPPORTED", "重复或不支持的 parser directive。", location)
            directives.add(key)
            if key == "escape":
                if value not in {"\\", "`"}:
                    fail("DOCKERFILE_SYNTAX_UNSUPPORTED", "不支持的 escape directive。", location)
                escape = value
            elif not STABLE_FRONTEND.fullmatch(value):
                fail("DOCKERFILE_SYNTAX_UNSUPPORTED", "仅支持标准稳定 Dockerfile frontend。", location)
            continue
        header = False  # a blank, ordinary comment or instruction ends directives
        if not line or line.startswith("#"):
            continue
        if not pending:
            start = number
        continued = line.endswith(escape)
        pending += line[:-1] if continued else line
        if continued:
            continue
        location = f"{field}:line[{start}]"
        parsed = re.fullmatch(r"([A-Za-z]+)(?:[ \t]+(.*))?", pending)
        if not parsed or parsed[1].upper() not in INSTRUCTIONS or "<<" in pending or "\x00" in pending:
            fail("DOCKERFILE_SYNTAX_UNSUPPORTED", "指令结构不在静态核验支持范围内。", location)
        instruction, arguments = parsed[1].upper(), parsed[2] or ""
        if instruction == "ONBUILD" and re.match(r"\s*FROM(?:\s|$)", arguments, re.I):
            fail("DOCKERFILE_FROM_INVALID", "ONBUILD 不允许 FROM。", location)
        result.append((start, instruction, arguments))
        pending = ""
    if pending:
        fail("DOCKERFILE_SYNTAX_UNSUPPORTED", "未完成的续行。", f"{field}:line[{start}]")
    return result


def _digests(content: str, field: str, declared: set[str]) -> set[str]:
    instructions = _instructions(content, field)
    froms = [(number, args) for number, instruction, args in instructions if instruction == "FROM"]
    if not froms:
        fail("DOCKERFILE_FROM_REQUIRED", "每份 Dockerfile 至少需要一个 FROM。", field)
    stages = set()
    referenced = set()
    named_stages = {
        tokens[-1].lower() for _, arguments in froms
        if len(tokens := arguments.split()) >= 3 and tokens[-2].lower() == "as"
    }
    for number, arguments in froms:
        location = f"{field}:line[{number}]"
        tokens = arguments.split()
        if tokens and tokens[0].startswith("--platform=") and len(tokens[0]) > len("--platform="):
            tokens = tokens[1:]
        if len(tokens) not in {1, 3} or (len(tokens) == 3 and tokens[1].lower() != "as") or tokens[0].startswith("--"):
            fail("DOCKERFILE_FROM_INVALID", "FROM 参数结构无效。", location)
        image = tokens[0]
        alias = tokens[2].lower() if len(tokens) == 3 else None
        if alias is not None and (not STAGE.fullmatch(alias) or alias in stages):
            fail("DOCKERFILE_FROM_INVALID", "Stage 名称无效或重复。", location)
        if "$" in image:
            fail("DOCKERFILE_FROM_VARIABLE_UNSUPPORTED", "镜像 token 必须为字面量 tag 与 digest。", location)
        if image.lower() not in stages and image != "scratch":
            if image.isdecimal() or image.lower() in named_stages:
                fail("DOCKERFILE_FROM_INVALID", "不能核验前向、自引用或数字 stage 引用。", location)
            match = IMAGE.fullmatch(image)
            if match is None:
                fail("DOCKERFILE_DIGEST_REQUIRED", "外部 FROM 必须固定 tag 与 lowercase sha256 digest。", location)
            digest = match[1]
            if digest not in declared:
                fail("DOCKERFILE_DIGEST_MISMATCH", "FROM digest 不属于声明的 OCI digest 集合。", location)
            referenced.add(digest)
        if alias is not None:
            stages.add(alias)
    return referenced


def validate_dockerfiles(project: dict[str, Any], components: dict[str, dict[str, Any]], repo_root: Path | str | None) -> None:
    """Called only after catalog/profile/project semantic checks succeed."""
    from .validator import CONTAINER_DELIVERY_CONTRACTS

    if project["delivery_contract"] not in CONTAINER_DELIVERY_CONTRACTS:
        if "dockerfiles" in project:
            fail("DOCKERFILE_DECLARATION_FORBIDDEN", "非容器交付不得声明 dockerfiles。", "$.dockerfiles")
        return
    if "dockerfiles" not in project:
        fail("DOCKERFILE_DECLARATION_REQUIRED", "容器交付必须声明全部 Dockerfile。", "$.dockerfiles")
    if repo_root is None:
        fail("DOCKERFILE_ROOT_REQUIRED", "容器核验需要明确的仓库根。", "--repo-root")
    try:
        root = Path(repo_root).resolve(strict=True)
        if not root.is_dir():
            fail("DOCKERFILE_ROOT_REQUIRED", "仓库根必须为已有目录。", "--repo-root")
    except (OSError, RuntimeError, ValueError):
        fail("DOCKERFILE_ROOT_REQUIRED", "仓库根无法确定。", "--repo-root")
    declared = {
        item["digest"] for item in project["components"]
        if components[item["component_id"]]["category"] == "oci-image"
    }
    referenced: set[str] = set()
    for index, relative in enumerate(project["dockerfiles"]):
        field = f"$.dockerfiles[{index}]"
        referenced.update(_digests(_read(root, relative, field), field, declared))
    if declared - referenced:
        fail("DOCKERFILE_BASE_IMAGE_UNUSED", "声明的 OCI digest 未全部被外部 FROM 引用。", "$.components")

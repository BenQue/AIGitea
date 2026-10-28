"""从 governance manifest 解析项目的交付阶段。

manifest 是唯一事实来源：Loop 只有 GITEA_REPO，按仓库名查表即可。
读不到 manifest、查不到仓库、或取值非法时一律回落到 "production"——
缺省取更严的一档，保证任何不确定都不会意外放宽文档要求。
"""

from __future__ import annotations

import json
import os
from pathlib import Path

PRODUCTION = "production"
DEVELOPMENT = "development"
PHASES = frozenset({DEVELOPMENT, PRODUCTION})

DEFAULT_MANIFEST = Path("/usr/local/share/aisoft/gitea-governance.json")
MANIFEST_ENV = "AISOFT_GOVERNANCE_MANIFEST"


def manifest_path() -> Path:
    override = os.environ.get(MANIFEST_ENV)
    return Path(override) if override else DEFAULT_MANIFEST


def resolve_change_control(repository: str, *, manifest: Path | str | None = None) -> str:
    """返回 repository 的交付阶段；任何不确定都回落到 production。"""
    path = Path(manifest) if manifest is not None else manifest_path()
    try:
        raw = json.loads(path.read_text())
    except (OSError, ValueError):
        return PRODUCTION
    entries = raw.get("repositories")
    if not isinstance(entries, list):
        return PRODUCTION
    for entry in entries:
        if not isinstance(entry, dict) or entry.get("name") != repository:
            continue
        phase = entry.get("change_control", PRODUCTION)
        return phase if phase in PHASES else PRODUCTION
    return PRODUCTION


PROJECT_DECLARATION = ".aisoft/project.json"


def declared_change_control(repo: Path | str, repository: str) -> str | None:
    """项目自声明来源（#434）：检出里有 .aisoft/project.json 时以它为准。

    没有这个文件时返回 None，调用方照旧查 governance manifest。文件存在但读不出、
    声明的是别的仓库、或取值越界时直接报错：这些都是项目侧的合同错误，回落到
    production 会把一个明确的声明悄悄换成另一个答案。
    """
    from .contract import ContractError

    path = Path(repo) / PROJECT_DECLARATION
    if not path.is_file():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ContractError(f"{PROJECT_DECLARATION} is not readable JSON") from exc
    if not isinstance(raw, dict) or raw.get("repository") != repository:
        raise ContractError(f"{PROJECT_DECLARATION} does not declare {repository}")
    phase = raw.get("change_control", PRODUCTION)
    if phase not in PHASES:
        raise ContractError(f"{PROJECT_DECLARATION} change_control is out of range")
    return phase

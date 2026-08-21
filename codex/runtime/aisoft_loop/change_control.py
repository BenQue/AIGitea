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

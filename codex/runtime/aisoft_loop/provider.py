"""Structured provider boundary shared by Codex and future Claude adapters."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import tempfile
from typing import Mapping

from .verifier import redact


class ProviderError(RuntimeError):
    """Provider invocation or output violated the controller contract."""


PROVIDER_STATUSES = frozenset(
    {"CONTINUE", "COMPLETE", "NEEDS_HUMAN_DECISION", "BLOCKED_EXTERNAL"}
)


@dataclass(frozen=True)
class ProviderResult:
    status: str
    summary: str
    changed_files: tuple[str, ...]
    root_cause: str
    escalation: str

    def __post_init__(self) -> None:
        if self.status not in PROVIDER_STATUSES:
            raise ProviderError(f"unsupported provider status: {self.status!r}")
        if not self.summary.strip():
            raise ProviderError("provider summary must not be empty")
        if len(set(self.changed_files)) != len(self.changed_files):
            raise ProviderError("provider changed_files must not contain duplicates")
        for path in self.changed_files:
            _validate_changed_path(path)
        if self.status in {"NEEDS_HUMAN_DECISION", "BLOCKED_EXTERNAL"} and not self.escalation.strip():
            raise ProviderError(f"{self.status} requires an escalation explanation")

    @classmethod
    def from_json(cls, text: str) -> "ProviderResult":
        try:
            raw = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ProviderError("provider output is not valid JSON") from exc
        expected = {"status", "summary", "changed_files", "root_cause", "escalation"}
        if not isinstance(raw, dict) or set(raw) != expected:
            raise ProviderError("provider output must contain the exact result schema")
        changed = raw["changed_files"]
        if not isinstance(changed, list) or not all(isinstance(item, str) for item in changed):
            raise ProviderError("provider changed_files must be a string array")
        for field in ("status", "summary", "root_cause", "escalation"):
            if not isinstance(raw[field], str):
                raise ProviderError(f"provider field {field} must be a string")
        return cls(
            status=raw["status"],
            summary=raw["summary"],
            changed_files=tuple(changed),
            root_cause=raw["root_cause"],
            escalation=raw["escalation"],
        )


class CommandProvider:
    """Invoke one provider adapter process with private request/result files."""

    def __init__(self, command: tuple[str, ...], timeout_seconds: int = 2700) -> None:
        if not command or not all(isinstance(item, str) and item for item in command):
            raise ProviderError("provider command must be a non-empty argv tuple")
        if timeout_seconds <= 0 or timeout_seconds > 7200:
            raise ProviderError("provider timeout must be in (0, 7200]")
        self.command = command
        self.timeout_seconds = timeout_seconds

    def run(self, request: Mapping[str, object], worktree: Path) -> ProviderResult:
        environment = {
            name: os.environ[name]
            for name in ("PATH", "HOME", "TMPDIR", "LANG", "LC_ALL", "CODEX_MODEL", "CLAUDE_MODEL")
            if name in os.environ
        }
        with tempfile.TemporaryDirectory(prefix="aisoft-provider-") as tempdir:
            request_path = Path(tempdir) / "request.json"
            result_path = Path(tempdir) / "result.json"
            request_path.write_text(
                json.dumps(dict(request), ensure_ascii=False, sort_keys=True),
                encoding="utf-8",
            )
            os.chmod(request_path, 0o600)
            try:
                completed = subprocess.run(
                    self.command + (str(request_path), str(result_path), str(worktree)),
                    cwd=worktree,
                    env=environment,
                    shell=False,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=self.timeout_seconds,
                    check=False,
                )
            except subprocess.TimeoutExpired as exc:
                raise ProviderError("provider exceeded its configured timeout") from exc
            if completed.returncode != 0:
                detail = redact(completed.stderr or completed.stdout)[-4000:]
                raise ProviderError(f"provider process failed: {detail}")
            try:
                result_text = result_path.read_text(encoding="utf-8")
            except (OSError, UnicodeError) as exc:
                raise ProviderError("provider did not write a readable result file") from exc
            return ProviderResult.from_json(result_text)


def _validate_changed_path(path: str) -> None:
    pure = PurePosixPath(path)
    if (
        not path
        or pure.is_absolute()
        or ".." in pure.parts
        or "." in pure.parts
        or ".git" in pure.parts
        or pure.name == "AGENTS.md"
    ):
        raise ProviderError(f"provider reported forbidden changed path: {path!r}")

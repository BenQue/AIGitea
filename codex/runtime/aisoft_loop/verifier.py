"""Deterministic, shell-free verification independent from model claims."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
import subprocess
from typing import Optional


MAX_OUTPUT_BYTES = 64 * 1024
INHERITED_ENV = frozenset(
    {"PATH", "HOME", "TMPDIR", "TMP", "TEMP", "LANG", "LC_ALL", "CI", "NODE_ENV"}
)


class VerificationConfigError(ValueError):
    """The versioned verification command contract is unsafe or invalid."""


@dataclass(frozen=True)
class VerificationCommand:
    name: str
    argv: tuple[str, ...]
    timeout_seconds: float
    required: bool


@dataclass(frozen=True)
class VerificationResult:
    name: str
    exit_code: Optional[int]
    timed_out: bool
    required: bool
    stdout: str
    stderr: str

    @property
    def passed(self) -> bool:
        return not self.timed_out and self.exit_code == 0


@dataclass(frozen=True)
class VerificationReport:
    results: tuple[VerificationResult, ...]

    @property
    def passed(self) -> bool:
        return all(result.passed or not result.required for result in self.results)

    @property
    def failed_required(self) -> tuple[VerificationResult, ...]:
        return tuple(
            result for result in self.results if result.required and not result.passed
        )


class Verifier:
    def __init__(self, repo: Path, commands: tuple[VerificationCommand, ...]) -> None:
        self.repo = repo.resolve()
        self.commands = commands

    @classmethod
    def from_file(
        cls,
        repo: Path | str,
        config_path: Path | str = Path(".gitea/loop-verification.json"),
    ) -> "Verifier":
        repo_path = Path(repo).resolve()
        supplied = Path(config_path)
        target = supplied.resolve() if supplied.is_absolute() else (repo_path / supplied).resolve()
        if not target.is_relative_to(repo_path):
            raise VerificationConfigError("verification config must stay inside repository")
        try:
            raw = json.loads(target.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise VerificationConfigError(f"verification config is missing: {target}") from exc
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise VerificationConfigError("verification config is unreadable or invalid JSON") from exc
        return cls(repo_path, _parse_config(raw))

    def run_all(self) -> VerificationReport:
        environment = {name: os.environ[name] for name in INHERITED_ENV if name in os.environ}
        environment.setdefault("CI", "true")
        results: list[VerificationResult] = []
        for command in self.commands:
            try:
                completed = subprocess.run(
                    command.argv,
                    cwd=self.repo,
                    env=environment,
                    shell=False,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=command.timeout_seconds,
                    check=False,
                )
                result = VerificationResult(
                    name=command.name,
                    exit_code=completed.returncode,
                    timed_out=False,
                    required=command.required,
                    stdout=_bounded(redact(completed.stdout)),
                    stderr=_bounded(redact(completed.stderr)),
                )
            except subprocess.TimeoutExpired as exc:
                result = VerificationResult(
                    name=command.name,
                    exit_code=None,
                    timed_out=True,
                    required=command.required,
                    stdout=_bounded(redact(_timeout_text(exc.stdout))),
                    stderr=_bounded(redact(_timeout_text(exc.stderr))),
                )
            except FileNotFoundError:
                result = VerificationResult(
                    name=command.name,
                    exit_code=127,
                    timed_out=False,
                    required=command.required,
                    stdout="",
                    stderr=f"command not found: {command.argv[0]}\n",
                )
            results.append(result)
        return VerificationReport(tuple(results))


def redact(text: str) -> str:
    cleaned = re.sub(
        r"(?im)^(Authorization\s*:\s*(?:token|bearer)\s+)\S+",
        r"\1[REDACTED]",
        text,
    )
    cleaned = re.sub(
        r"(?im)^([A-Z0-9_]*(?:TOKEN|PASSWORD|SECRET|API_KEY|PRIVATE_KEY|CREDENTIAL)"
        r"[A-Z0-9_]*\s*=\s*)\S+",
        r"\1[REDACTED]",
        cleaned,
    )
    return cleaned


def _parse_config(raw: object) -> tuple[VerificationCommand, ...]:
    if not isinstance(raw, dict):
        raise VerificationConfigError("verification config root must be an object")
    if set(raw) != {"version", "commands"}:
        raise VerificationConfigError("verification config has unknown or missing fields")
    if raw["version"] != 1:
        raise VerificationConfigError("verification config version must be 1")
    commands_raw = raw["commands"]
    if not isinstance(commands_raw, list) or not commands_raw:
        raise VerificationConfigError("verification commands must be a non-empty array")

    commands: list[VerificationCommand] = []
    names: set[str] = set()
    expected_fields = {"name", "argv", "timeout_seconds", "required"}
    for index, item in enumerate(commands_raw):
        if not isinstance(item, dict):
            raise VerificationConfigError(f"command {index} must be an object")
        if set(item) != expected_fields:
            raise VerificationConfigError(f"command {index} has unknown fields or omissions")
        name = item["name"]
        argv = item["argv"]
        timeout = item["timeout_seconds"]
        required = item["required"]
        if not isinstance(name, str) or not re.fullmatch(r"[a-z0-9][a-z0-9._-]*", name):
            raise VerificationConfigError(f"command {index} has invalid name")
        if name in names:
            raise VerificationConfigError(f"duplicate verification command name: {name}")
        names.add(name)
        if (
            not isinstance(argv, list)
            or not argv
            or not all(isinstance(arg, str) and arg and "\0" not in arg for arg in argv)
        ):
            raise VerificationConfigError(f"command {name} argv must be a non-empty string array")
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not 0 < timeout <= 7200:
            raise VerificationConfigError(f"command {name} timeout must be in (0, 7200]")
        if not isinstance(required, bool):
            raise VerificationConfigError(f"command {name} required must be boolean")
        commands.append(
            VerificationCommand(name, tuple(argv), float(timeout), required)
        )
    return tuple(commands)


def _bounded(text: str) -> str:
    encoded = text.encode("utf-8")
    if len(encoded) <= MAX_OUTPUT_BYTES:
        return text
    clipped = encoded[:MAX_OUTPUT_BYTES].decode("utf-8", errors="ignore")
    return clipped + "\n[output truncated]\n"


def _timeout_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)

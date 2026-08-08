from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from .contract import ContractError, load_contract


SECTION_RE = re.compile(r"^\s*\[([^]]+)]\s*(?:[;#].*)?$")
KEY_RE = re.compile(r"^\s*([A-Za-z0-9_.-]+)\s*=.*$")
TARGETS = {
    "service": ("DISABLE_REGISTRATION", "REQUIRE_SIGNIN_VIEW"),
    "repository": ("DEFAULT_PRIVATE", "FORCE_PRIVATE"),
}
DEFAULTS = {
    ("service", "DISABLE_REGISTRATION"): "false",
    ("service", "REQUIRE_SIGNIN_VIEW"): "false",
    ("repository", "DEFAULT_PRIVATE"): "last",
    ("repository", "FORCE_PRIVATE"): "false",
}


def _read_lines(path: Path) -> list[str]:
    try:
        return path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError) as exc:
        raise ContractError(f"cannot read Gitea config: {exc}") from exc


def _parse_values(lines: list[str]) -> dict[tuple[str, str], str]:
    section = ""
    values: dict[tuple[str, str], str] = {}
    for line in lines:
        section_match = SECTION_RE.match(line)
        if section_match:
            section = section_match.group(1).strip().lower()
            continue
        key_match = KEY_RE.match(line)
        if not key_match or section not in TARGETS:
            continue
        key = key_match.group(1).upper()
        if key not in TARGETS[section]:
            continue
        target = (section, key)
        if target in values:
            raise ContractError(f"duplicate Gitea config key: {section}.{key}")
        raw_value = line.split("=", 1)[1].strip()
        # Target values are booleans or a single visibility word. Strip only
        # comments on these known fields; never parse or emit unrelated secrets.
        raw_value = re.split(r"\s+[;#]", raw_value, maxsplit=1)[0].strip()
        values[target] = raw_value
    return values


def _bool(value: str, context: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"true", "yes", "on", "1"}:
        return True
    if normalized in {"false", "no", "off", "0", ""}:
        return False
    raise ContractError(f"invalid boolean in Gitea config: {context}")


def read_policy(path: Path) -> dict[str, object]:
    values = _parse_values(_read_lines(path))
    get = lambda section, key: values.get((section, key), DEFAULTS[(section, key)])
    default_private = get("repository", "DEFAULT_PRIVATE").lower()
    if default_private not in {"last", "private", "public"}:
        raise ContractError("invalid repository.DEFAULT_PRIVATE value")
    return {
        "disable_registration": _bool(
            get("service", "DISABLE_REGISTRATION"), "service.DISABLE_REGISTRATION"
        ),
        "require_signin_view": _bool(
            get("service", "REQUIRE_SIGNIN_VIEW"), "service.REQUIRE_SIGNIN_VIEW"
        ),
        "default_private": default_private,
        "force_private": _bool(
            get("repository", "FORCE_PRIVATE"), "repository.FORCE_PRIVATE"
        ),
    }


def render_policy(input_path: Path, output_path: Path, expected: dict[str, object]) -> None:
    lines = _read_lines(input_path)
    _parse_values(lines)  # reject duplicates before rendering
    desired = {
        ("service", "DISABLE_REGISTRATION"): str(expected["disable_registration"]).lower(),
        ("service", "REQUIRE_SIGNIN_VIEW"): str(expected["require_signin_view"]).lower(),
        ("repository", "DEFAULT_PRIVATE"): str(expected["default_private"]),
        ("repository", "FORCE_PRIVATE"): str(expected["force_private"]).lower(),
    }
    output: list[str] = []
    section = ""
    seen_sections: set[str] = set()
    emitted: set[tuple[str, str]] = set()

    def finish_section(name: str) -> None:
        if name not in TARGETS:
            return
        for key in TARGETS[name]:
            target = (name, key)
            if target not in emitted:
                output.append(f"{key} = {desired[target]}")
                emitted.add(target)

    for line in lines:
        section_match = SECTION_RE.match(line)
        if section_match:
            finish_section(section)
            section = section_match.group(1).strip().lower()
            seen_sections.add(section)
            output.append(line)
            continue
        key_match = KEY_RE.match(line)
        if key_match and section in TARGETS:
            key = key_match.group(1).upper()
            target = (section, key)
            if key in TARGETS[section]:
                output.append(f"{key} = {desired[target]}")
                emitted.add(target)
                continue
        output.append(line)
    finish_section(section)
    for missing_section in ("service", "repository"):
        if missing_section in seen_sections:
            continue
        if output and output[-1] != "":
            output.append("")
        output.append(f"[{missing_section}]")
        finish_section(missing_section)
    try:
        output_path.write_text("\n".join(output) + "\n", encoding="utf-8")
    except OSError as exc:
        raise ContractError(f"cannot write candidate Gitea config: {exc}") from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="gitea-service-policy")
    parser.add_argument("--manifest", required=True)
    subparsers = parser.add_subparsers(dest="command", required=True)
    read = subparsers.add_parser("read")
    read.add_argument("--config", required=True)
    render = subparsers.add_parser("render")
    render.add_argument("--config", required=True)
    render.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    try:
        contract = load_contract(args.manifest)
        if args.command == "read":
            print(json.dumps(read_policy(Path(args.config)), sort_keys=True))
            return 0
        render_policy(Path(args.config), Path(args.output), contract.raw["server_policy"])
        print(json.dumps({"result": "rendered"}, sort_keys=True))
        return 0
    except ContractError as exc:
        print(f"BLOCKED_EXTERNAL: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

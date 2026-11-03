"""Strict YAML check of platform skill frontmatter (#438).

Every skill that skills/skills.manifest declares, and every skills/<dir>/
holding a SKILL.md, must open with a `---` line, close the block with another
`---` line, and that block must parse as a YAML mapping whose `name` is a
string equal to the directory name and whose `description` is a non-empty
string. Every skills/<dir>/agents/*.yaml must parse as a mapping.

A tool that reads frontmatter strictly drops every field when the block does
not parse (the skill falls back to its directory name and first body line), so
"Claude Code happens to tolerate it" is not evidence. There is no hand-written
fallback parser: the backend is PyYAML (`yaml.safe_load`) when importable,
otherwise Ruby Psych (`YAML.safe_load`); with neither the run exits 2.
AISOFT_YAML_BACKEND=python|ruby forces one backend, for tests.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

BACKENDS = ("python", "ruby")
RUBY_PARSE = (
    'require "yaml"; require "json"; '
    "begin; s = $stdin.read; "
    # safe_load reads only the first document; a second one, valid or not,
    # would otherwise go unparsed (PyYAML's safe_load already refuses it).
    "n = YAML.parse_stream(s).children.length; "
    'raise "expected a single document in the stream, found #{n}" if n > 1; '
    "v = YAML.safe_load(s); "
    'puts JSON.generate({"ok" => true, "value" => v}); '
    "rescue Exception => e; "
    'puts JSON.generate({"ok" => false, "error" => e.message.lines.first.to_s.strip}); end'
)


class ParseError(Exception):
    pass


def python_available() -> bool:
    try:
        import yaml  # noqa: F401
    except ImportError:
        return False
    return True


def ruby_available() -> bool:
    ruby = shutil.which("ruby")
    if ruby is None:
        return False
    probe = subprocess.run(
        [ruby, "-Eutf-8", "-e", 'require "yaml"; require "json"'],
        stdin=subprocess.DEVNULL, capture_output=True,
    )
    return probe.returncode == 0


def select_backend() -> str:
    forced = os.environ.get("AISOFT_YAML_BACKEND", "")
    if forced:
        if forced not in BACKENDS:
            raise SystemExit(f"AISOFT_YAML_BACKEND 只能是 {'|'.join(BACKENDS)}，收到 {forced!r}")
        available = python_available() if forced == "python" else ruby_available()
        if not available:
            raise SystemExit(f"指定的 YAML 后端 {forced} 在本机不可用")
        return forced
    if python_available():
        return "python"
    if ruby_available():
        return "ruby"
    raise SystemExit("没有可用的严格 YAML 解析器：需要 python3 的 PyYAML 或带 Psych 的 ruby（#438 不回退到手写解析）")


def parse(backend: str, text: str) -> object:
    if backend == "python":
        import yaml

        try:
            return yaml.safe_load(text)
        except yaml.YAMLError as error:
            raise ParseError(" ".join(str(error).split())) from None
    result = subprocess.run(
        ["ruby", "-Eutf-8", "-e", RUBY_PARSE],
        input=text.encode("utf-8"), capture_output=True,
    )
    if result.returncode != 0:
        raise ParseError(f"ruby 退出 {result.returncode}: {result.stderr.decode('utf-8', 'replace').strip()}")
    reply = json.loads(result.stdout)
    if not reply["ok"]:
        raise ParseError(reply["error"])
    return reply["value"]


def frontmatter(text: str) -> str:
    lines = text.split("\n")
    if not lines or lines[0] != "---":
        raise ParseError("第一行必须是 ---")
    for index, line in enumerate(lines[1:], start=1):
        if line == "---":
            return "\n".join(lines[1:index]) + "\n"
    raise ParseError("frontmatter 没有闭合的 --- 行")


def declared_skills(skills: Path) -> list[str]:
    names = []
    for raw in (skills / "skills.manifest").read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line and not line.startswith("#"):
            names.append(line.split()[0])
    return names


def check(root: Path, backend: str) -> list[str]:
    skills = root / "skills"
    problems: list[str] = []
    try:
        declared = declared_skills(skills)
    except OSError as error:
        return [f"skills/skills.manifest: 读不到（{error.strerror}）"]
    present = sorted(p.parent.name for p in skills.glob("*/SKILL.md"))
    for name in list(dict.fromkeys(declared + present)):
        relative = f"skills/{name}/SKILL.md"
        path = skills / name / "SKILL.md"
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as error:
            problems.append(f"{relative}: 读不到（{error.strerror}）")
            continue
        except UnicodeDecodeError:
            problems.append(f"{relative}: 不是 UTF-8")
            continue
        try:
            value = parse(backend, frontmatter(text))
        except ParseError as error:
            problems.append(f"{relative}: frontmatter 不是合法 YAML：{error}")
            continue
        if not isinstance(value, dict):
            problems.append(f"{relative}: frontmatter 必须是 mapping，实际是 {type(value).__name__}")
            continue
        if value.get("name") != name:
            problems.append(f"{relative}: name 必须是字符串 {name!r}，实际是 {value.get('name')!r}")
        description = value.get("description")
        if not isinstance(description, str) or not description.strip():
            problems.append(f"{relative}: description 必须是非空字符串")
        for agent in sorted((skills / name / "agents").glob("*.yaml")):
            agent_relative = f"skills/{name}/agents/{agent.name}"
            try:
                agent_value = parse(backend, agent.read_text(encoding="utf-8"))
            except (ParseError, UnicodeDecodeError) as error:
                problems.append(f"{agent_relative}: 不是合法 YAML：{error}")
                continue
            if not isinstance(agent_value, dict):
                problems.append(f"{agent_relative}: 必须是 mapping")
    return problems


def main(argv: list[str]) -> int:
    root = None
    default_root = None
    args = list(argv)
    while args:
        flag = args.pop(0)
        if flag in ("--root", "--default-root") and args:
            value = Path(args.pop(0))
            if flag == "--root":
                root = value
            else:
                default_root = value
        else:
            print("usage: check-skill-frontmatter.sh [--root DIR]", file=sys.stderr)
            return 2
    root = root or default_root
    if root is None:
        print("usage: check-skill-frontmatter.sh [--root DIR]", file=sys.stderr)
        return 2
    try:
        backend = select_backend()
    except SystemExit as error:
        print(f"check-skill-frontmatter: {error}", file=sys.stderr)
        return 2
    problems = check(root, backend)
    for problem in problems:
        print(f"FAIL: {problem}")
    print(f"RESULT {'GAP' if problems else 'PASS'} (backend: {backend})")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

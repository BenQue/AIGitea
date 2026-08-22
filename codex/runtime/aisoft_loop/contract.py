"""Load and revalidate Issue contracts before a Development Loop starts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import subprocess
from typing import Mapping, Optional

from aisoft_change_name import ChangeName, ChangeNameError, SLUG_PATTERN, select_change_name

from .classification import CHANGE_TYPES, Classification, ClassificationError


DOCUMENT_ROLES = ("summary", "spec", "plan", "verification")
# Lifecycle states that assert a pull request already exists. Read from the
# repository rather than from Gitea on purpose (#142 spec §5.1): it keeps the
# change document audit offline and credential-free, and "status: pr-open with
# an empty pr_url" is a contradiction that needs no network to detect.
PR_BEARING_STATUSES = frozenset({"pr-open", "completed", "deployed"})
LEGACY_DOCUMENTS = {
    "summary": "00-summary.md",
    "spec": "01-spec.md",
    "plan": "02-plan.md",
    "verification": "03-verification.md",
}
NEW_DOCUMENT_RE = re.compile(
    r"^(summary|spec|plan|verification)-"
    rf"({SLUG_PATTERN})-(\d{{6}})\.md$"
)


# The executable half of the closed taxonomy, derived from the analyzer's
# CHANGE_TYPES so the two can never be edited apart. A type label that is
# canonical in the manifest but missing here makes the Loop refuse the Issue
# with "must have exactly one type label", and makes the label projector reject
# it as unknown — a failure whose message points nowhere near its cause.
# test_contract.py pins this set to codex/config/gitea-labels.json (#108).
TYPE_LABELS = frozenset(f"type/{name}" for name in CHANGE_TYPES)
COMPLEXITY_LABELS = frozenset({"complexity/small", "complexity/complex"})
LIFECYCLE_LABELS = frozenset(
    {
        "needs-analysis",
        "awaiting-triage",
        "spec-drafting",
        "spec-review",
        "approved",
        "pr-open",
        "completed",
        "deployed",
    }
)
DELIVERY_TERMINAL_LABELS = frozenset({"completed", "deployed"})
TRIAGE_CATEGORY_LABELS = frozenset({"triage/bug", "triage/enhancement"})
TRIAGE_STATE_LABELS = frozenset(
    {
        "triage/needs-triage",
        "triage/needs-info",
        "triage/ready-for-agent",
        "triage/ready-for-human",
        "triage/wontfix",
    }
)
TRIAGE_LABELS = TRIAGE_CATEGORY_LABELS | TRIAGE_STATE_LABELS


class ContractError(ValueError):
    """A contract cannot safely start or continue a Loop."""

    def __init__(
        self,
        *reasons: str,
        terminal_state: str = "NEEDS_HUMAN_DECISION",
        lifecycle_label: str = "awaiting-triage",
    ) -> None:
        self.reasons = tuple(reasons)
        self.terminal_state = terminal_state
        self.lifecycle_label = lifecycle_label
        super().__init__("; ".join(reasons))


@dataclass(frozen=True)
class Contract:
    issue_number: int
    title: str
    change_type: str
    effective_complexity: str
    contract_effect: str
    risk_flags: tuple[str, ...]
    branch: str
    document_directory: Path
    required_docs: tuple[str, ...]
    acceptance_criteria: tuple[str, ...]
    dependencies: tuple[int, ...]


def resolve_documents(repo: Path | str, issue_number: int) -> dict[str, str]:
    """Resolve one Issue's active document roles without requiring Loop readiness."""
    repo_path = Path(repo).resolve()
    if not repo_path.is_dir():
        raise ContractError(f"repository is unavailable: {repo_path}")
    if not isinstance(issue_number, int) or issue_number <= 0:
        raise ContractError("Issue number must be a positive integer")
    _, _, _, documents = _document_context(repo_path, issue_number)
    return documents


def resolve_summary(repo: Path | str, issue_number: int) -> tuple[Path, dict[str, object]]:
    """Resolve one Issue's active summary path and its parsed front matter.

    The public half of _document_context, added so callers that need the summary
    itself — rather than the documents mapping resolve_documents returns — do not
    reach into a private function. Every structural check resolve_documents makes
    still runs, so a caller cannot use this to read a summary the contract would
    have rejected.
    """
    repo_path = Path(repo).resolve()
    _, summary_path, summary, _ = _document_context(repo_path, issue_number)
    return summary_path, summary


def resolve_change_name(repo: Path | str, issue_number: int) -> ChangeName:
    """Resolve the one evidence-backed legacy or readable change tuple."""
    repo_path = Path(repo).resolve()
    if not repo_path.is_dir():
        raise ContractError(f"repository is unavailable: {repo_path}")
    return _change_directory(repo_path, issue_number)[0]


def load_contract(
    repo: Path | str,
    issue: Mapping[str, object],
    *,
    allowed_lifecycle: tuple[str, ...] = ("approved",),
    change_control: str = "production",
) -> Contract:
    repo_path = Path(repo).resolve()
    if not repo_path.is_dir():
        raise ContractError(
            f"repository is unavailable: {repo_path}",
            terminal_state="BLOCKED_EXTERNAL",
            lifecycle_label="approved",
        )

    number = issue.get("number")
    if not isinstance(number, int) or number <= 0:
        raise ContractError("Issue number must be a positive integer")
    if issue.get("state") != "open":
        raise ContractError("Issue must be open before starting the Loop")

    labels = _label_names(issue.get("labels"))
    type_labels = sorted(labels & TYPE_LABELS)
    complexity_labels = sorted(labels & COMPLEXITY_LABELS)
    lifecycle_labels = sorted(labels & LIFECYCLE_LABELS)
    if len(type_labels) != 1:
        raise ContractError(f"Issue must have exactly one type label, got {type_labels}")
    if len(complexity_labels) != 1:
        raise ContractError(
            f"Issue must have exactly one effective complexity label, got {complexity_labels}"
        )
    if len(lifecycle_labels) != 1 or lifecycle_labels[0] not in allowed_lifecycle:
        raise ContractError(
            f"Issue lifecycle must be one of {allowed_lifecycle}, got {lifecycle_labels}",
            lifecycle_label=lifecycle_labels[0] if len(lifecycle_labels) == 1 else "awaiting-triage",
        )

    directory, summary_path, summary, documents = _document_context(repo_path, number)
    try:
        change_name = ChangeName.parse_directory(directory.name, issue_number=number)
    except ChangeNameError as exc:
        raise ContractError(str(exc)) from exc
    summary_text = summary_path.read_text(encoding="utf-8")
    dependencies = _dependencies(summary.get("depends_on", []), number)
    expected_branch = change_name.branch
    if _as_int(summary.get("issue")) != number:
        raise ContractError("summary issue does not match the Gitea Issue number")
    if summary.get("branch") != expected_branch:
        raise ContractError("summary branch must be " + expected_branch)

    try:
        classification = _classification_from_front_matter(summary)
        route = classification.route(change_control=change_control)
    except ClassificationError as exc:
        raise ContractError(f"summary classification is invalid: {exc}") from exc
    if route.effective_complexity is None:
        raise ContractError(
            "classification is unresolved",
            lifecycle_label="awaiting-triage",
        )

    expected_type_label = f"type/{classification.change_type}"
    if type_labels != [expected_type_label]:
        raise ContractError(
            f"type label {type_labels[0]} conflicts with summary {expected_type_label}"
        )
    expected_complexity_label = f"complexity/{route.effective_complexity}"
    if complexity_labels != [expected_complexity_label]:
        forced = " forced complex" if route.effective_complexity == "complex" else ""
        raise ContractError(
            f"complexity label {complexity_labels[0]} conflicts with{forced} route {expected_complexity_label}",
            lifecycle_label="spec-drafting" if route.effective_complexity == "complex" else "awaiting-triage",
        )

    required_docs = _required_document_names(route.required_docs, documents)
    missing_docs = [name for name in required_docs if not directory.joinpath(name).is_file()]
    if missing_docs:
        lifecycle = "spec-drafting" if route.effective_complexity == "complex" else "awaiting-triage"
        raise ContractError(
            "missing required contract documents: " + ", ".join(missing_docs),
            lifecycle_label=lifecycle,
        )

    body = str(issue.get("body") or "")
    _reject_governing_self_modification(body)
    spec_required = bool({"spec", "01-spec.md"} & set(route.required_docs))
    if route.effective_complexity == "small":
        criteria = _acceptance_criteria(body)
        if not criteria:
            raise ContractError("small Issue requires measurable acceptance criteria")
    elif not spec_required:
        # development 阶段的 complex 没有 spec，验收标准改由 Issue 正文提供。
        # 「必须有可测验收」这条门槛不随阶段放宽——它正是 verification 得以成立的前提。
        criteria = _acceptance_criteria(body)
        if not criteria:
            raise ContractError(
                "development-phase complex Issue requires measurable acceptance criteria in the Issue body"
            )
    else:
        spec_name = documents["spec"]
        plan_name = documents["plan"]
        spec_text = directory.joinpath(spec_name).read_text(encoding="utf-8")
        plan_text = directory.joinpath(plan_name).read_text(encoding="utf-8")
        _validate_complex_document_front_matter(spec_text, number, expected_branch, spec_name)
        _validate_complex_document_front_matter(plan_text, number, expected_branch, plan_name)
        criteria = _acceptance_criteria(spec_text)
        if not criteria:
            raise ContractError("01-spec.md requires measurable acceptance criteria")
        unresolved = _section(spec_text, "未决问题")
        if not unresolved or not re.match(r"^(无|没有|none\b)", unresolved.strip(), re.IGNORECASE):
            raise ContractError("01-spec.md 未决问题 must be resolved before approved")
        if not re.search(r"\|\s*AC-\d+\s*\|", plan_text, re.IGNORECASE):
            raise ContractError("02-plan.md must map each AC to a verification command or review")
        _reject_governing_self_modification(spec_text + "\n" + plan_text)

    return Contract(
        issue_number=number,
        title=str(issue.get("title") or ""),
        change_type=classification.change_type,
        effective_complexity=route.effective_complexity,
        contract_effect=classification.contract_effect,
        risk_flags=classification.risk_flags,
        branch=expected_branch,
        document_directory=directory,
        required_docs=required_docs,
        acceptance_criteria=criteria,
        dependencies=dependencies,
    )


def parse_front_matter(text: str) -> dict[str, object]:
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        raise ContractError("document must start with YAML front matter")
    try:
        end = lines.index("---", 1)
    except ValueError as exc:
        raise ContractError("document front matter is not closed") from exc

    values: dict[str, object] = {}
    active: Optional[str] = None
    for line_number, raw_line in enumerate(lines[1:end], start=2):
        if not raw_line.strip():
            continue
        if "\t" in raw_line:
            raise ContractError(f"tabs are forbidden in front matter line {line_number}")
        if raw_line.startswith("  - "):
            if active is None:
                raise ContractError(f"list item without field at front matter line {line_number}")
            if not isinstance(values[active], list):
                values[active] = []
            item = _safe_scalar(raw_line[4:].strip(), line_number)
            assert isinstance(values[active], list)
            values[active].append(item)
            continue
        if raw_line.startswith("  "):
            if active != "documents" or ":" not in raw_line[2:]:
                raise ContractError(f"unsupported front matter syntax at line {line_number}")
            name, raw_value = raw_line[2:].split(":", 1)
            if not re.fullmatch(r"[a-z_]+", name):
                raise ContractError(f"invalid documents key at line {line_number}")
            if not isinstance(values[active], dict):
                values[active] = {}
            mapping = values[active]
            assert isinstance(mapping, dict)
            if name in mapping:
                raise ContractError(f"duplicate documents key {name}")
            value = raw_value.strip()
            if not value:
                raise ContractError(f"empty documents value at line {line_number}")
            mapping[name] = _safe_scalar(value, line_number)
            continue
        if raw_line[0].isspace() or ":" not in raw_line:
            raise ContractError(f"unsupported front matter syntax at line {line_number}")
        name, raw_value = raw_line.split(":", 1)
        if name in values:
            raise ContractError(f"duplicate front matter field {name}")
        value = raw_value.strip()
        active = name if not value else None
        if value == "[]":
            values[name] = []
        elif value:
            values[name] = _safe_scalar(value, line_number)
        else:
            values[name] = ""
    return values


def _find_summary(directory: Path) -> Path:
    legacy = directory / LEGACY_DOCUMENTS["summary"]
    candidates = sorted(
        path
        for path in directory.iterdir()
        if path.is_file() and NEW_DOCUMENT_RE.fullmatch(path.name)
        and path.name.startswith("summary-")
    ) if directory.is_dir() else []
    if legacy.is_file() and candidates:
        raise ContractError("both legacy and new summary documents exist")
    if legacy.is_file():
        return legacy
    if len(candidates) != 1:
        raise ContractError("exactly one new summary document is required")
    return candidates[0]


def _document_context(
    repo: Path, issue_number: int
) -> tuple[Path, Path, dict[str, object], dict[str, str]]:
    change_name, directory = _change_directory(repo, issue_number)
    summary_path = _find_summary(directory)
    summary = parse_front_matter(summary_path.read_text(encoding="utf-8"))
    documents = _resolve_documents(directory, summary_path, summary, change_name)
    return directory, summary_path, summary, documents


def _change_directory(repo: Path, issue_number: int) -> tuple[ChangeName, Path]:
    root = repo / "docs" / "changes"
    candidates: list[tuple[ChangeName, Path]] = []
    if root.is_dir():
        for path in root.iterdir():
            if not path.is_dir():
                continue
            try:
                name = ChangeName.parse_directory(path.name, issue_number=issue_number)
            except ChangeNameError:
                continue
            candidates.append((name, path))
    try:
        selected = select_change_name(issue_number, (name for name, _ in candidates))
    except ChangeNameError as exc:
        raise ContractError(str(exc)) from exc
    assert selected is not None
    if selected.is_legacy:
        relative = Path("docs") / "changes" / selected.directory_name
        result = subprocess.run(
            ("git", "log", "-1", "--format=%H", "--", relative.as_posix()),
            cwd=repo,
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0 or not result.stdout.strip():
            raise ContractError(
                "legacy change directory requires repository history evidence"
            )
    for name, path in candidates:
        if name == selected:
            return name, path
    raise AssertionError("selected change directory is unavailable")


def _resolve_documents(
    directory: Path,
    summary_path: Path,
    summary: Mapping[str, object],
    change_name: ChangeName,
) -> dict[str, str]:
    raw = summary.get("documents")
    if summary_path.name == LEGACY_DOCUMENTS["summary"]:
        if raw not in (None, ""):
            raise ContractError("legacy summary must not declare documents mapping")
        return dict(LEGACY_DOCUMENTS)
    if not isinstance(raw, Mapping) or not raw:
        raise ContractError("new summary requires a documents mapping")
    unknown = set(raw) - set(DOCUMENT_ROLES)
    if unknown:
        raise ContractError(f"unknown document roles: {sorted(unknown)}")
    documents: dict[str, str] = {}
    slugs: set[str] = set()
    for role, value in raw.items():
        if not isinstance(value, str) or Path(value).name != value or len(value) > 64:
            raise ContractError(f"documents.{role} must be a safe basename of at most 64 characters")
        match = NEW_DOCUMENT_RE.fullmatch(value)
        if not match or match.group(1) != role:
            raise ContractError(f"documents.{role} has an invalid role, slug, or date")
        slug = match.group(2)
        if len(slug) > 32:
            raise ContractError(f"documents.{role} slug exceeds 32 characters")
        slugs.add(slug)
        documents[str(role)] = value
    if len(slugs) != 1:
        raise ContractError("all new change documents must use the same slug")
    if change_name.slug is not None and slugs != {change_name.slug}:
        raise ContractError("document slug must match the readable change directory")
    if documents.get("summary") != summary_path.name:
        raise ContractError("documents.summary must reference the active summary")
    declared_names = set(documents.values())
    present_names = {
        path.name
        for path in directory.iterdir()
        if path.is_file() and NEW_DOCUMENT_RE.fullmatch(path.name)
    }
    undeclared = present_names - declared_names
    if undeclared:
        raise ContractError("new change documents are not declared: " + ", ".join(sorted(undeclared)))
    for role, name in documents.items():
        path = directory / name
        if not path.is_file():
            continue
        front_matter = summary if path == summary_path else parse_front_matter(
            path.read_text(encoding="utf-8")
        )
        created = front_matter.get("created")
        match = NEW_DOCUMENT_RE.fullmatch(name)
        assert match is not None
        if not isinstance(created, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", created):
            raise ContractError(f"documents.{role} requires created: YYYY-MM-DD")
        if created[2:4] + created[5:7] + created[8:10] != match.group(3):
            raise ContractError(f"documents.{role} date must match its created field")
    return documents


def _required_document_names(
    required: tuple[str, ...], documents: Mapping[str, str]
) -> tuple[str, ...]:
    role_based = required and required[0] == "summary"
    if role_based:
        missing_roles = [role for role in required if role not in documents]
        if missing_roles:
            raise ContractError("documents mapping is missing required roles: " + ", ".join(missing_roles))
        return tuple(documents[role] for role in required)
    if any(name not in LEGACY_DOCUMENTS.values() for name in required):
        raise ContractError("legacy required_docs contains unsupported filenames")
    return required


def _classification_from_front_matter(front_matter: Mapping[str, object]) -> Classification:
    fields = [
        "change_type",
        "requested_complexity",
        "assessed_complexity",
    ]
    if "effective_complexity" in front_matter:
        fields.append("effective_complexity")
    fields.extend(
        (
            "contract_effect",
            "reason",
            "risk_flags",
            "required_docs",
            "confidence",
            "override_reason",
        )
    )
    output: list[str] = []
    for name in fields:
        if name not in front_matter:
            raise ClassificationError(f"missing summary field {name}")
        value = front_matter[name]
        if isinstance(value, list):
            if not value:
                output.append(f"{name}: []")
            else:
                output.append(f"{name}:")
                output.extend(f"  - {item}" for item in value)
        else:
            scalar = str(value)
            rendered = scalar if scalar else "''"
            output.append(f"{name}: {rendered}")
    return Classification.from_yaml("\n".join(output) + "\n")


def _validate_complex_document_front_matter(
    text: str, number: int, branch: str, filename: str
) -> None:
    front_matter = parse_front_matter(text)
    if _as_int(front_matter.get("issue")) != number:
        raise ContractError(f"{filename} issue does not match")
    if front_matter.get("branch") != branch:
        raise ContractError(f"{filename} branch must be {branch}")
    if front_matter.get("effective_complexity") != "complex":
        raise ContractError(f"{filename} must declare effective_complexity: complex")


def _label_names(raw_labels: object) -> set[str]:
    if not isinstance(raw_labels, list):
        return set()
    names: set[str] = set()
    for item in raw_labels:
        if isinstance(item, str):
            names.add(item)
        elif isinstance(item, Mapping) and isinstance(item.get("name"), str):
            names.add(str(item["name"]))
    return names


def _acceptance_criteria(text: str) -> tuple[str, ...]:
    match = re.search(
        r"^##\s+(?:Acceptance criteria|验收标准|验收条件)\s*$([\s\S]*?)(?=^##\s+|\Z)",
        text,
        re.IGNORECASE | re.MULTILINE,
    )
    if not match:
        return ()
    criteria: list[str] = []
    for line in match.group(1).splitlines():
        item = re.match(r"^\s*[-*]\s+(?:\[[ xX]\]\s*)?(.+?)\s*$", line)
        if not item:
            continue
        value = item.group(1).strip()
        if value and not re.search(r"待填写|placeholder|以后补", value, re.IGNORECASE):
            criteria.append(value)
    return tuple(criteria)


def _section(text: str, heading: str) -> str:
    match = re.search(
        rf"^##\s+{re.escape(heading)}\s*$([\s\S]*?)(?=^##\s+|\Z)",
        text,
        re.MULTILINE,
    )
    return match.group(1).strip() if match else ""


def _reject_governing_self_modification(text: str) -> None:
    if "AGENTS.md" not in text:
        return
    candidate = re.sub(
        r"[^。.!?\n]*(?:must\s+not|never|不得|永远不)[^。.!?\n]*AGENTS\.md[^。.!?\n]*[。.!?]?",
        "",
        text,
        flags=re.IGNORECASE,
    )
    direct_self_mod = re.search(
        r"(?:running|current|governing|本次运行|当前运行).{0,50}"
        r"(?:edit|modify|write|修改|编辑|写入).{0,30}AGENTS\.md"
        r"|(?:edit|modify|write|修改|编辑|写入).{0,50}"
        r"(?:running|current|governing|本次运行|当前运行).{0,30}AGENTS\.md",
        candidate,
        re.IGNORECASE | re.DOTALL,
    )
    if direct_self_mod:
        raise ContractError(
            "ordinary worker must not edit the governing AGENTS.md for its current run"
        )


def _safe_scalar(value: str, line_number: int) -> str:
    if any(marker in value for marker in ("&", "*", "!", "{", "}", "[", "]")):
        raise ContractError(f"unsafe YAML scalar at line {line_number}")
    if value.startswith(("'", '"')):
        if len(value) < 2 or value[-1] != value[0]:
            raise ContractError(f"unterminated quoted scalar at line {line_number}")
        value = value[1:-1]
    return value


def _as_int(value: object) -> Optional[int]:
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return None


def _dependencies(value: object, issue_number: int) -> tuple[int, ...]:
    if value in ("", None):
        return ()
    if not isinstance(value, list):
        raise ContractError("summary depends_on must be a list of positive Issue numbers")
    dependencies: list[int] = []
    for item in value:
        dependency = _as_int(item)
        if dependency is None or dependency <= 0:
            raise ContractError("summary depends_on must contain only positive Issue numbers")
        if dependency == issue_number:
            raise ContractError("summary depends_on must not reference its own Issue")
        if dependency in dependencies:
            raise ContractError(f"summary depends_on contains duplicate Issue #{dependency}")
        dependencies.append(dependency)
    return tuple(dependencies)

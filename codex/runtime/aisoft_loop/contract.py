"""Load and revalidate Issue contracts before a Development Loop starts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Mapping, Optional

from .classification import Classification, ClassificationError


TYPE_LABELS = frozenset(
    {
        "type/bugfix",
        "type/feature",
        "type/docs",
        "type/test",
        "type/refactor",
        "type/maintenance",
        "type/platform",
    }
)
COMPLEXITY_LABELS = frozenset({"complexity/small", "complexity/complex"})
LIFECYCLE_LABELS = frozenset(
    {
        "needs-analysis",
        "awaiting-triage",
        "spec-drafting",
        "spec-review",
        "approved",
        "pr-open",
        "deployed",
    }
)


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


def load_contract(
    repo: Path | str,
    issue: Mapping[str, object],
    *,
    allowed_lifecycle: tuple[str, ...] = ("approved",),
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

    directory = repo_path / "docs" / "changes" / str(number)
    summary_path = directory / "00-summary.md"
    if not summary_path.is_file():
        raise ContractError("summary 00-summary.md is missing")
    summary_text = summary_path.read_text(encoding="utf-8")
    summary = parse_front_matter(summary_text)
    expected_branch = f"change/{number}"
    if _as_int(summary.get("issue")) != number:
        raise ContractError("summary issue does not match the Gitea Issue number")
    if summary.get("branch") != expected_branch:
        raise ContractError("summary branch must be " + expected_branch)

    try:
        classification = _classification_from_front_matter(summary)
        route = classification.route()
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

    required_docs = route.required_docs
    missing_docs = [name for name in required_docs if not directory.joinpath(name).is_file()]
    if missing_docs:
        lifecycle = "spec-drafting" if route.effective_complexity == "complex" else "awaiting-triage"
        raise ContractError(
            "missing required contract documents: " + ", ".join(missing_docs),
            lifecycle_label=lifecycle,
        )

    body = str(issue.get("body") or "")
    _reject_governing_self_modification(body)
    if route.effective_complexity == "small":
        criteria = _acceptance_criteria(body)
        if not criteria:
            raise ContractError("small Issue requires measurable acceptance criteria")
    else:
        spec_text = directory.joinpath("01-spec.md").read_text(encoding="utf-8")
        plan_text = directory.joinpath("02-plan.md").read_text(encoding="utf-8")
        _validate_complex_document_front_matter(spec_text, number, expected_branch, "01-spec.md")
        _validate_complex_document_front_matter(plan_text, number, expected_branch, "02-plan.md")
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
    direct_self_mod = re.search(
        r"(?:running|current|governing|本次运行|当前运行).{0,50}"
        r"(?:edit|modify|write|修改|编辑|写入).{0,30}AGENTS\.md"
        r"|(?:edit|modify|write|修改|编辑|写入).{0,50}"
        r"(?:running|current|governing|本次运行|当前运行).{0,30}AGENTS\.md",
        text,
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

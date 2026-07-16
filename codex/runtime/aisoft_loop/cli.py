"""Command-line entrypoints for the provider-neutral Loop runtime."""

from __future__ import annotations

import argparse
from datetime import date
import json
import os
from pathlib import Path
import sys

from .analysis import (
    AnalysisError,
    AnalysisResult,
    analyze_route,
    render_summary,
    route_labels,
)
from .controller import Controller, LocalGit
from .gitea import GiteaClient, GiteaError
from .provider import CommandProvider, ProviderError, ProviderResult
from .state import GlobalLock, StateStore, TerminalState, default_state_root
from .verifier import VerificationConfigError, Verifier


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="aisoft-loop")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="run or resume one Issue Loop")
    run_parser.add_argument("issue", type=int)
    run_parser.add_argument("--repo", required=True, type=Path)
    run_parser.add_argument(
        "--verification-config",
        default=Path(".gitea/loop-verification.json"),
        type=Path,
    )

    validate_parser = subparsers.add_parser(
        "validate-provider", help="validate and normalize provider result JSON"
    )
    validate_parser.add_argument("input", type=Path)
    validate_parser.add_argument("output", type=Path)

    validate_analysis = subparsers.add_parser(
        "validate-analysis", help="validate and normalize analyzer result JSON"
    )
    validate_analysis.add_argument("input", type=Path)
    validate_analysis.add_argument("output", type=Path)

    get_issue = subparsers.add_parser("get-issue", help="write one Issue JSON privately")
    get_issue.add_argument("issue", type=int)
    get_issue.add_argument("output", type=Path)

    list_issues = subparsers.add_parser("list-issues", help="list open Issue numbers by label")
    list_issues.add_argument("label")

    render_analysis = subparsers.add_parser(
        "render-analysis", help="render a validated 00-summary.md"
    )
    render_analysis.add_argument("issue_json", type=Path)
    render_analysis.add_argument("result_json", type=Path)
    render_analysis.add_argument("output_summary", type=Path)

    apply_analysis = subparsers.add_parser(
        "apply-analysis", help="apply analyzer labels and audit comment"
    )
    apply_analysis.add_argument("issue", type=int)
    apply_analysis.add_argument("result_json", type=Path)
    apply_analysis.add_argument("summary_url")

    args = parser.parse_args(argv)
    if args.command == "validate-provider":
        return _validate_provider(args.input, args.output)
    if args.command == "validate-analysis":
        return _validate_analysis(args.input, args.output)
    if args.command == "get-issue":
        return _get_issue(args.issue, args.output)
    if args.command == "list-issues":
        return _list_issues(args.label)
    if args.command == "render-analysis":
        return _render_analysis(args.issue_json, args.result_json, args.output_summary)
    if args.command == "apply-analysis":
        return _apply_analysis(args.issue, args.result_json, args.summary_url)
    return _run(args.issue, args.repo, args.verification_config)


def _run(issue: int, repo: Path, verification_config: Path) -> int:
    required_env = ("GITEA_URL", "GITEA_OWNER", "GITEA_REPO", "GITEA_TOKEN")
    missing = [name for name in required_env if not os.environ.get(name)]
    if missing:
        print("missing required environment: " + ", ".join(missing), file=sys.stderr)
        return 2
    state_root = Path(os.environ.get("AISOFT_LOOP_STATE_DIR") or default_state_root())
    source_provider = Path(__file__).parents[2] / "agent" / "codex-provider.sh"
    default_provider = (
        source_provider if source_provider.is_file() else Path.home() / "agent" / "codex-provider.sh"
    )
    provider_script = Path(
        os.environ.get("CODEX_PROVIDER_SCRIPT") or default_provider
    ).resolve()
    branch = f"change/{issue}"
    try:
        gitea = GiteaClient(
            os.environ["GITEA_URL"],
            os.environ["GITEA_OWNER"],
            os.environ["GITEA_REPO"],
            os.environ["GITEA_TOKEN"],
        )
        controller = Controller(
            repo=repo,
            gitea=gitea,
            provider=CommandProvider(
                (str(provider_script),),
                timeout_seconds=int(os.environ.get("LOOP_PROVIDER_TIMEOUT", "2700")),
            ),
            verifier=Verifier.from_file(repo, verification_config),
            git=LocalGit(repo, branch),
            state_store=StateStore(state_root),
            lock=GlobalLock(state_root / "loop.lock"),
            max_rounds=int(os.environ.get("LOOP_MAX_ROUNDS", "8")),
            max_same_root=int(os.environ.get("LOOP_MAX_SAME_ROOT", "3")),
        )
        result = controller.run(issue)
    except (GiteaError, ProviderError, VerificationConfigError, ValueError) as exc:
        print(json.dumps({"terminal_state": "BLOCKED_EXTERNAL", "message": str(exc)}))
        return 2
    print(
        json.dumps(
            {
                "terminal_state": result.terminal_state.value,
                "message": result.message,
                "pr_number": result.pr_number,
            },
            ensure_ascii=False,
        )
    )
    return 0 if result.terminal_state in {TerminalState.CONTINUE, TerminalState.READY_FOR_REVIEW} else 2


def _validate_provider(input_path: Path, output_path: Path) -> int:
    try:
        result = ProviderResult.from_json(input_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ProviderError) as exc:
        print(f"invalid provider result: {exc}", file=sys.stderr)
        return 2
    output_path.write_text(
        json.dumps(
            {
                "status": result.status,
                "summary": result.summary,
                "changed_files": list(result.changed_files),
                "root_cause": result.root_cause,
                "escalation": result.escalation,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    os.chmod(output_path, 0o600)
    return 0


def _validate_analysis(input_path: Path, output_path: Path) -> int:
    try:
        result = AnalysisResult.from_json(input_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, AnalysisError) as exc:
        print(f"invalid analyzer result: {exc}", file=sys.stderr)
        return 2
    output_path.write_text(_analysis_json(result) + "\n", encoding="utf-8")
    os.chmod(output_path, 0o600)
    return 0


def _get_issue(issue_number: int, output_path: Path) -> int:
    try:
        issue = _gitea_from_env().get_issue(issue_number)
        output_path.write_text(
            json.dumps(issue, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        os.chmod(output_path, 0o600)
        return 0
    except (GiteaError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


def _list_issues(label: str) -> int:
    try:
        issues = _gitea_from_env().list_issues(label)
    except GiteaError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    for issue in issues:
        number = issue.get("number")
        if isinstance(number, int):
            print(number)
    return 0


def _render_analysis(issue_path: Path, result_path: Path, output_path: Path) -> int:
    try:
        issue = json.loads(issue_path.read_text(encoding="utf-8"))
        if not isinstance(issue, dict):
            raise AnalysisError("Issue JSON must be an object")
        result = AnalysisResult.from_json(result_path.read_text(encoding="utf-8"))
        route = analyze_route(issue, result)
        output = render_summary(
            issue,
            result,
            route,
            _required_env("GITEA_URL"),
            _required_env("GITEA_OWNER"),
            _required_env("GITEA_REPO"),
            date=date.today().isoformat(),
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output, encoding="utf-8")
        os.chmod(output_path, 0o644)
        return 0
    except (OSError, UnicodeError, json.JSONDecodeError, AnalysisError, RuntimeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


def _apply_analysis(issue_number: int, result_path: Path, summary_url: str) -> int:
    try:
        gitea = _gitea_from_env()
        issue = gitea.get_issue(issue_number)
        result = AnalysisResult.from_json(result_path.read_text(encoding="utf-8"))
        route = analyze_route(issue, result)
        labels = route_labels(result, route)
        gitea.set_labels(issue_number, labels)
        effective = route.effective_complexity or "needs-human-decision"
        gitea.comment(
            issue_number,
            "🤖 **AI 判级完成**\n\n"
            f"- effective complexity: `{effective}`\n"
            f"- lifecycle: `{route.lifecycle_label}`\n"
            f"- summary: {summary_url}\n\n"
            "最终 PR 仍须人工审核与合并。",
        )
        return 0
    except (GiteaError, OSError, UnicodeError, AnalysisError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


def _gitea_from_env() -> GiteaClient:
    return GiteaClient(
        _required_env("GITEA_URL"),
        _required_env("GITEA_OWNER"),
        _required_env("GITEA_REPO"),
        _required_env("GITEA_TOKEN"),
    )


def _required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"missing required environment: {name}")
    return value


def _analysis_json(result: AnalysisResult) -> str:
    return json.dumps(
        {
            "classification": _classification_yaml(result),
            "problem_summary": result.problem_summary,
            "impact": result.impact,
            "approach": result.approach,
            "risks": list(result.risks),
            "evidence": list(result.evidence),
            "missing_acceptance_criteria": list(result.missing_acceptance_criteria),
        },
        ensure_ascii=False,
        sort_keys=True,
    )


def _classification_yaml(result: AnalysisResult) -> str:
    classification = result.classification
    lines = [
        f"change_type: {classification.change_type}",
        f"requested_complexity: {classification.requested_complexity}",
        f"assessed_complexity: {classification.assessed_complexity}",
    ]
    if classification.effective_complexity is not None:
        lines.append(f"effective_complexity: {classification.effective_complexity}")
    lines.extend(
        (
            f"contract_effect: {classification.contract_effect}",
            f"reason: {classification.reason}",
        )
    )
    if classification.risk_flags:
        lines.append("risk_flags:")
        lines.extend(f"  - {item}" for item in classification.risk_flags)
    else:
        lines.append("risk_flags: []")
    lines.append("required_docs:")
    lines.extend(f"  - {item}" for item in classification.required_docs)
    lines.extend(
        (
            f"confidence: {classification.confidence}",
            "override_reason: " + (classification.override_reason or "''"),
        )
    )
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())

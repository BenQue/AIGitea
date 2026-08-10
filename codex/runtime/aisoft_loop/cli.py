"""Command-line entrypoints for the provider-neutral Loop runtime."""

from __future__ import annotations

import argparse
from datetime import date
import json
import os
from pathlib import Path
import sys
from typing import Mapping

from .analysis import (
    AnalysisError,
    AnalysisResult,
    analyze_route,
    render_summary,
    route_labels,
    summary_filename,
)
from .controller import Controller, LocalGit
from .contract import ContractError, resolve_change_name, resolve_documents
from .documents import publish_plan, publish_spec
from .gitea import GiteaClient, GiteaError
from .output import OutputError, extract_last_json_object
from .provider import CommandProvider, ProviderError, ProviderResult
from .state import GlobalLock, StateStore, TerminalState, default_state_root
from .verifier import VerificationConfigError, Verifier


IMPLEMENTATION_PROVIDERS = ("codex", "claude")


def select_provider_script(env: Mapping[str, str], agent_dir: Path | str) -> Path:
    """Resolve the adapter for the explicitly selected implementation provider."""
    provider = (env.get("IMPLEMENT_PROVIDER") or "none").strip()
    if provider == "none":
        raise ProviderError("implementation provider is disabled")
    if provider not in IMPLEMENTATION_PROVIDERS:
        raise ProviderError(f"unsupported implementation provider: {provider!r}")
    override = env.get(f"{provider.upper()}_PROVIDER_SCRIPT")
    script = Path(override) if override else Path(agent_dir) / f"{provider}-provider.sh"
    return script.resolve()


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

    analysis_slug = subparsers.add_parser(
        "analysis-slug", help="print the validated readable slug from analyzer JSON"
    )
    analysis_slug.add_argument("input", type=Path)

    extract_json = subparsers.add_parser(
        "extract-json", help="isolate the last JSON object in raw provider output"
    )
    extract_json.add_argument("input", type=Path)
    extract_json.add_argument("output", type=Path)

    get_issue = subparsers.add_parser("get-issue", help="write one Issue JSON privately")
    get_issue.add_argument("issue", type=int)
    get_issue.add_argument("output", type=Path)

    list_issues = subparsers.add_parser("list-issues", help="list open Issue numbers by label")
    list_issues.add_argument("label")

    render_analysis = subparsers.add_parser(
        "render-analysis", help="render a validated named summary document"
    )
    render_analysis.add_argument("issue_json", type=Path)
    render_analysis.add_argument("result_json", type=Path)
    render_analysis.add_argument("output_directory", type=Path)

    apply_analysis = subparsers.add_parser(
        "apply-analysis", help="apply analyzer labels and audit comment"
    )
    apply_analysis.add_argument("issue", type=int)
    apply_analysis.add_argument("result_json", type=Path)
    apply_analysis.add_argument("summary_url")

    resolve_document_names = subparsers.add_parser(
        "resolve-documents", help="resolve one Issue's active change document names"
    )
    resolve_document_names.add_argument("issue", type=int)
    resolve_document_names.add_argument("--repo", required=True, type=Path)

    for command, help_text in (
        ("publish-spec", "publish to the Issue's mapped spec path"),
        ("publish-plan", "publish to the Issue's mapped plan path"),
    ):
        publish = subparsers.add_parser(command, help=help_text)
        publish.add_argument("issue", type=int)
        publish.add_argument("body", type=Path)
        publish.add_argument("--repo", required=True, type=Path)

    args = parser.parse_args(argv)
    if args.command == "validate-provider":
        return _validate_provider(args.input, args.output)
    if args.command == "validate-analysis":
        return _validate_analysis(args.input, args.output)
    if args.command == "analysis-slug":
        return _analysis_slug(args.input)
    if args.command == "extract-json":
        return _extract_json(args.input, args.output)
    if args.command == "get-issue":
        return _get_issue(args.issue, args.output)
    if args.command == "list-issues":
        return _list_issues(args.label)
    if args.command == "render-analysis":
        return _render_analysis(args.issue_json, args.result_json, args.output_directory)
    if args.command == "apply-analysis":
        return _apply_analysis(args.issue, args.result_json, args.summary_url)
    if args.command == "resolve-documents":
        return _resolve_documents(args.repo, args.issue)
    if args.command == "publish-spec":
        return _publish_document(args.repo, args.issue, args.body, "spec")
    if args.command == "publish-plan":
        return _publish_document(args.repo, args.issue, args.body, "plan")
    return _run(args.issue, args.repo, args.verification_config)


def _run(issue: int, repo: Path, verification_config: Path) -> int:
    required_env = ("GITEA_URL", "GITEA_OWNER", "GITEA_REPO", "GITEA_TOKEN")
    missing = [name for name in required_env if not os.environ.get(name)]
    if missing:
        print("missing required environment: " + ", ".join(missing), file=sys.stderr)
        return 2
    state_root = Path(os.environ.get("AISOFT_LOOP_STATE_DIR") or default_state_root())
    source_agent = Path(__file__).parents[2] / "agent"
    agent_dir = source_agent if source_agent.is_dir() else Path.home() / "agent"
    try:
        branch = resolve_change_name(repo, issue).branch
        provider_script = select_provider_script(os.environ, agent_dir)
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


def _analysis_slug(input_path: Path) -> int:
    try:
        result = AnalysisResult.from_json(input_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, AnalysisError) as exc:
        print(f"invalid analyzer result: {exc}", file=sys.stderr)
        return 2
    print(result.document_slug)
    return 0


def _extract_json(input_path: Path, output_path: Path) -> int:
    try:
        text = extract_last_json_object(input_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, OutputError) as exc:
        print(f"unusable provider output: {exc}", file=sys.stderr)
        return 2
    output_path.write_text(text + "\n", encoding="utf-8")
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


def _render_analysis(issue_path: Path, result_path: Path, output_directory: Path) -> int:
    try:
        issue = json.loads(issue_path.read_text(encoding="utf-8"))
        if not isinstance(issue, dict):
            raise AnalysisError("Issue JSON must be an object")
        result = AnalysisResult.from_json(result_path.read_text(encoding="utf-8"))
        route = analyze_route(issue, result)
        created = date.today().isoformat()
        output = render_summary(
            issue,
            result,
            route,
            _required_env("GITEA_URL"),
            _required_env("GITEA_OWNER"),
            _required_env("GITEA_REPO"),
            date=created,
        )
        output_path = output_directory / summary_filename(result, created)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output, encoding="utf-8")
        os.chmod(output_path, 0o644)
        print(output_path)
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


def _resolve_documents(repo: Path, issue_number: int) -> int:
    try:
        print(
            json.dumps(
                resolve_documents(repo, issue_number),
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return 0
    except (OSError, UnicodeError, ContractError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


def _publish_document(repo: Path, issue_number: int, body_path: Path, role: str) -> int:
    try:
        issue = _gitea_from_env().get_issue(issue_number)
        body = body_path.read_text(encoding="utf-8")
        destination = (
            publish_spec(repo, issue, body)
            if role == "spec"
            else publish_plan(repo, issue, body)
        )
        print(destination)
        return 0
    except (GiteaError, OSError, UnicodeError, ContractError) as exc:
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
            "document_slug": result.document_slug,
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

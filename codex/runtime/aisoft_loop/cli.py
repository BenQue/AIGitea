"""Command-line entrypoints for the provider-neutral Loop runtime."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
from typing import Optional

from aisoft_change_name import ChangeName, ChangeNameError
from aisoft_worktree_owner import (
    SESSION_ENV, WorktreeOwnerError, caller_session, claim as claim_worktree,
)

from .analysis import AnalysisError, AnalysisResult, analyze_route, route_labels
from .change_audit import audit_change_documents
from .change_control import resolve_change_control
from .contract import ContractError, resolve_documents, resolve_required_documents
from .documents import backfill_pr_url, publish_plan, publish_spec
from .gitea import GiteaClient, GiteaError
from .worktree import (
    WorktreeError, require_branch, resolve_git_dir, scan_change_worktrees,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="aisoft-loop")
    subparsers = parser.add_subparsers(dest="command", required=True)

    change_name = subparsers.add_parser(
        "change-name", help="validate and print one new readable change branch"
    )
    change_name.add_argument("issue", type=int)
    change_name.add_argument("slug")

    get_issue = subparsers.add_parser("get-issue", help="write one Issue JSON privately")
    get_issue.add_argument("issue", type=int)
    get_issue.add_argument("output", type=Path)

    list_issues = subparsers.add_parser("list-issues", help="list open Issue numbers by label")
    list_issues.add_argument("label")

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

    resolve_routes = subparsers.add_parser("resolve-route", help="resolve concrete provider skills from the policy")
    resolve_routes.add_argument("issue", type=int)
    resolve_routes.add_argument("--repo", required=True, type=Path)
    resolve_routes.add_argument("--provider", required=True, choices=("codex", "claude", "cursor"))

    prepare = subparsers.add_parser("prepare-ticket", help="prepare or resume an exact Txx execution view")
    prepare.add_argument("issue", type=int)
    prepare.add_argument("ticket")
    prepare.add_argument("--repo", required=True, type=Path)
    prepare.add_argument("--provider", required=True, choices=("codex", "claude", "cursor"))
    prepare.add_argument("--resume", action="store_true")

    candidate = subparsers.add_parser("review-candidate", help="inspect a fixed local ticket review candidate")
    candidate.add_argument("issue", type=int)
    candidate.add_argument("ticket")
    candidate.add_argument("--repo", required=True, type=Path)
    candidate.add_argument("--head", required=True)
    candidate.add_argument("--necessary-ignored", action="append", default=[])

    required_document_names = subparsers.add_parser(
        "resolve-required-documents", help="read validated required roles and mapped filenames"
    )
    required_document_names.add_argument("issue", type=int)
    required_document_names.add_argument("--repo", required=True, type=Path)

    backfill = subparsers.add_parser(
        "backfill-pr-url", help="write one change's PR URL into its summary front matter"
    )
    backfill.add_argument("issue", type=int)
    backfill.add_argument("--repo", required=True, type=Path)
    backfill.add_argument("--pr-url", required=True, dest="pr_url")

    check_documents = subparsers.add_parser(
        "check-change-documents",
        help="assert the change document front matter contract across one checkout",
    )
    check_documents.add_argument("--repo", required=True, type=Path)
    check_documents.add_argument(
        "--porcelain",
        action="store_true",
        help="emit name<TAB>status<TAB>detail for tools instead of PASS/GAP lines",
    )

    claim = subparsers.add_parser(
        "claim-worktree",
        help="bind one change worktree to the single session that may write it",
    )
    claim.add_argument("--branch", required=True)
    claim.add_argument(
        "--session",
        help=f"owning session id; defaults to ${SESSION_ENV}",
    )
    claim.add_argument(
        "--worktree",
        type=Path,
        default=Path.cwd(),
        help="the change worktree to claim (default: the current directory)",
    )
    claim.add_argument(
        "--takeover",
        action="store_true",
        help="claim a worktree another session already owns; only after it handed it back",
    )

    scan = subparsers.add_parser(
        "scan-worktrees",
        help="read-only: report every change worktree whose HEAD left its last push",
    )
    scan.add_argument("--repo", required=True, type=Path)
    scan.add_argument(
        "--porcelain",
        action="store_true",
        help="emit branch<TAB>status<TAB>reason<TAB>detail for tools instead of PASS/GAP lines",
    )

    for command, help_text in (
        ("publish-spec", "publish to the Issue's mapped spec path"),
        ("publish-plan", "publish to the Issue's mapped plan path"),
    ):
        publish = subparsers.add_parser(command, help=help_text)
        publish.add_argument("issue", type=int)
        publish.add_argument("body", type=Path)
        publish.add_argument("--repo", required=True, type=Path)

    args = parser.parse_args(argv)
    if args.command == "change-name":
        return _change_name(args.issue, args.slug)
    if args.command == "get-issue":
        return _get_issue(args.issue, args.output)
    if args.command == "list-issues":
        return _list_issues(args.label)
    if args.command == "apply-analysis":
        return _apply_analysis(args.issue, args.result_json, args.summary_url)
    if args.command == "resolve-documents":
        return _resolve_documents(args.repo, args.issue)
    if args.command == "review-candidate":
        from .review_candidate import review_candidate
        try:
            result = review_candidate(args.repo, args.issue, args.ticket, args.head,
                                      necessary_ignored=tuple(args.necessary_ignored))
        except (ContractError, WorktreeOwnerError, WorktreeError, OSError, ValueError) as exc:
            print(f"review candidate refused: {exc}", file=sys.stderr)
            return 2
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    if args.command == "prepare-ticket":
        from .ticket_execution import prepare_ticket
        try:
            result = prepare_ticket(args.repo, args.issue, args.ticket, args.provider, resume=args.resume)
        except (ContractError, WorktreeOwnerError, WorktreeError, OSError, ValueError) as exc:
            print(f"ticket preparation refused: {exc}", file=sys.stderr)
            return 2
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    if args.command == "resolve-route":
        from .route_policy import resolve_issue_route
        try:
            result = resolve_issue_route(args.repo, args.issue, args.provider)
        except (ContractError, OSError, ValueError) as exc:
            print(f"route resolution failed: {exc}", file=sys.stderr)
            return 2
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    if args.command == "resolve-required-documents":
        try:
            resolved = resolve_required_documents(args.repo, args.issue)
        except (ContractError, ChangeNameError, OSError, UnicodeError) as exc:
            print(f"required document resolution failed: {exc}", file=sys.stderr)
            return 2
        print(json.dumps(resolved, ensure_ascii=False, sort_keys=True))
        return 0
    if args.command == "backfill-pr-url":
        return _backfill_pr_url(args.repo, args.issue, args.pr_url)
    if args.command == "check-change-documents":
        return _check_change_documents(args.repo, args.porcelain)
    if args.command == "scan-worktrees":
        return _scan_worktrees(args.repo, args.porcelain)
    if args.command == "claim-worktree":
        return _claim_worktree(
            args.worktree, args.branch, args.session, args.takeover
        )
    if args.command == "publish-spec":
        return _publish_document(args.repo, args.issue, args.body, "spec")
    if args.command == "publish-plan":
        return _publish_document(args.repo, args.issue, args.body, "plan")
    parser.error(f"unknown command: {args.command}")
    return 2


def _backfill_pr_url(repo: Path, issue: int, pr_url: str) -> int:
    try:
        summary_path, changed = backfill_pr_url(repo, issue, pr_url)
    except (ContractError, ChangeNameError, OSError, UnicodeError) as exc:
        print(f"pr_url backfill refused: {exc}", file=sys.stderr)
        return 2
    print(f"{'changed' if changed else 'unchanged'} {summary_path}")
    return 0


def _claim_worktree(
    worktree: Path, branch: str, session: Optional[str], takeover: bool
) -> int:
    resolved_session = (session or caller_session()).strip()
    if not resolved_session:
        print(
            f"claim refused: pass --session or set ${SESSION_ENV}",
            file=sys.stderr,
        )
        return 2
    try:
        require_branch(worktree, branch)
        git_dir = resolve_git_dir(worktree)
        marker, result = claim_worktree(
            git_dir,
            branch=branch,
            session=resolved_session,
            worktree=worktree,
            takeover=takeover,
        )
    except (WorktreeOwnerError, WorktreeError, OSError) as exc:
        code = exc.code if isinstance(exc, WorktreeOwnerError) else "CLAIM_FAILED"
        print(f"claim refused: {code}: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({
        "branch": marker.branch,
        "issue": marker.issue,
        "last_push_head": marker.last_push_head,
        "result": result,
        "session": marker.session,
        "worktree": marker.worktree,
    }, ensure_ascii=False, sort_keys=True))
    return 0


def _scan_worktrees(repo: Path, porcelain: bool) -> int:
    try:
        entries = scan_change_worktrees(repo)
    except (WorktreeError, OSError) as exc:
        print(f"worktree scan failed: {exc}", file=sys.stderr)
        return 2
    for entry in entries:
        status = "PASS" if entry.ok else "GAP"
        if porcelain:
            print(f"{entry.branch}\t{status}\t{entry.reason}\t{entry.detail}")
        else:
            print(
                f"{status}: {entry.branch} [{entry.reason}] {entry.worktree}\n"
                f"      head={entry.head or '-'} "
                f"last_push={entry.last_push_head or '-'} "
                f"session={entry.session or '-'}\n"
                f"      {entry.detail}"
            )
    gaps = sum(1 for entry in entries if not entry.ok)
    if not porcelain:
        print(
            f"result: worktrees={len(entries)} pass={len(entries) - gaps} gap={gaps}"
        )
    return 0 if gaps == 0 else 1


def _check_change_documents(repo: Path, porcelain: bool) -> int:
    try:
        report = audit_change_documents(repo)
    except OSError as exc:
        print(f"change document audit failed: {exc}", file=sys.stderr)
        return 2
    for check in report.checks:
        detail = "; ".join(check.problems)
        if porcelain:
            # Tab separated so aisoft-project-check.sh can split it without
            # guessing where a Chinese-punctuated detail string ends.
            print(f"{check.name}\t{'PASS' if check.ok else 'GAP'}\t{detail}")
        elif check.ok:
            print(f"PASS: {check.name}")
        else:
            print(f"GAP: {check.name} — {detail}")
        if check.legacy:
            # Registered history (#409): reported, never counted as a gap.
            registered = f"登记 {len(check.legacy)} 项：" + "; ".join(check.legacy)
            if porcelain:
                print(f"{check.name}\tLEGACY\t{registered}")
            else:
                print(f"LEGACY: {check.name} — {registered}")
    if not porcelain:
        gaps = sum(1 for check in report.checks if not check.ok)
        print(
            f"result: changes={report.change_count} "
            f"pass={len(report.checks) - gaps} gap={gaps}"
        )
    return 0 if report.ok else 1


def _change_name(issue_number: int, slug: str) -> int:
    try:
        print(ChangeName.new(issue_number, slug).branch)
    except ChangeNameError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 0


def _get_issue(issue_number: int, output_path: Path) -> int:
    try:
        gitea = _gitea_from_env()
        issue = gitea.get_issue(issue_number)
        # #180: the raw Issue object's `comments` is only a count. The analyzer
        # reads this file as its whole view of the Issue, so the thread rides
        # along under its own key; the count stays untouched for consumers
        # that already read it. Same read-only project-agent token, one more
        # GET per 50 comments — no new credential path and no write.
        issue["issue_comments"] = gitea.list_issue_comments(issue_number)
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


def _apply_analysis(issue_number: int, result_path: Path, summary_url: str) -> int:
    try:
        gitea = _gitea_from_env()
        issue = gitea.get_issue(issue_number)
        result = AnalysisResult.from_json(result_path.read_text(encoding="utf-8"))
        route = analyze_route(
            issue,
            result,
            change_control=resolve_change_control(_required_env("GITEA_REPO")),
        )
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


if __name__ == "__main__":
    raise SystemExit(main())

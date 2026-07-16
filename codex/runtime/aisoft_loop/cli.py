"""Command-line entrypoints for the provider-neutral Loop runtime."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

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

    args = parser.parse_args(argv)
    if args.command == "validate-provider":
        return _validate_provider(args.input, args.output)
    return _run(args.issue, args.repo, args.verification_config)


def _run(issue: int, repo: Path, verification_config: Path) -> int:
    required_env = ("GITEA_URL", "GITEA_OWNER", "GITEA_REPO", "GITEA_TOKEN")
    missing = [name for name in required_env if not os.environ.get(name)]
    if missing:
        print("missing required environment: " + ", ".join(missing), file=sys.stderr)
        return 2
    state_root = Path(os.environ.get("AISOFT_LOOP_STATE_DIR") or default_state_root())
    provider_script = Path(
        os.environ.get("CODEX_PROVIDER_SCRIPT")
        or Path(__file__).parents[2] / "agent" / "codex-provider.sh"
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


if __name__ == "__main__":
    raise SystemExit(main())

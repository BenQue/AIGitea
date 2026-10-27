"""`aisoft-access`: the project-declared entry of the typed access engine (#434).

Same --operation surface as the site broker, minus --project: the project is the
one `.aisoft/project.json` in the current checkout declares. Output and error
shapes match the site broker so callers do not care which source answered.
"""
from __future__ import annotations

import argparse
import json
import sys

from .broker import BrokerError, ReadCollection
from .cli import _json, _validate_scope, _receipt_error
from .project_source import ProjectSourceBroker, load_project_declaration


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="aisoft-access")
    # Fixed by the entry script, never by the caller.
    parser.add_argument("--label-manifest", required=True)
    parser.add_argument("--operation", required=True)
    for name in ("--reference", "--branch", "--title", "--body", "--comment", "--sha",
                 "--entry-label", "--lifecycle", "--change-type", "--complexity",
                 "--label", "--color", "--description", "--token-kind"):
        parser.add_argument(name)
    parser.add_argument("--number", type=int)
    parser.add_argument("--issue", type=int)
    parser.add_argument("--job", type=int)
    parser.add_argument("--state", choices=("open", "closed", "all"))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        declaration = load_project_declaration(".")
        broker = ProjectSourceBroker(declaration, label_manifest_path=args.label_manifest)
        arguments = {
            key: getattr(args, key) for key in (
                "number", "state", "branch", "issue", "title", "body", "comment", "sha", "job",
                "entry_label", "lifecycle", "change_type", "complexity", "label", "color",
                "description", "token_kind",
            )
        }
        if args.reference is not None:
            arguments["reference"] = args.reference
        value = broker.execute(None, args.operation, **arguments)
        if args.operation == "gitea.pulls.read":
            if not isinstance(value, ReadCollection):
                raise _receipt_error()
            _validate_scope(value.read_receipt, broker.contract,
                            broker.contract.projects[0], args.operation)
            if value.read_receipt.get("state") != args.state:
                raise _receipt_error()
        _json(value)
        return 0
    except (BrokerError, OSError, ValueError) as exc:
        code = exc.code if isinstance(exc, BrokerError) else "CONTRACT_INVALID"
        print(json.dumps({"status": "BLOCKED_EXTERNAL", "code": code, "message": str(exc)},
                         ensure_ascii=False, sort_keys=True), file=sys.stderr)
        return 20


if __name__ == "__main__":
    raise SystemExit(main())

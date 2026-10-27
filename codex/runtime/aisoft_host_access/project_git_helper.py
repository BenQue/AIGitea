"""Git credential helper of the project-declared source (#434, ADR 0003).

Git runs it as `<python> -I project_git_helper.py SECRET PROTOCOL HOST PATH get`.
It answers only a `get` for exactly the declared remote — same protocol, host
with port, and repository path — by printing the mode-600 credential file the
engine wrote for this one call. Any other request gets no credential, so a
redirect or a second remote can never receive it.
"""
from __future__ import annotations

import sys


def main(argv: list[str]) -> int:
    if len(argv) != 6:
        return 0
    secret, protocol, host, path, action = argv[1:]
    if action != "get":
        return 0
    fields: dict[str, str] = {}
    for line in sys.stdin.read().splitlines():
        key, sep, value = line.partition("=")
        if sep:
            fields[key] = value
    if (fields.get("protocol"), fields.get("host"), fields.get("path", "").lstrip("/")) != (protocol, host, path):
        return 0
    with open(secret, encoding="utf-8") as handle:
        sys.stdout.write(handle.read())
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

#!/usr/bin/env bash
set -euo pipefail
root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.." && pwd)"
case "${1:---not-run}" in
  --not-run) action=not-run ;;
  --preflight) action=preflight ;;
  --identity-precheck) action=identity ;;
  *) printf '%s\n' 'BLOCKED: valid modes: --not-run --preflight --identity-precheck' >&2; exit 2 ;;
esac
if (($#)); then shift; fi
exec python3 -B "$root/codex/tests/integration/docker28-classic-driver.py" "$action" "$@"

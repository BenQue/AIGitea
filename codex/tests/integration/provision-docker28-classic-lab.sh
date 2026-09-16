#!/usr/bin/env bash
set -euo pipefail
root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.." && pwd)"
exec python3 -B "$root/codex/tests/integration/docker28-classic-driver.py" "${@:-not-run}"

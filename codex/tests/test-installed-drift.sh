#!/usr/bin/env bash
# Fixture-only acceptance: never accesses this host's real installation surface.
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
exec python3 -B "$ROOT/codex/tests/fixtures/installed-drift/test-installed-drift.py" "$ROOT"

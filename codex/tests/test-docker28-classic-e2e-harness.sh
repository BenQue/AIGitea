#!/usr/bin/env bash
set -euo pipefail
root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
result="$(bash "$root/codex/tests/integration/test-docker28-classic-e2e.sh")"
[[ "$result" == *'NOT RUN'* ]]
if env -u AISOFT_296_APPROVED bash "$root/codex/tests/integration/test-docker28-classic-e2e.sh" --preflight >/dev/null 2>&1; then
  printf '%s\n' 'FAIL: unapproved preflight accepted' >&2
  exit 1
fi
python3 -B -m unittest discover -s "$root/codex/runtime/tests" -p test_release_docker28_compatibility.py
for file in "$root/codex/tests/integration/test-docker28-classic-e2e.sh" \
  "$root/codex/tests/integration/provision-docker28-classic-lab.sh" \
  "$root/codex/tests/fixtures/docker28-classic/install-daemon.sh" \
  "$root/codex/tests/fixtures/docker28-classic/migrate.sh"; do
  bash -n "$file"
done
printf '%s\n' 'PASS: Issue #296 static/fake safety gates; real acceptance NOT RUN'

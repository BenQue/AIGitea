#!/usr/bin/env bash
set -euo pipefail

root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
harness="$root/codex/tests/integration/test-company-delivery-real-release.sh"

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

default_output="$(bash "$harness")"
grep -Fq \
  'NOT RUN: Issue #124 exact real-release regression requires explicit --execute.' \
  <<<"$default_output" || fail 'default invocation must remain NOT RUN'
grep -Fq 'No Docker, target, network, deployment' <<<"$default_output" ||
  fail 'default invocation must state the execution boundary'

if bash "$harness" --execute \
  --repository-root relative --release-root relative \
  --release-id 006d0c43cafebff058889e3338d1e8bdcc8b661c \
  >/dev/null 2>&1; then
  fail 'relative input roots must fail before any release operation'
fi
if bash "$harness" --execute \
  --repository-root "$root" --release-root /tmp \
  --release-id 1111111111111111111111111111111111111111 \
  >/dev/null 2>&1; then
  fail 'a non-approved release ID must fail before any release operation'
fi

grep -Fq 'status --porcelain --untracked-files=all' "$harness" ||
  fail 'harness must require and preserve a clean candidate'
grep -Fq 'inspect_offline_artifact' \
  "$root/codex/runtime/aisoft_company_delivery/bundle.py" ||
  fail 'builder must consume the canonical verified graph seam'
grep -Fq 'docker_calls") == 0' "$harness" ||
  fail 'harness must assert zero Docker calls'
grep -Fq 'target_facts") == "NOT_READ"' "$harness" ||
  fail 'harness must assert target facts are not read'
grep -Fq 'input_fingerprint_before' "$harness" ||
  fail 'harness must fingerprint the exact input before both builds'
grep -Fq 'input_fingerprint_after' "$harness" ||
  fail 'harness must fingerprint the exact input after both builds'
grep -Fq 'post-build artifact-only verification failed' "$harness" ||
  fail 'harness must revalidate all artifact checksums after both builds'
grep -Fq 'aisoft-issue124-one.XXXXXX' "$harness" ||
  fail 'harness must create a distinct first temporary output'
grep -Fq 'aisoft-issue124-two.XXXXXX' "$harness" ||
  fail 'harness must create a distinct second temporary output'
grep -Fq 'rm -rf -- "$path"' "$harness" ||
  fail 'harness must clean only its validated temporary outputs'

printf '%s\n' 'PASS: Issue #124 real-release harness default/guard contract'

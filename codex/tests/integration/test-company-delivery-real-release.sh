#!/usr/bin/env bash
set -euo pipefail

expected_release_id="006d0c43cafebff058889e3338d1e8bdcc8b661c"
expected_base_sha="7950d119ab5c949d914de172dac8606369483cd4"
expected_branch="change/124-secret-scan-false-positive"
created_at="2026-08-16T08:00:00Z"
mode="${1:---not-run}"

fail() {
  printf '%s\n' "BLOCKED: $1" >&2
  exit 1
}

not_run() {
  printf '%s\n' \
    'NOT RUN: Issue #124 exact real-release regression requires explicit --execute.'
  printf '%s\n' \
    'No Docker, target, network, deployment, Secret, database, service or timer action was run.'
}

file_mode() {
  stat -c '%a' "$1" 2>/dev/null || stat -f '%Lp' "$1"
}

json_assert_artifact() {
  python3 -c '
import json, sys
value = json.load(sys.stdin)
valid = (
    value.get("ok") is True
    and value.get("contract_version") == "docker-release/v2"
    and value.get("docker_calls") == 0
    and value.get("target_facts") == "NOT_READ"
)
raise SystemExit(0 if valid else 1)
'
}

json_assert_handoff() {
  python3 -c '
import json, sys
value = json.load(sys.stdin)
valid = (
    value.get("ok") is True
    and value.get("contract_version") == "company-delivery-handoff/v1"
    and value.get("docker_calls") == 0
    and value.get("target_facts") == "NOT_READ"
)
raise SystemExit(0 if valid else 1)
'
}

json_field() {
  local field="$1"
  python3 -c '
import json, sys
field = sys.argv[1]
value = json.load(sys.stdin).get(field)
if not isinstance(value, str) or not value:
    raise SystemExit(1)
print(value)
' "$field"
}

if [[ "$mode" == "--not-run" ]]; then
  [[ "$#" -eq 0 || "$#" -eq 1 ]] || fail 'unexpected arguments for --not-run'
  not_run
  exit 0
fi
[[ "$mode" == "--execute" ]] ||
  fail 'usage: test-company-delivery-real-release.sh [--not-run|--execute --repository-root ABS --release-root ABS --release-id FULL_SHA]'
shift

repository_root=""
release_root=""
release_id=""
while [[ "$#" -gt 0 ]]; do
  case "$1" in
    --repository-root)
      [[ "$#" -ge 2 ]] || fail 'missing repository root'
      repository_root="$2"
      shift 2
      ;;
    --release-root)
      [[ "$#" -ge 2 ]] || fail 'missing release root'
      release_root="$2"
      shift 2
      ;;
    --release-id)
      [[ "$#" -ge 2 ]] || fail 'missing release ID'
      release_id="$2"
      shift 2
      ;;
    *) fail 'unexpected execute argument' ;;
  esac
done

[[ "$repository_root" == /* && "$release_root" == /* ]] ||
  fail 'repository and release roots must be absolute'
[[ "$release_id" == "$expected_release_id" ]] ||
  fail 'release ID does not match the approved exact release'
[[ -d "$repository_root" && ! -L "$repository_root" ]] ||
  fail 'repository root must be a non-symlink directory'
[[ -d "$release_root" && ! -L "$release_root" ]] ||
  fail 'release root must be a non-symlink directory'

repository_root="$(cd -P -- "$repository_root" && pwd -P)"
release_root="$(cd -P -- "$release_root" && pwd -P)"
[[ "$release_root" != "$repository_root" &&
  "$release_root" != "$repository_root/"* ]] ||
  fail 'release root must remain outside the candidate repository'

for command in git mktemp python3 rm stat; do
  command -v "$command" >/dev/null 2>&1 || fail 'required local command is unavailable'
done

[[ "$(git -C "$repository_root" rev-parse --show-toplevel)" == "$repository_root" ]] ||
  fail 'repository root does not match Git top level'
[[ "$(git -C "$repository_root" branch --show-current)" == "$expected_branch" ]] ||
  fail 'candidate branch does not match Issue #124 tuple'
git -C "$repository_root" merge-base --is-ancestor \
  "$expected_base_sha" HEAD || fail 'candidate does not descend from approved main'
[[ -z "$(git -C "$repository_root" status --porcelain --untracked-files=all)" ]] ||
  fail 'candidate repository must be clean'
source_sha="$(git -C "$repository_root" rev-parse HEAD)"
[[ "$source_sha" =~ ^[0-9a-f]{40}$ ]] || fail 'candidate HEAD is not a full Git SHA'

docker_release="$repository_root/docker-release/bin/aisoft-docker-release"
company_delivery="$repository_root/company-delivery/bin/aisoft-company-delivery"
[[ -x "$docker_release" && -x "$company_delivery" ]] ||
  fail 'candidate operator entrypoints are unavailable'

artifact_json="$(
  AISOFT_DOCKER_RELEASE_RUNTIME_DIR="$repository_root/codex/runtime" \
    "$docker_release" verify-artifact \
    --release-root "$release_root" --release-id "$release_id"
)" || fail 'artifact-only verification failed'
json_assert_artifact <<<"$artifact_json" ||
  fail 'artifact-only verification crossed its fixed boundary'

temp_parent="$(cd -P -- "${TMPDIR:-/tmp}" && pwd -P)"
output_one=""
output_two=""
cleanup() {
  local path
  for path in "$output_one" "$output_two"; do
    if [[ -n "$path" && -d "$path" &&
      "$path" == "$temp_parent/aisoft-issue124-"* ]]; then
      rm -rf -- "$path"
    fi
  done
}
trap cleanup EXIT

umask 077
output_one="$(mktemp -d "$temp_parent/aisoft-issue124-one.XXXXXX")"
output_two="$(mktemp -d "$temp_parent/aisoft-issue124-two.XXXXXX")"
[[ "$(file_mode "$output_one")" == "700" &&
  "$(file_mode "$output_two")" == "700" ]] ||
  fail 'temporary output directories must use mode 0700'

build_one="$(
  "$company_delivery" build-bundle \
    --repository-root "$repository_root" \
    --source-sha "$source_sha" \
    --release-root "$release_root" \
    --release-id "$release_id" \
    --output-directory "$output_one" \
    --created-at "$created_at" \
    --source-transport approved-bundle
)" || fail 'first deterministic bundle build failed'
build_two="$(
  "$company_delivery" build-bundle \
    --repository-root "$repository_root" \
    --source-sha "$source_sha" \
    --release-root "$release_root" \
    --release-id "$release_id" \
    --output-directory "$output_two" \
    --created-at "$created_at" \
    --source-transport approved-bundle
)" || fail 'second deterministic bundle build failed'

checksum_one="$(json_field archive_sha256 <<<"$build_one")" ||
  fail 'first build result is invalid'
checksum_two="$(json_field archive_sha256 <<<"$build_two")" ||
  fail 'second build result is invalid'
bundle_one="$(json_field bundle_name <<<"$build_one")" ||
  fail 'first bundle identity is invalid'
bundle_two="$(json_field bundle_name <<<"$build_two")" ||
  fail 'second bundle identity is invalid'
[[ "$checksum_one" =~ ^[0-9a-f]{64}$ && "$checksum_one" == "$checksum_two" ]] ||
  fail 'deterministic archive checksums differ'
[[ "$bundle_one" == "$bundle_two" &&
  "$bundle_one" =~ ^aisoft-company-delivery-1\.0\.1-[0-9a-f]{40}$ ]] ||
  fail 'bundle identities are inconsistent'

verify_one="$(
  "$company_delivery" verify-handoff \
    --manifest "$output_one/$bundle_one/handoff-manifest.json" \
    --bundle-root "$output_one/$bundle_one"
)" || fail 'first handoff verification failed'
verify_two="$(
  "$company_delivery" verify-handoff \
    --manifest "$output_two/$bundle_two/handoff-manifest.json" \
    --bundle-root "$output_two/$bundle_two"
)" || fail 'second handoff verification failed'
json_assert_handoff <<<"$verify_one" || fail 'first handoff result is invalid'
json_assert_handoff <<<"$verify_two" || fail 'second handoff result is invalid'

[[ -z "$(git -C "$repository_root" status --porcelain --untracked-files=all)" ]] ||
  fail 'candidate repository changed during exact release regression'
cleanup
trap - EXIT
[[ ! -e "$output_one" && ! -e "$output_two" ]] ||
  fail 'temporary bundle outputs were not removed'

printf '%s\n' \
  'PASS: artifact-only docker-release/v2; docker_calls=0; target_facts=NOT_READ'
printf 'PASS: source_sha=%s release_id=%s\n' "$source_sha" "$release_id"
printf 'PASS: deterministic_archive_sha256=%s verify_handoff=2/2 cleanup=PASS\n' \
  "$checksum_one"

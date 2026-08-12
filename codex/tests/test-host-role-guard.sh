#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
GUARD="$ROOT/codex/tools/verify-host-role.sh"
SCHEMA="$ROOT/codex/config/host-role.schema.json"
CATALOG="$ROOT/codex/config/host-capabilities.json"
FIXTURES="$ROOT/codex/tests/fixtures/host-role"
TMP="$(mktemp -d)"
trap 'rm -rf -- "$TMP"' EXIT

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

run_guard() (
  local profile="$1"
  local fixture_hostname="$2"
  local fixture_host_id="$3"
  local profile_mode="$4"
  shift 4

  # Source the implementation so deterministic fixtures can replace only OS
  # identity/stat probes. The installed CLI exposes no profile or identity override.
  # shellcheck source=/dev/null
  source "$GUARD"
  # These globals/functions are consumed dynamically by the sourced guard.
  # shellcheck disable=SC2034
  PROFILE_PATH="$profile"
  # shellcheck disable=SC2034
  SCHEMA_PATH="${TEST_SCHEMA_PATH:-$SCHEMA}"
  # shellcheck disable=SC2034
  CATALOG_PATH="${TEST_CATALOG_PATH:-$CATALOG}"
  # shellcheck disable=SC2329
  path_uid_mode() {
    case "$1" in
      "$profile") printf '0 %s\n' "$profile_mode" ;;
      *) printf '0 644\n' ;;
    esac
  }
  # shellcheck disable=SC2329
  path_is_readable() { [[ "$1" != "${TEST_UNREADABLE_PATH:-}" ]]; }
  # shellcheck disable=SC2329
  read_actual_hostname() { printf '%s\n' "$fixture_hostname"; }
  # shellcheck disable=SC2329
  read_actual_host_id() { printf '%s\n' "$fixture_host_id"; }
  verify_host_role_main "$@"
)

jq empty "$SCHEMA" "$CATALOG" "$FIXTURES"/*.json >/dev/null ||
  fail 'host-role schema, catalog and fixtures must be valid JSON'
jq -e '.properties.contract_version.const == "1.0"' "$SCHEMA" >/dev/null ||
  fail 'host-role schema contract version must be 1.0'
jq -e '.contract_version == "1.0" and (.roles | length == 3)' "$CATALOG" >/dev/null ||
  fail 'host-role catalog must contain the exact v1 role set'

valid="$FIXTURES/valid-scm-ci.json"
set +e
allow_one="$(run_guard "$valid" fixture-scm-ci \
  aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa 640 --action run --resource build 2>&1)"
allow_one_status=$?
set -e
[[ "$allow_one_status" == 0 ]] ||
  fail "build allow probe returned $allow_one_status instead of 0"
grep -Fxq \
  'decision=allow host=fixture-scm-ci role=scm-ci action=run resource=build' \
  <<<"$allow_one" || fail 'build allow probe returned an unexpected decision'
set +e
allow_two="$(run_guard "$valid" fixture-scm-ci \
  aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa 640 --action run --resource build 2>&1)"
allow_two_status=$?
set -e
[[ "$allow_two_status" == 0 ]] ||
  fail "repeated build allow probe returned $allow_two_status instead of 0"
[[ "$allow_one" == "$allow_two" ]] || fail 'allow decisions must be deterministic'

set +e
deny_output="$(run_guard "$valid" fixture-scm-ci \
  aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa 640 --action start --resource application 2>&1)"
deny_status=$?
set -e
[[ "$deny_status" == 20 ]] ||
  fail "application start deny probe returned $deny_status instead of 20"
grep -Fxq \
  'decision=deny host=fixture-scm-ci role=scm-ci action=start resource=application' \
  <<<"$deny_output" || fail 'application start deny probe returned an unexpected decision'

set +e
unknown_output="$(run_guard "$valid" fixture-scm-ci \
  aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa 640 --action launch --resource application 2>&1)"
unknown_status=$?
set -e
[[ "$unknown_status" == 30 ]] ||
  fail "unknown capability probe returned $unknown_status instead of 30"
grep -Fq 'decision=invalid-profile reason=unknown-action-resource-pair' \
  <<<"$unknown_output" || fail 'unknown capability probe returned an unexpected reason'

set +e
identity_output="$(run_guard "$valid" wrong-host \
  aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa 640 --action run --resource build 2>&1)"
identity_status=$?
set -e
[[ "$identity_status" == 40 ]] ||
  fail "identity mismatch probe returned $identity_status instead of 40"
grep -Fq 'decision=identity-mismatch reason=hostname-mismatch' \
  <<<"$identity_output" || fail 'identity mismatch probe returned an unexpected reason'

set +e
permission_output="$(run_guard "$valid" fixture-scm-ci \
  aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa 666 --action run --resource build 2>&1)"
permission_status=$?
set -e
[[ "$permission_status" == 30 ]] ||
  fail "profile mode probe returned $permission_status instead of 30"
grep -Fq 'decision=invalid-profile reason=profile-path-owner-or-mode' \
  <<<"$permission_output" || fail 'profile mode probe returned an unexpected reason'

for unreadable_kind in profile schema catalog; do
  case "$unreadable_kind" in
    profile) unreadable_path="$valid" ;;
    schema) unreadable_path="$SCHEMA" ;;
    catalog) unreadable_path="$CATALOG" ;;
  esac
  set +e
  unreadable_output="$(
    TEST_UNREADABLE_PATH="$unreadable_path" \
      run_guard "$valid" fixture-scm-ci \
        aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa 640 --action run --resource build 2>&1
  )"
  unreadable_status=$?
  set -e
  [[ "$unreadable_status" == 30 ]] ||
    fail "$unreadable_kind unreadable probe returned $unreadable_status instead of 30"
  grep -Fxq "decision=invalid-profile reason=${unreadable_kind}-permission-denied" \
    <<<"$unreadable_output" ||
    fail "$unreadable_kind unreadable probe returned an unexpected reason"
done

malformed_marker='MALFORMED_JSON_MARKER_MUST_NOT_LEAK_97'
malformed_profile="$TMP/malformed-profile.json"
malformed_schema="$TMP/malformed-schema.json"
malformed_catalog="$TMP/malformed-catalog.json"
printf '{"marker":"%s"' "$malformed_marker" >"$malformed_profile"
printf '{"marker":"%s"' "$malformed_marker" >"$malformed_schema"
printf '{"marker":"%s"' "$malformed_marker" >"$malformed_catalog"

for malformed_kind in profile schema catalog; do
  test_schema_path="$SCHEMA"
  test_catalog_path="$CATALOG"
  case "$malformed_kind" in
    profile) malformed_path="$malformed_profile" ;;
    schema)
      malformed_path="$valid"
      test_schema_path="$malformed_schema"
      ;;
    catalog)
      malformed_path="$valid"
      test_catalog_path="$malformed_catalog"
      ;;
  esac
  set +e
  malformed_output="$(
    TEST_SCHEMA_PATH="$test_schema_path" TEST_CATALOG_PATH="$test_catalog_path" \
      run_guard "$malformed_path" fixture-scm-ci \
        aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa 640 --action run --resource build 2>&1
  )"
  malformed_status=$?
  set -e
  [[ "$malformed_status" == 30 ]] ||
    fail "$malformed_kind malformed JSON probe returned $malformed_status instead of 30"
  grep -Fxq "decision=invalid-profile reason=${malformed_kind}-invalid-json" \
    <<<"$malformed_output" ||
    fail "$malformed_kind malformed JSON probe returned an unexpected reason"
  if grep -Fq "$malformed_marker" <<<"$malformed_output"; then
    fail "$malformed_kind malformed JSON probe leaked input content"
  fi
done

empty_json="$TMP/empty.json"
whitespace_json="$TMP/whitespace.json"
: >"$empty_json"
printf ' \t\n' >"$whitespace_json"

for blank_variant in empty whitespace; do
  case "$blank_variant" in
    empty) blank_path="$empty_json" ;;
    whitespace) blank_path="$whitespace_json" ;;
  esac
  for blank_kind in profile schema catalog; do
    test_schema_path="$SCHEMA"
    test_catalog_path="$CATALOG"
    case "$blank_kind" in
      profile) blank_profile_path="$blank_path" ;;
      schema)
        blank_profile_path="$valid"
        test_schema_path="$blank_path"
        ;;
      catalog)
        blank_profile_path="$valid"
        test_catalog_path="$blank_path"
        ;;
    esac
    set +e
    blank_output="$(
      TEST_SCHEMA_PATH="$test_schema_path" TEST_CATALOG_PATH="$test_catalog_path" \
        run_guard "$blank_profile_path" fixture-scm-ci \
          aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa 640 --action run --resource build 2>&1
    )"
    blank_status=$?
    set -e
    [[ "$blank_status" == 30 ]] ||
      fail "$blank_kind $blank_variant JSON probe returned $blank_status instead of 30"
    grep -Fxq "decision=invalid-profile reason=${blank_kind}-invalid-json" \
      <<<"$blank_output" ||
      fail "$blank_kind $blank_variant JSON probe returned an unexpected reason"
  done
done

for invalid_profile in \
  "$FIXTURES/invalid-missing-host-id.json" \
  "$FIXTURES/invalid-unknown-capability.json"; do
  set +e
  invalid_output="$(run_guard "$invalid_profile" fixture-scm-ci \
    aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa 640 --action run --resource build 2>&1)"
  invalid_status=$?
  set -e
  [[ "$invalid_status" == 30 ]] ||
    fail "invalid fixture $(basename "$invalid_profile") returned $invalid_status instead of 30"
  grep -Fq 'decision=invalid-profile' <<<"$invalid_output" ||
    fail "invalid fixture $(basename "$invalid_profile") returned an unexpected decision"
done

redacted_profile="$TMP/redacted.json"
secret_marker='SECRET_MARKER_MUST_NOT_LEAK_21'
jq --arg marker "$secret_marker" '.secret = $marker' "$valid" >"$redacted_profile"
set +e
redacted_output="$(run_guard "$redacted_profile" fixture-scm-ci \
  aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa 640 --action run --resource build 2>&1)"
redacted_status=$?
set -e
[[ "$redacted_status" == 30 ]] ||
  fail "unexpected profile field probe returned $redacted_status instead of 30"
if grep -Fq "$secret_marker" <<<"$redacted_output"; then
  fail 'guard leaked an unexpected profile value'
fi

mutation_marker="$TMP/mutated"
set +e
run_guard "$valid" fixture-scm-ci \
  aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa 640 \
  --action start --resource application >/dev/null 2>&1
mutation_status=$?
set -e
if [[ "$mutation_status" == 0 ]]; then
  : >"$mutation_marker"
fi
[[ "$mutation_status" == 20 ]] ||
  fail "guarded mutation probe returned $mutation_status instead of 20"
[[ ! -e "$mutation_marker" ]] || fail 'denied guard decision reached the mutation marker'

printf '%s\n' 'host-role guard tests passed'

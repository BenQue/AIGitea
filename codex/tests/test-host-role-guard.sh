#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
GUARD="$ROOT/codex/tools/verify-host-role.sh"
SCHEMA="$ROOT/codex/config/host-role.schema.json"
CATALOG="$ROOT/codex/config/host-capabilities.json"
FIXTURES="$ROOT/codex/tests/fixtures/host-role"
TMP="$(mktemp -d)"
trap 'rm -rf -- "$TMP"' EXIT

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
  SCHEMA_PATH="$SCHEMA"
  # shellcheck disable=SC2034
  CATALOG_PATH="$CATALOG"
  # shellcheck disable=SC2329
  path_uid_mode() {
    case "$1" in
      "$profile") printf '0 %s\n' "$profile_mode" ;;
      *) printf '0 644\n' ;;
    esac
  }
  # shellcheck disable=SC2329
  read_actual_hostname() { printf '%s\n' "$fixture_hostname"; }
  # shellcheck disable=SC2329
  read_actual_host_id() { printf '%s\n' "$fixture_host_id"; }
  verify_host_role_main "$@"
)

jq empty "$SCHEMA" "$CATALOG" "$FIXTURES"/*.json >/dev/null
jq -e '.properties.contract_version.const == "1.0"' "$SCHEMA" >/dev/null
jq -e '.contract_version == "1.0" and (.roles | length == 3)' "$CATALOG" >/dev/null

valid="$FIXTURES/valid-scm-ci.json"
allow_one="$(run_guard "$valid" fixture-scm-ci \
  aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa 640 --action run --resource build)"
grep -Fxq \
  'decision=allow host=fixture-scm-ci role=scm-ci action=run resource=build' \
  <<<"$allow_one"
allow_two="$(run_guard "$valid" fixture-scm-ci \
  aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa 640 --action run --resource build)"
[[ "$allow_one" == "$allow_two" ]]

set +e
deny_output="$(run_guard "$valid" fixture-scm-ci \
  aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa 640 --action start --resource application 2>&1)"
deny_status=$?
set -e
[[ "$deny_status" == 20 ]]
grep -Fxq \
  'decision=deny host=fixture-scm-ci role=scm-ci action=start resource=application' \
  <<<"$deny_output"

set +e
unknown_output="$(run_guard "$valid" fixture-scm-ci \
  aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa 640 --action launch --resource application 2>&1)"
unknown_status=$?
set -e
[[ "$unknown_status" == 30 ]]
grep -Fq 'decision=invalid-profile reason=unknown-action-resource-pair' \
  <<<"$unknown_output"

set +e
identity_output="$(run_guard "$valid" wrong-host \
  aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa 640 --action run --resource build 2>&1)"
identity_status=$?
set -e
[[ "$identity_status" == 40 ]]
grep -Fq 'decision=identity-mismatch reason=hostname-mismatch' \
  <<<"$identity_output"

set +e
permission_output="$(run_guard "$valid" fixture-scm-ci \
  aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa 666 --action run --resource build 2>&1)"
permission_status=$?
set -e
[[ "$permission_status" == 30 ]]
grep -Fq 'decision=invalid-profile reason=profile-path-owner-or-mode' \
  <<<"$permission_output"

for invalid_profile in \
  "$FIXTURES/invalid-missing-host-id.json" \
  "$FIXTURES/invalid-unknown-capability.json"; do
  set +e
  invalid_output="$(run_guard "$invalid_profile" fixture-scm-ci \
    aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa 640 --action run --resource build 2>&1)"
  invalid_status=$?
  set -e
  [[ "$invalid_status" == 30 ]]
  grep -Fq 'decision=invalid-profile' <<<"$invalid_output"
done

redacted_profile="$TMP/redacted.json"
secret_marker='SECRET_MARKER_MUST_NOT_LEAK_21'
jq --arg marker "$secret_marker" '.secret = $marker' "$valid" >"$redacted_profile"
set +e
redacted_output="$(run_guard "$redacted_profile" fixture-scm-ci \
  aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa 640 --action run --resource build 2>&1)"
redacted_status=$?
set -e
[[ "$redacted_status" == 30 ]]
if grep -Fq "$secret_marker" <<<"$redacted_output"; then
  echo 'guard leaked an unexpected profile value' >&2
  exit 1
fi

mutation_marker="$TMP/mutated"
set +e
(
  run_guard "$valid" fixture-scm-ci \
    aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa 640 \
    --action start --resource application
  : >"$mutation_marker"
) >/dev/null 2>&1
mutation_status=$?
set -e
[[ "$mutation_status" == 20 ]]
[[ ! -e "$mutation_marker" ]]

printf '%s\n' 'host-role guard tests passed'

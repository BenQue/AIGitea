#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf -- "$TMP"' EXIT

PYTHONPATH="$ROOT/codex/runtime" python3 -m aisoft_host_access.cli \
  --access-manifest "$ROOT/codex/config/host-access-broker.json" \
  --governance-manifest "$ROOT/codex/config/gitea-governance.json" \
  validate >"$TMP/validate.json"
jq -e '
  .status == "PASS" and
  .contract_version == "host-access-broker/v1" and
  .project_count == 9 and
  .operation_count == 13 and
  .merge_operation_count == 0
' "$TMP/validate.json" >/dev/null

jq -e '
  ([.operations[].name] | length == 13) and
  all(.operations[];
    (.name | contains("merge") | not) and
    (.name | contains("shell") | not) and
    (.name | contains("url") | not)) and
  .human_merge_identity == "admin" and
  .identity_bindings.manager_audit.identity == "aisoft-platform-manager" and
  .identity_bindings.manager_mutation.identity == "aisoft-platform-manager" and
  .identity_bindings.project_agent.account_source == "manifest-project-agent" and
  ([.projects[] | select(.vm_profile != null) | .repository] | sort) ==
    ["HSDB", "NewEMaint", "SFMDigitalBoard", "rsdesign-new"]
' "$ROOT/codex/config/host-access-broker.json" >/dev/null

set +e
denied_output="$("$ROOT/codex/tools/host-access-broker.sh" \
  --project hsdb --operation shell.run 2>&1)"
denied_status=$?
set -e
test "$denied_status" = 20
grep -Fq 'BLOCKED_EXTERNAL' <<<"$denied_output"
grep -Fq 'REQUEST_DENIED' <<<"$denied_output"

set +e
url_output="$("$ROOT/codex/tools/host-access-broker.sh" \
  --project hsdb --operation gitea.repo.read \
  --url http://attacker.invalid 2>&1)"
url_status=$?
set -e
test "$url_status" = 2
grep -Fq 'unrecognized arguments: --url' <<<"$url_output"

set +e
profile_output="$("$ROOT/codex/tools/project-profile-migration.sh" \
  --project unknown --action plan 2>&1)"
profile_status=$?
set -e
test "$profile_status" = 20
grep -Fq 'BLOCKED_EXTERNAL' <<<"$profile_output"
grep -Fq 'TARGET_DENIED' <<<"$profile_output"

export AISOFT_HOST_ACCESS_INSTALL_ROOT="$TMP/install-root"
first="$("$ROOT/codex/install-host-access-broker.sh")"
grep -Fq 'no credential, Git config, project profile, token, service, timer, VM, merge, or deployment mutation' \
  <<<"$first"
first_manifest="$TMP/first-manifest"
find "$AISOFT_HOST_ACCESS_INSTALL_ROOT" -type f -print0 |
  sort -z |
  xargs -0 shasum -a 256 >"$first_manifest"
second="$("$ROOT/codex/install-host-access-broker.sh")"
grep -Fq 'host-access-broker/v1 candidate' <<<"$second"
second_manifest="$TMP/second-manifest"
find "$AISOFT_HOST_ACCESS_INSTALL_ROOT" -type f -print0 |
  sort -z |
  xargs -0 shasum -a 256 >"$second_manifest"
diff -u "$first_manifest" "$second_manifest"

test -x "$AISOFT_HOST_ACCESS_INSTALL_ROOT/usr/local/libexec/aisoft/host-access-broker"
test -x "$AISOFT_HOST_ACCESS_INSTALL_ROOT/usr/local/libexec/aisoft/git-credential-aisoft-host"
test -x "$AISOFT_HOST_ACCESS_INSTALL_ROOT/usr/local/libexec/aisoft/project-profile-migration"
test -f "$AISOFT_HOST_ACCESS_INSTALL_ROOT/usr/local/share/aisoft/host-access-broker.json"
test -f "$AISOFT_HOST_ACCESS_INSTALL_ROOT/usr/local/lib/aisoft-host-access/aisoft_host_access/broker.py"
test ! -e "$AISOFT_HOST_ACCESS_INSTALL_ROOT/etc/aisoft/host-profile.json"
test ! -d "$AISOFT_HOST_ACCESS_INSTALL_ROOT/etc/systemd"
if find "$AISOFT_HOST_ACCESS_INSTALL_ROOT" -type f \
  \( -name '*.token' -o -name '*.env' \) | grep -q .; then
  echo 'broker installer created a credential or project profile' >&2
  exit 1
fi

printf '%s\n' 'host access broker shell and installer tests passed'

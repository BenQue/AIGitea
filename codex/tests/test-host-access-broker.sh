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
  .project_count == 10 and
  .operation_count == 26 and
  .merge_operation_count == 0
' "$TMP/validate.json" >/dev/null

jq -e '
  ([.operations[].name] | length == 26) and
  all(.operations[];
    (.name | contains("merge") | not) and
    (.name | contains("shell") | not) and
    (.name | contains("url") | not)) and
  .human_merge_identity == "admin" and
  .identity_bindings.manager_audit.identity == "aisoft-platform-manager" and
  .identity_bindings.manager_audit.credential_kind == "protected-file" and
  .identity_bindings.manager_mutation.identity == "aisoft-platform-manager" and
  .identity_bindings.manager_mutation.credential_kind == "protected-file" and
  .identity_bindings.project_agent.account_source == "manifest-project-agent" and
  .identity_bindings.project_agent.credential_kind == "protected-file" and
  .mac_host.credential_directory_mode == "700" and
  .mac_host.credential_file_mode == "600" and
  ([.operations[] | select(.name == "gitea.issue.create")][0].arguments == ["title", "body"]) and
  ([.operations[] | select(.name == "gitea.pull.create")][0].arguments == ["issue", "title", "body"]) and
  ([.operations[] | select(.name == "gitea.commit.status.read")][0].arguments == ["sha"]) and
  ([.operations[] | select(.name == "git.push.change")][0].arguments == ["branch"]) and
  ([.operations[] | select(.name == "host.access.audit")][0].arguments == []) and
  ([.operations[] | select(.name == "host.onboarding.check")][0].arguments == []) and
  ([.operations[] | select(.name == "gitea.labels.read")][0].arguments == []) and
  ([.operations[] | select(.name == "gitea.labels.provision")][0].arguments == []) and
  ([.operations[] | select(.name == "gitea.issue.labels.read")][0].arguments == ["number"]) and
  ([.operations[] | select(.name == "gitea.issue.labels.set")][0].arguments
    == ["number", "lifecycle"]) and
  ([.operations[] | select(.name == "gitea.issue.labels.set")][0].mutating == true) and
  ([.operations[] | select(.name == "gitea.issue.labels.read")][0].mutating == false) and
  ([.operations[].name] | any(test("^gitea\\.labels\\.")) ) and
  ([.operations[].name] | any(contains("delete")) | not) and
  ([.projects[] | select(.project_id == "newemaint")][0].git_remote_name == "gitea") and
  ([.projects[] | select(.project_id == "rsdesign-new")][0].git_remote_name == "gitea") and
  ([.projects[] | select(.project_id == "sfm-digital-board")][0].git_remote_name == "gitea") and
  ([.projects[]
    | select(.project_id != "newemaint" and .project_id != "rsdesign-new" and .project_id != "sfm-digital-board")
    | has("git_remote_name")] | all(. == false)) and
  ([.projects[] | select(.vm_profile != null) | .repository] | sort) ==
    ["HSDB", "NewEMaint", "SFMDigitalBoard", "aisoft-platform", "rsdesign-new"]
' "$ROOT/codex/config/host-access-broker.json" >/dev/null

if rg -ni 'keychain|/usr/bin/security|find-generic-password|dump-keychain|security -A' \
  "$ROOT/codex/runtime/aisoft_host_access"; then
  echo 'host access runtime contains a forbidden Keychain surface' >&2
  exit 1
fi

set +e
denied_output="$("$ROOT/codex/tools/host-access-broker.sh" \
  --project hsdb --operation shell.run 2>&1)"
denied_status=$?
set -e
test "$denied_status" = 20
grep -Fq 'BLOCKED_EXTERNAL' <<<"$denied_output"
grep -Fq 'REQUEST_DENIED' <<<"$denied_output"

# Label deletion is unreachable by construction (#108 AC-7): the provisioning
# operations exist, the delete counterpart is not allowlisted, and asking for it
# is denied rather than silently ignored.
set +e
labels_delete_output="$("$ROOT/codex/tools/host-access-broker.sh" \
  --project hsdb --operation gitea.labels.delete 2>&1)"
labels_delete_status=$?
set -e
test "$labels_delete_status" = 20
grep -Fq 'BLOCKED_EXTERNAL' <<<"$labels_delete_output"
grep -Fq 'REQUEST_DENIED' <<<"$labels_delete_output"

# gitea.issue.labels.set only accepts the lifecycle states the installed label
# manifest declares (#115 AC-1). An out-of-range value is refused before any
# credential is resolved or any request is made — so this case runs offline —
# and it is refused rather than silently ignored, which would look like success
# while leaving the Issue on its old state.
for invalid_lifecycle in bogus type/feature triage/ready-for-agent; do
  set +e
  lifecycle_output="$("$ROOT/codex/tools/host-access-broker.sh" \
    --project hsdb --operation gitea.issue.labels.set \
    --number 1 --lifecycle "$invalid_lifecycle" 2>&1)"
  lifecycle_status=$?
  set -e
  test "$lifecycle_status" = 20
  grep -Fq 'BLOCKED_EXTERNAL' <<<"$lifecycle_output"
  grep -Fq 'ARGUMENT_MISMATCH' <<<"$lifecycle_output"
done

# The lifecycle argument belongs to that one operation. Omitting it, or adding
# it to the read counterpart, is a typed-contract violation rather than a
# defaulted write.
for mismatched in \
  "--operation gitea.issue.labels.set --number 1" \
  "--operation gitea.issue.labels.read --number 1 --lifecycle completed"; do
  set +e
  # shellcheck disable=SC2086  # fixed literal argument vectors, not user input
  mismatch_output="$("$ROOT/codex/tools/host-access-broker.sh" \
    --project hsdb $mismatched 2>&1)"
  mismatch_status=$?
  set -e
  test "$mismatch_status" = 20
  grep -Fq 'ARGUMENT_MISMATCH' <<<"$mismatch_output"
done

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

for invalid_request in \
  $'protocol=http\nhost=gitea-ci.orb.local:3000\npath=admin/aisoft-platform.git\nmalformed\n' \
  $'protocol=http\nhost=gitea-ci.orb.local:3000\npath=admin/aisoft-platform.git\nauthtype=basic\n' \
  $'protocol=http\nprotocol=https\nhost=gitea-ci.orb.local:3000\npath=admin/aisoft-platform.git\n'; do
  set +e
  helper_output="$(printf '%s' "$invalid_request" | \
    "$ROOT/codex/tools/git-credential-aisoft-host.sh" get 2>&1)"
  helper_status=$?
  set -e
  test "$helper_status" = 20
  grep -Fq 'BLOCKED_EXTERNAL' <<<"$helper_output"
  grep -Fq 'CREDENTIAL_PROTOCOL_INVALID' <<<"$helper_output"
  if grep -Fq 'CREDENTIAL_UNAVAILABLE' <<<"$helper_output"; then
    echo 'credential helper reached the credential store before protocol rejection' >&2
    exit 1
  fi
done

export AISOFT_HOST_ACCESS_INSTALL_ROOT="$TMP/install-root"
mkdir -p "$AISOFT_HOST_ACCESS_INSTALL_ROOT/usr/local/libexec/aisoft"
printf '%s\n' legacy-helper > \
  "$AISOFT_HOST_ACCESS_INSTALL_ROOT/usr/local/libexec/aisoft/keychain-acl-audit"
printf '%s\n' legacy-helper-previous > \
  "$AISOFT_HOST_ACCESS_INSTALL_ROOT/usr/local/libexec/aisoft/keychain-acl-audit.previous"
first="$("$ROOT/codex/install-host-access-broker.sh")"
grep -Fq 'no credential, Git config, project profile, token, service, timer, VM, merge, or deployment mutation' \
  <<<"$first"
first_manifest="$TMP/first-manifest"
find "$AISOFT_HOST_ACCESS_INSTALL_ROOT" -type f -print0 |
  sort -z |
  xargs -0 shasum -a 256 >"$first_manifest"
second="$("$ROOT/codex/install-host-access-broker.sh")"
grep -Fq 'host-access-broker/v1 candidate already current (no-op)' <<<"$second"
second_manifest="$TMP/second-manifest"
find "$AISOFT_HOST_ACCESS_INSTALL_ROOT" -type f -print0 |
  sort -z |
  xargs -0 shasum -a 256 >"$second_manifest"
diff -u "$first_manifest" "$second_manifest"

test -x "$AISOFT_HOST_ACCESS_INSTALL_ROOT/usr/local/libexec/aisoft/host-access-broker"
test ! -e "$AISOFT_HOST_ACCESS_INSTALL_ROOT/usr/local/libexec/aisoft/keychain-acl-audit"
test ! -e "$AISOFT_HOST_ACCESS_INSTALL_ROOT/usr/local/libexec/aisoft/keychain-acl-audit.previous"
test -x "$AISOFT_HOST_ACCESS_INSTALL_ROOT/usr/local/libexec/aisoft/git-credential-aisoft-host"
test -x "$AISOFT_HOST_ACCESS_INSTALL_ROOT/usr/local/libexec/aisoft/project-profile-migration"
test -f "$AISOFT_HOST_ACCESS_INSTALL_ROOT/usr/local/share/aisoft/host-access-broker.json"
test -f "$AISOFT_HOST_ACCESS_INSTALL_ROOT/usr/local/lib/aisoft-host-access/aisoft_host_access/broker.py"
test -f "$AISOFT_HOST_ACCESS_INSTALL_ROOT/usr/local/lib/aisoft-host-access/aisoft_change_name.py"
test ! -e "$AISOFT_HOST_ACCESS_INSTALL_ROOT/etc/aisoft/host-profile.json"
test ! -d "$AISOFT_HOST_ACCESS_INSTALL_ROOT/etc/systemd"
if find "$AISOFT_HOST_ACCESS_INSTALL_ROOT" -type f \
  \( -name '*.token' -o -name '*.env' \) | grep -q .; then
  echo 'broker installer created a credential or project profile' >&2
  exit 1
fi

printf '%s\n' 'host access broker shell and installer tests passed'

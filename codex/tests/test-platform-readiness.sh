#!/usr/bin/env bash
set -euo pipefail

root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
test_root="$(mktemp -d)"
trap 'rm -rf "$test_root"' EXIT

bash "$root/codex/install-skills.sh" "$test_root/home" >/dev/null

fake_broker="$test_root/fake-broker"
cat >"$fake_broker" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
operation=''
while (($#)); do
  case "$1" in
    --operation) operation="$2"; shift 2 ;;
    --project) shift 2 ;;
    *) exit 2 ;;
  esac
done
case "$operation" in
  gitea.repo.read) printf '%s\n' '{"default_branch":"main","has_actions":true}' ;;
  gitea.protection.read)
    if [[ "${FAKE_PROTECTION_GAP:-0}" == "1" ]]; then
      printf '%s\n' '{"enable_status_check":false,"status_check_contexts":[]}'
    else
      printf '%s\n' '{"enable_status_check":true,"status_check_contexts":["CI / verify (pull_request)"]}'
    fi
    ;;
  orbstack.vm.units.read)
    case "${FAKE_UNITS:-pass}" in
      pass)
        printf '%s\n' '{"status":"PASS","timer_count":2,"timers":[
          {"timer":"a.timer","enabled":true,"failures_24h":0},
          {"timer":"b.timer","enabled":false,"failures_24h":7}]}'
        ;;
      none) printf '%s\n' '{"status":"PASS","timer_count":0,"timers":[]}' ;;
      gap)
        printf '%s\n' '{"status":"PASS","timer_count":2,"timers":[
          {"timer":"a.timer","enabled":true,"failures_24h":49},
          {"timer":"b.timer","enabled":true,"failures_24h":0}]}'
        ;;
      missing)
        printf '%s\n' '{"code":"REQUEST_DENIED","message":"requested operation is not allowlisted","status":"BLOCKED_EXTERNAL"}' >&2
        exit 20
        ;;
      malformed) printf '%s\n' '{"status":"PASS","timers":[{"timer":"a.timer","enabled":true}]}' ;;
      broken)
        printf '%s\n' '{"code":"HOST_COMMAND_FAILED","message":"structured host operation failed","status":"BLOCKED_EXTERNAL"}' >&2
        exit 20
        ;;
    esac
    ;;
  *) exit 2 ;;
esac
EOF
chmod +x "$fake_broker"

# #397: PAT_AGE reads a fixture credential root only, never the real store,
# and never opens a token (the fixture token is unreadable on purpose).
creds="$test_root/credentials"
mkdir -p "$creds/manager/.rotation-manager-mutation"
: >"$creds/manager/audit.token"
chmod 000 "$creds/manager/audit.token"
printf 'issue=1\n' >"$creds/manager/audit.token-created-by-issue-1"
touch -t "$(date -v-10d +%Y%m%d%H%M 2>/dev/null || date -d '10 days ago' +%Y%m%d%H%M)" \
  "$creds/manager/audit.token-created-by-issue-1"
printf '{"observed_at":%s}\n' "$(($(date +%s) - 200 * 86400))" \
  >"$creds/manager/.rotation-manager-mutation/provenance.json"
printf '{"phase":"complete"}\n' >"$creds/manager/.rotation-manager-mutation/journal.json"
# A receipt whose transaction never completed is not a rotation (provenance is
# written before the journal reaches complete).
mkdir -p "$creds/projects/aisoft-platform/.rotation-project-agent"
printf '{"observed_at":%s}\n' "$(date +%s)" >"$creds/projects/aisoft-platform/.rotation-project-agent/provenance.json"
printf '{"phase":"revoked"}\n' >"$creds/projects/aisoft-platform/.rotation-project-agent/journal.json"

output="$(bash "$root/codex/tools/aisoft-platform-readiness.sh" \
  --repo "$root" --home "$test_root/home" --broker "$fake_broker" --credential-root "$creds")"
# Two manager credentials plus one agent per project, none of which has metadata.
note="$(grep -E '^PAT_AGE NOTE checked=[0-9]+ over_180d=1 unknown=[0-9]+$' <<<"$output")"
checked="$(sed -E 's/.*checked=([0-9]+).*/\1/' <<<"$note")"
unknown="$(sed -E 's/.*unknown=([0-9]+)$/\1/' <<<"$note")"
[[ "$checked" == "$((unknown + 2))" && "$unknown" -gt 0 ]]
grep -Eq '^  PAT_AGE manager/audit.token 1[01]d source=marker$' <<<"$output"
grep -Eq '^  PAT_AGE manager/mutation.token 200d source=receipt OVER$' <<<"$output"
grep -Fq '  PAT_AGE projects/aisoft-platform/project-agent.token unknown' <<<"$output"
grep -Fq 'SOURCE PASS' <<<"$output"
grep -Fq 'INSTALLED_CODEX PASS' <<<"$output"
grep -Fq 'INSTALLED_CLAUDE NOT_INSTALLED' <<<"$output"
grep -Fq 'LIVE_REPO PASS' <<<"$output"
grep -Fq 'LIVE_PROTECTION PASS status_check=true contexts=1' <<<"$output"
# A disabled timer's past failures do not count against readiness.
grep -Fq 'LIVE_VM_TIMERS PASS enabled=1 failing=0' <<<"$output"

none_output="$(FAKE_UNITS=none bash "$root/codex/tools/aisoft-platform-readiness.sh" \
  --repo "$root" --home "$test_root/home" --broker "$fake_broker" --credential-root "$creds")"
grep -Fq 'LIVE_VM_TIMERS PASS enabled=0 failing=0' <<<"$none_output"

for mode in gap missing broken malformed; do
  set +e
  units_output="$(FAKE_UNITS="$mode" bash "$root/codex/tools/aisoft-platform-readiness.sh" \
    --repo "$root" --home "$test_root/home" --broker "$fake_broker" --credential-root "$creds")"
  units_status=$?
  set -e
  [[ "$units_status" == "1" ]]
  case "$mode" in
    gap) grep -Fq 'LIVE_VM_TIMERS GAP enabled=2 failing=a.timer:49' <<<"$units_output" ;;
    missing) grep -Fq 'LIVE_VM_TIMERS BLOCKED operation-not-installed' <<<"$units_output" ;;
    broken | malformed) grep -Fq 'LIVE_VM_TIMERS BLOCKED unreadable' <<<"$units_output" ;;
  esac
done

set +e
gap_output="$(FAKE_PROTECTION_GAP=1 bash "$root/codex/tools/aisoft-platform-readiness.sh" \
  --repo "$root" --home "$test_root/home" --broker "$fake_broker" --credential-root "$creds")"
gap_status=$?
set -e
[[ "$gap_status" == "1" ]]
grep -Fq 'LIVE_PROTECTION GAP status_check=false contexts=0' <<<"$gap_output"

printf '%s\n' 'platform readiness tests passed'

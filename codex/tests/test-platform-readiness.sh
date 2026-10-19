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

output="$(bash "$root/codex/tools/aisoft-platform-readiness.sh" \
  --repo "$root" --home "$test_root/home" --broker "$fake_broker")"
grep -Fq 'SOURCE PASS' <<<"$output"
grep -Fq 'INSTALLED_CODEX PASS' <<<"$output"
grep -Fq 'INSTALLED_CLAUDE NOT_INSTALLED' <<<"$output"
grep -Fq 'LIVE_REPO PASS' <<<"$output"
grep -Fq 'LIVE_PROTECTION PASS status_check=true contexts=1' <<<"$output"
# A disabled timer's past failures do not count against readiness.
grep -Fq 'LIVE_VM_TIMERS PASS enabled=1 failing=0' <<<"$output"

none_output="$(FAKE_UNITS=none bash "$root/codex/tools/aisoft-platform-readiness.sh" \
  --repo "$root" --home "$test_root/home" --broker "$fake_broker")"
grep -Fq 'LIVE_VM_TIMERS PASS enabled=0 failing=0' <<<"$none_output"

for mode in gap missing broken malformed; do
  set +e
  units_output="$(FAKE_UNITS="$mode" bash "$root/codex/tools/aisoft-platform-readiness.sh" \
    --repo "$root" --home "$test_root/home" --broker "$fake_broker")"
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
  --repo "$root" --home "$test_root/home" --broker "$fake_broker")"
gap_status=$?
set -e
[[ "$gap_status" == "1" ]]
grep -Fq 'LIVE_PROTECTION GAP status_check=false contexts=0' <<<"$gap_output"

printf '%s\n' 'platform readiness tests passed'

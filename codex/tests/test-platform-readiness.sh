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

set +e
gap_output="$(FAKE_PROTECTION_GAP=1 bash "$root/codex/tools/aisoft-platform-readiness.sh" \
  --repo "$root" --home "$test_root/home" --broker "$fake_broker")"
gap_status=$?
set -e
[[ "$gap_status" == "1" ]]
grep -Fq 'LIVE_PROTECTION GAP status_check=false contexts=0' <<<"$gap_output"

printf '%s\n' 'platform readiness tests passed'

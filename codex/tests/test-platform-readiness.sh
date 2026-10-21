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

# #403: --render-readme reads source files only. A broker that records any call
# proves it is never consulted.
spy_broker="$test_root/spy-broker"
printf '#!/usr/bin/env bash\necho called >>"%s"\nexit 2\n' "$test_root/spy-calls" >"$spy_broker"
chmod +x "$spy_broker"
bash "$root/codex/tools/aisoft-platform-readiness.sh" --render-readme \
  --repo "$root" --broker "$spy_broker" >/dev/null
[[ ! -e "$test_root/spy-calls" ]]

# Every row, value and source is asserted on an isolated checkout built from the
# synthetic manifests (#380), so a missing fact can be injected without touching
# the real ones.
render_repo="$test_root/render-repo"
mkdir -p "$render_repo/codex/config" "$render_repo/usage" "$render_repo/.claude-plugin" \
  "$render_repo/codex/vendor/superpowers/v0" "$render_repo/architecture"
cp "$root"/codex/tests/fixtures/manifests/*.json "$render_repo/codex/config/"
for file in codex/config/installed-drift-baseline.json codex/config/gitea-labels.json \
  usage/bundle.json .claude-plugin/marketplace.json architecture/catalog.json; do
  cp "$root/$file" "$render_repo/$file"
done
cp "$root"/codex/vendor/superpowers/*/manifest.json "$render_repo/codex/vendor/superpowers/v0/"
git -C "$render_repo" init -q
git -C "$render_repo" -c user.name=t -c user.email=t@example.invalid commit -q --allow-empty -m fixture
config="$render_repo/codex/config"
# The source column names files by path; only the label is built from $label so the
# #380 guard keeps meaning "reads a real manifest".
label=codex/config
# shellcheck disable=SC2016 # backticks are literal Markdown, not expansions
expected="$(
  printf '%s\n' '| 项 | 值 | 来源 |' '|---|---|---|'
  printf '| 源码 | `%s` | `git rev-parse HEAD` |\n' "$(git -C "$render_repo" rev-parse --short=12 HEAD)"
  printf '| 治理仓库 | %s | `%s/gitea-governance.json` `.repositories` |\n' \
    "$(jq '.repositories | length' "$config/gitea-governance.json")" "$label"
  printf '| broker typed 操作 | %s | `%s/host-access-broker.json` `.operations` |\n' \
    "$(jq '.operations | length' "$config/host-access-broker.json")" "$label"
  printf '| installer 安装面 | %s | `codex/config/installed-drift-baseline.json` `.hosts` |\n' \
    "$(jq '[.hosts[] | keys[]] | unique | length' "$config/installed-drift-baseline.json")"
  printf '| 规范标签 | %s（type/* %s） | `codex/config/gitea-labels.json` `.canonical` |\n' \
    "$(jq '.canonical | length' "$config/gitea-labels.json")" \
    "$(jq '[.canonical[] | select(.name | startswith("type/"))] | length' "$config/gitea-labels.json")"
  printf '| 使用发布包最新版本 | %s | `usage/bundle.json` `.releases[-1]` |\n' \
    "$(jq -r '.releases[-1].version' "$render_repo/usage/bundle.json")"
  printf '| Matt pin | %s | `.claude-plugin/marketplace.json` |\n' \
    "$(jq -r '.plugins[] | select(.name == "mattpocock-skills") | .source | "\(.ref) `\(.sha[0:12])`"' \
      "$render_repo/.claude-plugin/marketplace.json")"
  printf '| superpowers pin | %s | `codex/vendor/superpowers/*/manifest.json` |\n' \
    "$(jq -r '"\(.tag) `\(.commit[0:12])`"' "$render_repo"/codex/vendor/superpowers/v0/manifest.json)"
  printf '| architecture catalog | %s | `architecture/catalog.json` `.revision` |\n' \
    "$(jq -r '.revision' "$render_repo/architecture/catalog.json")"
)"
[[ "$(bash "$root/codex/tools/aisoft-platform-readiness.sh" --render-readme --repo "$render_repo")" == "$expected" ]]

# A missing key, a wrong type or a missing pin fails the render with nothing on
# stdout -- never a row reading 0 or null.
render_must_fail() {
  local file="$1" filter="$2" saved="$test_root/render-saved.json" status output
  cp "$render_repo/$file" "$saved"
  jq "$filter" "$saved" >"$render_repo/$file"
  set +e
  output="$(bash "$root/codex/tools/aisoft-platform-readiness.sh" --render-readme \
    --repo "$render_repo" 2>/dev/null)"
  status=$?
  set -e
  cp "$saved" "$render_repo/$file"
  [[ "$status" == "1" && -z "$output" ]] || {
    echo "render accepted $file with $filter" >&2
    exit 1
  }
}
render_must_fail "$label/host-access-broker.json" 'del(.operations)'
render_must_fail "$label/gitea-governance.json" '.repositories = "x"'
render_must_fail codex/config/installed-drift-baseline.json '.hosts = {}'
render_must_fail usage/bundle.json '.releases[-1].version = null'
render_must_fail .claude-plugin/marketplace.json '(.plugins[] | select(.name == "mattpocock-skills") | .source) |= del(.sha)'
render_must_fail architecture/catalog.json 'del(.revision)'
mv "$render_repo/codex/vendor/superpowers/v0/manifest.json" "$test_root/superpowers-manifest.json"
jq 'del(.commit)' "$test_root/superpowers-manifest.json" >"$render_repo/codex/vendor/superpowers/v0/manifest.json"
set +e
pin_output="$(bash "$root/codex/tools/aisoft-platform-readiness.sh" --render-readme \
  --repo "$render_repo" 2>/dev/null)"
pin_status=$?
set -e
[[ "$pin_status" == "1" && -z "$pin_output" ]]

printf '%s\n' 'platform readiness tests passed'

#!/usr/bin/env bash
# #387: Mac failure alerts; #397 adds the projection gate. Fixture broker, notifier and launchctl only; never
# the real broker, osascript or the CI host's launchd.
set -euo pipefail

root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
test_root="$(mktemp -d)"
trap 'rm -rf "$test_root"' EXIT

poll="$root/codex/tools/aisoft-alert-poll.sh"
fake_broker="$test_root/fake-broker"
cat >"$fake_broker" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
operation=''
sha=''
number=''
while (($#)); do
  case "$1" in
    --operation) operation="$2"; shift 2 ;;
    --sha) sha="$2"; shift 2 ;;
    --number) number="$2"; shift 2 ;;
    --project | --state) shift 2 ;;
    *) exit 2 ;;
  esac
done
if [[ "${FAKE_BROKER_DOWN:-0}" == "1" ]]; then
  printf '%s\n' '{"code":"HOST_COMMAND_FAILED","message":"structured host operation failed","status":"BLOCKED_EXTERNAL"}' >&2
  exit 20
fi
case "$operation" in
  gitea.pulls.read)
    if [[ -n "${FAKE_PULLS:-}" ]]; then
      printf '%s\n' "$FAKE_PULLS"
    else
      printf '[{"number":7,"head":{"sha":"%s","ref":"change/7-fixture"},"body":null}]\n' "${FAKE_HEAD:-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa}"
    fi
    ;;
  gitea.commit.status.read)
    [[ "$sha" =~ ^[0-9a-f]{40}$ ]] || exit 2
    if [[ "$sha" == "${FAKE_DOWN_SHA:-}" ]]; then
      printf '%s\n' '{"code":"HTTP_502","status":"BLOCKED_EXTERNAL"}' >&2
      exit 20
    fi
    case "${FAKE_STATUS_SHAPE:-ok}" in
      array) printf '[]\n' ;;
      empty) printf '{}\n' ;;
      unknown) printf '{"sha":"%s","state":"exploded"}\n' "$sha" ;;
      *) printf '{"sha":"%s","state":"%s"}\n' "$sha" "${FAKE_CI:-success}" ;;
    esac
    ;;
  gitea.issue.labels.read)
    [[ "$number" =~ ^[1-9][0-9]*$ ]] || exit 2
    printf '%s\n' "$number" >>"${FAKE_LABEL_LOG:-/dev/null}"
    if [[ "$number" == "${FAKE_LABELS_DOWN:-}" ]]; then
      printf '%s\n' '{"code":"HTTP_502","status":"BLOCKED_EXTERNAL"}' >&2
      exit 20
    fi
    projected='[{"name":"approved"},{"name":"type/platform"},{"name":"complexity/complex"}]'
    printf '%s\n' "${FAKE_LABELS:-$projected}"
    ;;
  orbstack.vm.units.read)
    if [[ "${FAKE_UNITS_SHAPE:-ok}" == "bad" ]]; then
      printf '%s\n' '{"status":"PASS","timers":[{"timer":"a.timer","enabled":true}]}'
      exit 0
    fi
    printf '{"status":"PASS","timers":[{"timer":"a.timer","enabled":true,"failures_24h":%s},
      {"timer":"b.timer","enabled":false,"failures_24h":9}]}\n' "${FAKE_TIMER_FAILURES:-0}"
    ;;
  *) exit 2 ;;
esac
EOF
chmod +x "$fake_broker"

notifications="$test_root/notifications.log"
notifier="$test_root/notifier"
cat >"$notifier" <<EOF
#!/usr/bin/env bash
printf '%s|%s\n' "\$1" "\$2" >>"$notifications"
EOF
chmod +x "$notifier"

state="$test_root/state"
run_poll() {
  AISOFT_ALERT_NOTIFIER="$notifier" bash "$poll" --broker "$fake_broker" --state-dir "$state"
}
refute() {
  if "$@"; then
    echo "unexpected match: $*" >&2
    exit 1
  fi
}
notified() {
  [[ -f "$notifications" ]] && wc -l <"$notifications" | tr -d ' ' || echo 0
}

# Healthy: nothing to say, and a disabled timer's failures do not count.
out="$(run_poll)"
grep -Fxq 'ALERTS active=0 new=0 broker_failures=0' <<<"$out"
[[ "$(notified)" == "0" ]]

# CI failure on an open PR notifies once.
out="$(FAKE_CI=failure run_poll)"
grep -Fxq 'ALERTS active=1 new=1 broker_failures=0' <<<"$out"
grep -Fq 'PR #7 CI failure (aaaaaaaa)' "$notifications"
[[ "$(stat -c '%a' "$state" 2>/dev/null || stat -f '%Lp' "$state")" == "700" ]]

# Unchanged failure: no repeat.
FAKE_CI=failure run_poll >/dev/null
[[ "$(notified)" == "1" ]]

# A new failing head is a new alert.
FAKE_CI=error FAKE_HEAD=bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb run_poll >/dev/null
[[ "$(notified)" == "2" ]]
grep -Fq 'PR #7 CI error (bbbbbbbb)' "$notifications"

# Timer failure notifies once, alongside the still-failing CI head.
out="$(FAKE_CI=error FAKE_HEAD=bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb FAKE_TIMER_FAILURES=49 run_poll)"
grep -Fxq 'ALERTS active=2 new=1 broker_failures=0' <<<"$out"
grep -Fq 'a.timer failed 49 times in 24h' "$notifications"
FAKE_CI=error FAKE_HEAD=bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb FAKE_TIMER_FAILURES=50 run_poll >/dev/null
[[ "$(notified)" == "3" ]]
refute grep -Fq 'b.timer' "$notifications"

# Broker unavailable: reported once, previous alerts kept rather than cleared.
out="$(FAKE_BROKER_DOWN=1 run_poll)"
grep -Fxq 'ALERTS active=3 new=1 broker_failures=2' <<<"$out"
grep -Fq 'broker unreadable: gitea.pulls.read:HOST_COMMAND_FAILED' "$notifications"
FAKE_BROKER_DOWN=1 run_poll >/dev/null
[[ "$(notified)" == "4" ]]

# Recovery with the same failures does not re-notify them.
FAKE_CI=error FAKE_HEAD=bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb FAKE_TIMER_FAILURES=50 run_poll >/dev/null
[[ "$(notified)" == "4" ]]
# Cleared, then failing again: notified again.
run_poll >/dev/null
FAKE_TIMER_FAILURES=1 run_poll >/dev/null
[[ "$(notified)" == "5" ]]

# A malformed but successful answer is unreadable, not healthy: the poll keeps
# running, keeps the affected previous alerts and reports the broker once.
state_wrong="$test_root/state-wrong"
run_wrong() {
  AISOFT_ALERT_NOTIFIER="$notifier" bash "$poll" --broker "$fake_broker" --state-dir "$state_wrong"
}
FAKE_CI=failure FAKE_TIMER_FAILURES=3 run_wrong >/dev/null
before="$(notified)"
expected_new=1
for shape in array empty unknown; do
  out="$(FAKE_STATUS_SHAPE="$shape" FAKE_UNITS_SHAPE=bad run_wrong)"
  grep -Fxq "ALERTS active=3 new=$expected_new broker_failures=2" <<<"$out"
  expected_new=0
  grep -Fq 'ci:aisoft-platform:7:' "$state_wrong/active-alerts.tsv"
  grep -Fq 'timer:a.timer' "$state_wrong/active-alerts.tsv"
done
[[ "$(notified)" == "$((before + 1))" ]]
grep -Fq 'broker unreadable: gitea.commit.status.read:RESPONSE_SCHEMA_INVALID' "$notifications"

# A nested field of the wrong type in the PR list is unreadable too; the
# previous CI alert survives instead of being silently cleared.
for pulls in '[{"number":7,"head":[]}]' '[{"number":"7","head":{"sha":"x"}}]' '{"number":7}' '[1]'; do
  FAKE_PULLS="$pulls" FAKE_STATUS_SHAPE=ok FAKE_TIMER_FAILURES=3 run_wrong >/dev/null
  grep -Fq 'ci:aisoft-platform:7:' "$state_wrong/active-alerts.tsv"
  grep -Fq 'broker:unavailable' "$state_wrong/active-alerts.tsv"
done

# Two failing PRs, one status read fails: only that PR's previous key is kept,
# the other is re-read and clears once it passes.
state_multi="$test_root/state-multi"
run_multi() {
  AISOFT_ALERT_NOTIFIER="$notifier" bash "$poll" --broker "$fake_broker" --state-dir "$state_multi"
}
two='[{"number":7,"head":{"sha":"cccccccccccccccccccccccccccccccccccccccc","ref":"change/7-a"}},{"number":8,"head":{"sha":"dddddddddddddddddddddddddddddddddddddddd","ref":"change/8-b"}}]'
FAKE_PULLS="$two" FAKE_CI=failure run_multi >/dev/null
grep -Fq 'ci:aisoft-platform:7:' "$state_multi/active-alerts.tsv"
grep -Fq 'ci:aisoft-platform:8:' "$state_multi/active-alerts.tsv"
out="$(FAKE_PULLS="$two" FAKE_CI=success FAKE_DOWN_SHA=cccccccccccccccccccccccccccccccccccccccc run_multi)"
grep -Fxq 'ALERTS active=2 new=1 broker_failures=1' <<<"$out"
grep -Fq 'ci:aisoft-platform:7:' "$state_multi/active-alerts.tsv"
refute grep -Fq 'ci:aisoft-platform:8:' "$state_multi/active-alerts.tsv"

# #397 reverse proof: an open PR whose Issue lacks complexity/* alerts once,
# clears when the projection lands, and the Issue comes from the exact branch
# name or else the single Closes line. A PR that names no Issue alerts too; a
# labels read failure keeps that PR's previous projection key.
state_proj="$test_root/state-projection"
label_log="$test_root/labels.log"
run_proj() {
  AISOFT_ALERT_NOTIFIER="$notifier" FAKE_LABEL_LOG="$label_log" \
    bash "$poll" --broker "$fake_broker" --state-dir "$state_proj"
}
unprojected='[{"name":"approved"},{"name":"type/platform"}]'
pulls='[{"number":21,"head":{"sha":"eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee","ref":"change/397-ops-closure"},"body":"Closes #5"},
  {"number":22,"head":{"sha":"ffffffffffffffffffffffffffffffffffffffff","ref":"feature"},"body":"intro\nCloses #398\n"}]'
before="$(notified)"
out="$(FAKE_PULLS="$pulls" FAKE_LABELS="$unprojected" run_proj)"
grep -Fxq 'ALERTS active=2 new=2 broker_failures=0' <<<"$out"
grep -Fq 'PR #21: Issue #397 lacks type/* or complexity/*' "$notifications"
grep -Fq 'PR #22: Issue #398 lacks type/* or complexity/*' "$notifications"
[[ "$(sort -n "$label_log" | tr '\n' ' ')" == '397 398 ' ]]
FAKE_PULLS="$pulls" FAKE_LABELS="$unprojected" run_proj >/dev/null
[[ "$(notified)" == "$((before + 2))" ]]
out="$(FAKE_PULLS="$pulls" FAKE_LABELS="$unprojected" FAKE_LABELS_DOWN=397 run_proj)"
grep -Fxq 'ALERTS active=3 new=1 broker_failures=1' <<<"$out"
grep -Fq 'projection:aisoft-platform:21:397' "$state_proj/active-alerts.tsv"
out="$(FAKE_PULLS="$pulls" run_proj)"
grep -Fxq 'ALERTS active=0 new=0 broker_failures=0' <<<"$out"
unbound='[{"number":23,"head":{"sha":"1111111111111111111111111111111111111111","ref":"main"},"body":"Closes #1\nCloses #2"}]'
out="$(FAKE_PULLS="$unbound" run_proj)"
grep -Fxq 'ALERTS active=1 new=1 broker_failures=0' <<<"$out"
grep -Fq 'PR #23 names no Issue' "$notifications"
# An invalid head SHA is an unreadable list entry: the projection key stays.
FAKE_PULLS="$pulls" FAKE_LABELS="$unprojected" run_proj >/dev/null
out="$(FAKE_PULLS='[{"number":21,"head":{"sha":"bad","ref":"change/397-x"}}]' run_proj)"
grep -Fq 'broker_failures=1' <<<"$out"
grep -Fq 'projection:aisoft-platform:21:397' "$state_proj/active-alerts.tsv"
for shape in '{}' '[{"id":1}]' '"x"'; do
  out="$(FAKE_PULLS="$pulls" FAKE_LABELS="$unprojected" run_proj >/dev/null; FAKE_PULLS="$pulls" FAKE_LABELS="$shape" run_proj)"
  grep -Fq 'broker_failures=2' <<<"$out"
  grep -Fq 'projection:aisoft-platform:21:397' "$state_proj/active-alerts.tsv"
done

# The state file carries keys and messages only.
refute grep -Eiq 'token|password|authorization' "$state/active-alerts.tsv"

# Installer: user scope, rendered plist, bootstrap and clean uninstall.
launchctl_log="$test_root/launchctl.log"
fake_launchctl="$test_root/launchctl"
cat >"$fake_launchctl" <<EOF
#!/usr/bin/env bash
printf '%s\n' "\$*" >>"$launchctl_log"
EOF
chmod +x "$fake_launchctl"
home="$test_root/home & co"
AISOFT_LAUNCHCTL="$fake_launchctl" bash "$root/codex/tools/install-alert-agent.sh" --home "$home" >/dev/null
plist="$home/Library/LaunchAgents/com.aisoft.platform-alerts.plist"
alerts="$home/Library/Application Support/AISoftPlatform/alerts"
[[ -x "$alerts/aisoft-alert-poll.sh" ]]
cmp -s "$poll" "$alerts/aisoft-alert-poll.sh"
grep -Fq '<integer>900</integer>' "$plist"
grep -Fq "<string>${test_root}/home &amp; co/Library/Application Support/AISoftPlatform/alerts/aisoft-alert-poll.sh</string>" "$plist"
refute grep -Fq '__' "$plist"
if command -v plutil >/dev/null; then plutil -lint "$plist" >/dev/null; fi
python3 -c 'import plistlib,sys; d=plistlib.load(open(sys.argv[1],"rb")); assert d["StartInterval"]==900 and d["RunAtLoad"] is True' "$plist"
grep -Eq "^bootstrap gui/[0-9]+ $plist\$" "$launchctl_log"

AISOFT_LAUNCHCTL="$fake_launchctl" bash "$root/codex/tools/install-alert-agent.sh" --home "$home" --uninstall >/dev/null
grep -Eq '^bootout gui/[0-9]+/com\.aisoft\.platform-alerts$' "$launchctl_log"
[[ ! -e "$plist" && ! -e "$alerts" ]]

printf '%s\n' 'alert agent tests passed'

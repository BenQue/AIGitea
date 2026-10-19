#!/usr/bin/env bash
# #387: Mac failure alerts. Fixture broker, notifier and launchctl only; never
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
while (($#)); do
  case "$1" in
    --operation) operation="$2"; shift 2 ;;
    --sha) sha="$2"; shift 2 ;;
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
    printf '[{"number":7,"head":{"sha":"%s"}}]\n' "${FAKE_HEAD:-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa}"
    ;;
  gitea.commit.status.read)
    [[ "$sha" =~ ^[0-9a-f]{40}$ ]] || exit 2
    case "${FAKE_STATUS_SHAPE:-ok}" in
      array) printf '[]\n' ;;
      empty) printf '{}\n' ;;
      *) printf '{"sha":"%s","state":"%s"}\n' "$sha" "${FAKE_CI:-success}" ;;
    esac
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
for shape in array empty; do
  out="$(FAKE_STATUS_SHAPE="$shape" FAKE_UNITS_SHAPE=bad run_wrong)"
  grep -Fxq "ALERTS active=3 new=$expected_new broker_failures=2" <<<"$out"
  expected_new=0
  grep -Fq 'ci:aisoft-platform:7:' "$state_wrong/active-alerts.tsv"
  grep -Fq 'timer:a.timer' "$state_wrong/active-alerts.tsv"
done
[[ "$(notified)" == "$((before + 1))" ]]
grep -Fq 'broker unreadable: gitea.commit.status.read:RESPONSE_SCHEMA_INVALID' "$notifications"

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

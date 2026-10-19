#!/usr/bin/env bash
# Read-only failure poller for the platform owner's Mac (#387, 05 §5).
#
# Reads, through the host-access broker only, the CI state of the platform
# repository's open pull requests and the VM timer health, and raises a local
# notification for each failure that was not already active on the previous
# run. Never writes to Gitea, the VM or the broker; the only state it keeps is a
# list of active alert keys in the state directory, which holds no credentials.
set -euo pipefail

project="aisoft-platform"
broker="${AISOFT_HOST_ACCESS_BROKER:-/usr/local/libexec/aisoft/host-access-broker}"
state_dir="${AISOFT_ALERT_STATE_DIR:-$HOME/Library/Application Support/AISoftPlatform/alerts}"
# Tests replace the notifier; it receives the title and the message as two
# arguments and nothing else.
notifier="${AISOFT_ALERT_NOTIFIER:-}"
max_notifications=5

usage() {
  cat <<'EOF'
Usage: aisoft-alert-poll.sh [--project ID] [--broker PATH] [--state-dir PATH]

Raises a macOS notification for each new failure among: CI on open pull
requests of the project, enabled VM timers whose service failed in the last
24 hours, and the broker itself being unreadable. A failure that stays active
is notified once; it is notified again only after it clears and returns.
Prints one summary line and exits 0 unless its own arguments or tools are
invalid.
EOF
}

while (($#)); do
  case "$1" in
    --project | --broker | --state-dir)
      (($# >= 2)) || {
        usage >&2
        exit 2
      }
      case "$1" in
        --project) project="$2" ;;
        --broker) broker="$2" ;;
        --state-dir) state_dir="$2" ;;
      esac
      shift 2
      ;;
    -h | --help)
      usage
      exit 0
      ;;
    *)
      usage >&2
      exit 2
      ;;
  esac
done

command -v jq >/dev/null || {
  echo 'ALERTS BLOCKED jq-unavailable' >&2
  exit 2
}

notify() {
  local title="$1" message="$2"
  if [[ -n "$notifier" ]]; then
    "$notifier" "$title" "$message"
    return
  fi
  # Text travels as osascript argv, never spliced into the script source.
  /usr/bin/osascript \
    -e 'on run argv' \
    -e 'display notification (item 2 of argv) with title (item 1 of argv)' \
    -e 'end run' \
    "$title" "$message" >/dev/null 2>&1 || true
}

mkdir -p -- "$state_dir"
chmod 700 "$state_dir"
state_file="$state_dir/active-alerts.tsv"
work="$(mktemp -d)"
trap 'rm -rf -- "$work"' EXIT
[[ -f "$state_file" ]] || : >"$state_file"

current="$work/current.tsv"
: >"$current"
: >"$work/error.json"
broker_failures=()

# Keep the previous alerts of a source that could not be read, so a broker
# outage neither clears them nor re-notifies them when the broker returns.
carry_over() {
  awk -F '\t' -v prefix="$1" 'index($1, prefix) == 1' "$state_file" >>"$current"
}

# On failure the broker's error stays in error.json and is recorded; on
# success error.json is emptied (the broker writes receipts to stderr), so a
# non-empty error.json after a failed check means the call itself failed.
broker_call() {
  local operation="$1" output="$2"
  shift 2
  if ! "$broker" --project "$project" --operation "$operation" "$@" \
    >"$output" 2>"$work/error.json"; then
    broker_failures+=("$operation:$(jq -r '.code // "UNREADABLE"' "$work/error.json" 2>/dev/null ||
      echo UNREADABLE)")
    [[ -s "$work/error.json" ]] || echo '{}' >"$work/error.json"
    return 1
  fi
  : >"$work/error.json"
}

# CI on open pull requests. A new head is a new alert key, so a fresh failing
# push notifies again while a re-read of the same failing head does not. A
# response of the wrong shape counts as the broker being unreadable and keeps
# that source's previous keys; it never reads as "no failure".
if broker_call gitea.pulls.read "$work/pulls.json" --state open &&
  jq -e 'type == "array" and all(.[]; type == "object")' "$work/pulls.json" >/dev/null 2>&1; then
  while IFS=$'\t' read -r number sha; do
    if ! [[ "$number" =~ ^[0-9]+$ && "$sha" =~ ^[0-9a-f]{40}$ ]]; then
      broker_failures+=("gitea.pulls.read:RESPONSE_SCHEMA_INVALID")
      carry_over "ci:$project:"
      continue
    fi
    if broker_call gitea.commit.status.read "$work/status.json" --sha "$sha" &&
      state="$(jq -er 'if type == "object" and (.state | type) == "string"
        then .state else error("schema") end' "$work/status.json" 2>/dev/null)"; then
      case "$state" in
        failure | error)
          printf 'ci:%s:%s:%s\tPR #%s CI %s (%s)\n' \
            "$project" "$number" "$sha" "$number" "$state" "${sha:0:8}" >>"$current"
          ;;
      esac
    else
      [[ -s "$work/error.json" ]] ||
        broker_failures+=("gitea.commit.status.read:RESPONSE_SCHEMA_INVALID")
      # Only this pull request's previous key is kept; the others were read.
      carry_over "ci:$project:$number:"
    fi
  done < <(jq -r '.[] | [((.number // "") | tostring), (.head.sha // "")] | @tsv' "$work/pulls.json")
else
  [[ -s "$work/error.json" ]] || broker_failures+=("gitea.pulls.read:RESPONSE_SCHEMA_INVALID")
  carry_over "ci:$project:"
fi

# VM timers: an enabled timer whose service failed in the last 24 hours.
if broker_call orbstack.vm.units.read "$work/units.json" &&
  jq -e '(.timers | type) == "array" and all(.timers[];
    (.timer | type) == "string" and (.enabled | type) == "boolean"
    and (.failures_24h | type) == "number")' "$work/units.json" >/dev/null 2>&1; then
  jq -r '.timers[] | select(.enabled and .failures_24h > 0)
    | "timer:\(.timer)\t\(.timer) failed \(.failures_24h) times in 24h"' \
    "$work/units.json" >>"$current"
else
  [[ -s "$work/error.json" ]] || broker_failures+=("orbstack.vm.units.read:RESPONSE_SCHEMA_INVALID")
  carry_over "timer:"
fi

if [[ "${#broker_failures[@]}" -gt 0 ]]; then
  # One key for the whole outage: the first failing operation names it in the
  # message, but later runs with other failing operations do not re-notify.
  printf 'broker:unavailable\tbroker unreadable: %s\n' "${broker_failures[0]}" >>"$current"
fi

sort -u -t $'\t' -k1,1 "$current" >"$work/next.tsv"
cut -f1 "$state_file" >"$work/previous-keys"

# New = keys active now that were not active on the previous run.
new_count=0
while IFS=$'\t' read -r key message; do
  grep -Fxq -- "$key" "$work/previous-keys" && continue
  new_count=$((new_count + 1))
  if ((new_count <= max_notifications)); then
    notify "AISoft alert ($project)" "$message"
  fi
done <"$work/next.tsv"
if ((new_count > max_notifications)); then
  notify "AISoft alert ($project)" "$((new_count - max_notifications)) more new failures; see readiness"
fi

mv -f -- "$work/next.tsv" "$state_file"
chmod 600 "$state_file"
echo "ALERTS active=$(wc -l <"$state_file" | tr -d ' ') new=$new_count broker_failures=${#broker_failures[@]}"

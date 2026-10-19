#!/usr/bin/env bash
# Install or remove the owner's Mac failure-alert agent (#387, 05 §5).
#
# Installs a copy of aisoft-alert-poll.sh and a per-user launchd agent that runs
# it every 15 minutes. User scope only: no sudo, nothing under /usr/local or
# /Library, and no credential is read or written. --uninstall boots the agent
# out and removes exactly the files this script installed.
set -euo pipefail
# bash 5.2 would read "&" in a replacement as the matched text; 3.2 has no such
# option, so the failure of shopt there is expected.
shopt -u patsub_replacement 2>/dev/null || true

root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
label="com.aisoft.platform-alerts"
target_home="$HOME"
action="install"
# Tests replace launchctl; it must accept bootstrap/bootout like the real one.
launchctl_bin="${AISOFT_LAUNCHCTL:-/bin/launchctl}"

usage() {
  cat <<'EOF'
Usage: install-alert-agent.sh [--uninstall] [--home PATH]

Install: copies the poller to ~/Library/Application Support/AISoftPlatform/alerts,
renders ~/Library/LaunchAgents/com.aisoft.platform-alerts.plist from
codex/launchd and loads it for the current user (runs at load, then every 900s).
Uninstall: launchctl bootout, then removes the plist and the poller copy. The
alert state and log in the alerts directory are removed too.
EOF
}

while (($#)); do
  case "$1" in
    --uninstall)
      action="uninstall"
      shift
      ;;
    --home)
      (($# >= 2)) || {
        usage >&2
        exit 2
      }
      target_home="$2"
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

alerts_dir="$target_home/Library/Application Support/AISoftPlatform/alerts"
poller="$alerts_dir/aisoft-alert-poll.sh"
plist="$target_home/Library/LaunchAgents/$label.plist"
domain="gui/$(id -u)"

xml_escape() {
  local value="$1"
  value="${value//&/&amp;}"
  value="${value//</&lt;}"
  value="${value//>/&gt;}"
  printf '%s' "$value"
}

if [[ "$action" == "uninstall" ]]; then
  "$launchctl_bin" bootout "$domain/$label" 2>/dev/null || true
  rm -f -- "$plist" "$poller" "$alerts_dir/active-alerts.tsv" "$alerts_dir/poll.log"
  rmdir -- "$alerts_dir" 2>/dev/null || true
  echo "UNINSTALLED $label"
  exit 0
fi

template="$root/codex/launchd/$label.plist.template"
source_poller="$root/codex/tools/aisoft-alert-poll.sh"
[[ -f "$template" && -f "$source_poller" ]] || {
  echo "BLOCKED source files missing under $root" >&2
  exit 1
}

mkdir -p -- "$alerts_dir" "$(dirname -- "$plist")"
chmod 700 "$alerts_dir"
install -m 0755 "$source_poller" "$poller"

rendered="$(<"$template")"
rendered="${rendered//__POLL_SCRIPT__/$(xml_escape "$poller")}"
rendered="${rendered//__STATE_DIR__/$(xml_escape "$alerts_dir")}"
printf '%s\n' "$rendered" >"$plist.tmp"
chmod 644 "$plist.tmp"
mv -f -- "$plist.tmp" "$plist"

# Reload so a reinstall picks up a new poller or plist.
"$launchctl_bin" bootout "$domain/$label" 2>/dev/null || true
"$launchctl_bin" bootstrap "$domain" "$plist"

echo "INSTALLED $label plist=$plist poller=$poller"
echo "Uninstall: bash $root/codex/tools/install-alert-agent.sh --uninstall"

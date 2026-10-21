#!/usr/bin/env bash
# Read-only source / installed / live readiness report. Never installs or mutates.
set -euo pipefail

root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
repo="$root"
project="aisoft-platform"
target_home="$HOME"
broker="${AISOFT_HOST_ACCESS_BROKER:-/usr/local/libexec/aisoft/host-access-broker}"
credential_root=""

usage() {
  cat <<'EOF'
Usage: aisoft-platform-readiness.sh [--repo PATH] [--project ID] [--home PATH] [--broker PATH]
                                    [--credential-root PATH]

Reports sanitized SOURCE, INSTALLED_CODEX, INSTALLED_CLAUDE, LIVE_REPO,
LIVE_PROTECTION and LIVE_VM_TIMERS states. The command is read-only and exits 1
when any layer is DRIFT, GAP or BLOCKED. PAT_AGE is a NOTE only (#397): the age
of each manifest-declared Mac credential against the 180-day rotation period,
from its rotation receipt or else its creation marker; it never reads a token
and never changes the exit code.
EOF
}

while (($#)); do
  case "$1" in
    --repo | --project | --home | --broker | --credential-root)
      (($# >= 2)) || {
        usage >&2
        exit 2
      }
      case "$1" in
        --repo) repo="$2" ;;
        --project) project="$2" ;;
        --home) target_home="$2" ;;
        --broker) broker="$2" ;;
        --credential-root) credential_root="$2" ;;
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

git -C "$repo" rev-parse --git-dir >/dev/null 2>&1 || {
  echo 'SOURCE BLOCKED repository-unavailable'
  exit 1
}
command -v jq >/dev/null || {
  echo 'SOURCE BLOCKED jq-unavailable'
  exit 1
}

overall=0
source_sha="$(git -C "$repo" rev-parse HEAD 2>/dev/null || true)"
label_manifest="$repo/codex/config/gitea-labels.json"
if [[ -n "$source_sha" && -f "$label_manifest" ]] &&
  [[ "$(jq '[.canonical[] | select(.name | startswith("type/"))] | length' "$label_manifest")" == "10" ]] &&
  [[ "$(jq '.canonical | length' "$label_manifest")" == "27" ]]; then
  echo "SOURCE PASS sha=${source_sha:0:12} types=10 labels=27"
else
  echo 'SOURCE GAP invalid-sha-or-label-contract'
  overall=1
fi

skill_state() {
  local label="$1" checker="$2" output
  if output="$(bash "$checker" "$target_home" 2>/dev/null)"; then
    case "$output" in
      CLEAN) echo "$label PASS" ;;
      NOT_INSTALLED) echo "$label NOT_INSTALLED" ;;
      *)
        echo "$label GAP unexpected-checker-output"
        return 1
        ;;
    esac
  else
    echo "$label DRIFT items=$(grep -c '^DRIFT:' <<<"$output" || true)"
    return 1
  fi
}

skill_state INSTALLED_CODEX "$repo/codex/check-drift.sh" || overall=1
skill_state INSTALLED_CLAUDE "$repo/skill-for-claude/check-drift.sh" || overall=1

if [[ ! -x "$broker" ]]; then
  echo 'LIVE_REPO BLOCKED broker-unavailable'
  echo 'LIVE_PROTECTION BLOCKED broker-unavailable'
  echo 'LIVE_VM_TIMERS BLOCKED broker-unavailable'
  overall=1
else
  temp_root="$(mktemp -d)"
  trap 'rm -rf "$temp_root"' EXIT

  if "$broker" --project "$project" --operation gitea.repo.read >"$temp_root/repo.json" 2>/dev/null &&
    jq -e '.default_branch == "main" and .has_actions == true' "$temp_root/repo.json" >/dev/null; then
    echo 'LIVE_REPO PASS default_branch=main actions=true'
  else
    echo 'LIVE_REPO BLOCKED unreadable-or-contract-gap'
    overall=1
  fi

  if "$broker" --project "$project" --operation gitea.protection.read >"$temp_root/protection.json" 2>/dev/null; then
    enabled="$(jq -r '.enable_status_check // false' "$temp_root/protection.json")"
    contexts="$(jq -r '(.status_check_contexts // []) | length' "$temp_root/protection.json")"
    if [[ "$enabled" == "true" && "$contexts" -gt 0 ]]; then
      echo "LIVE_PROTECTION PASS status_check=true contexts=$contexts"
    else
      echo "LIVE_PROTECTION GAP status_check=$enabled contexts=$contexts"
      overall=1
    fi
  else
    echo 'LIVE_PROTECTION BLOCKED unreadable'
    overall=1
  fi

  # #387: an enabled timer whose service failed in the last 24 hours is a GAP
  # even though the timer itself still reads "active (waiting)".
  if "$broker" --project "$project" --operation orbstack.vm.units.read \
    >"$temp_root/units.json" 2>"$temp_root/units.err" &&
    jq -e '(.timers | type) == "array" and all(.timers[];
      (.timer | type) == "string" and (.enabled | type) == "boolean"
      and (.failures_24h | type) == "number")' "$temp_root/units.json" >/dev/null 2>&1; then
    enabled_timers="$(jq '[.timers[] | select(.enabled == true)] | length' "$temp_root/units.json")"
    failing_timers="$(jq -r '[.timers[] | select(.enabled and .failures_24h > 0)
      | "\(.timer):\(.failures_24h)"] | join(",")' "$temp_root/units.json")"
    if [[ -z "$failing_timers" ]]; then
      echo "LIVE_VM_TIMERS PASS enabled=$enabled_timers failing=0"
    else
      echo "LIVE_VM_TIMERS GAP enabled=$enabled_timers failing=$failing_timers"
      overall=1
    fi
  elif jq -e '.code == "REQUEST_DENIED" and (.message | test("not allowlisted"))' \
    "$temp_root/units.err" >/dev/null 2>&1; then
    # The installed broker predates the operation: reinstall both hosts.
    echo 'LIVE_VM_TIMERS BLOCKED operation-not-installed'
    overall=1
  else
    echo 'LIVE_VM_TIMERS BLOCKED unreadable'
    overall=1
  fi
fi

# #397: PAT rotation period (06 §4). Ages come from non-secret metadata only:
# the observed_at of a completed rotation receipt, else the mtime of the
# creation marker the bootstrap wrote. Token files are never opened.
python3 -I - "$repo/codex/config/host-access-broker.json" "$credential_root" <<'PY' || echo 'PAT_AGE NOTE unreadable'
import json, os, stat, sys, time
from pathlib import Path

LIMIT_DAYS = 180
manifest = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
root = Path(sys.argv[2] or manifest["site"]["credential_root_mac"])
bindings = manifest["identity_bindings"]
targets = [("manager-audit", bindings["manager_audit"]["relative_path"]),
           ("manager-mutation", bindings["manager_mutation"]["relative_path"])]
template = bindings["project_agent"]["relative_path_template"]
targets += [("project-agent", template.format(project_id=p["project_id"])) for p in manifest["projects"]]

def issued(kind, relative):
    parent = root / Path(relative).parent
    receipt = parent / (".rotation-" + kind) / "provenance.json"
    journal = receipt.with_name("journal.json")
    try:
        # provenance.json is written before the transaction completes; only a
        # journal in phase complete makes its time a finished rotation.
        if (stat.S_ISREG(os.lstat(receipt).st_mode) and stat.S_ISREG(os.lstat(journal).st_mode)
                and json.loads(journal.read_text(encoding="utf-8")).get("phase") == "complete"):
            value = json.loads(receipt.read_text(encoding="utf-8")).get("observed_at")
            if type(value) is int and value > 0:
                return value, "receipt"
    except (OSError, ValueError):
        pass
    try:
        prefix = Path(relative).name + "-created-by-issue-"
        times = [os.lstat(entry.path).st_mtime for entry in os.scandir(parent)
                 if entry.name.startswith(prefix) and entry.is_file(follow_symlinks=False)]
    except OSError:
        times = []
    return (int(max(times)), "marker") if times else (None, "unknown")

now, over, unknown, rows = time.time(), 0, 0, []
for kind, relative in targets:
    when, source = issued(kind, relative)
    if when is None:
        unknown += 1
        rows.append(f"  PAT_AGE {relative} unknown")
        continue
    days = int((now - when) // 86400)
    over += days > LIMIT_DAYS
    rows.append(f"  PAT_AGE {relative} {days}d source={source}" + (" OVER" if days > LIMIT_DAYS else ""))
print(f"PAT_AGE NOTE checked={len(targets)} over_{LIMIT_DAYS}d={over} unknown={unknown}")
print("\n".join(rows))
PY

exit "$overall"

#!/usr/bin/env bash
# Read-only source / installed / live readiness report. Never installs or mutates.
set -euo pipefail

root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
repo="$root"
project="aisoft-platform"
target_home="$HOME"
broker="${AISOFT_HOST_ACCESS_BROKER:-/usr/local/libexec/aisoft/host-access-broker}"

usage() {
  cat <<'EOF'
Usage: aisoft-platform-readiness.sh [--repo PATH] [--project ID] [--home PATH] [--broker PATH]

Reports sanitized SOURCE, INSTALLED_CODEX, INSTALLED_CLAUDE, LIVE_REPO and
LIVE_PROTECTION states. The command is read-only and exits 1 when any layer is
DRIFT, GAP or BLOCKED.
EOF
}

while (($#)); do
  case "$1" in
    --repo | --project | --home | --broker)
      (($# >= 2)) || {
        usage >&2
        exit 2
      }
      case "$1" in
        --repo) repo="$2" ;;
        --project) project="$2" ;;
        --home) target_home="$2" ;;
        --broker) broker="$2" ;;
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
fi

exit "$overall"

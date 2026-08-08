#!/usr/bin/env bash
set -euo pipefail
set +x

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
manifest=''
config=''
mode='check'
merged_sha=''
platform_root=''
evidence_dir=''
backup=''

usage() {
  printf '%s\n' \
    "usage: $0 --manifest FILE --config FILE [--check | --apply --merged-sha SHA --platform-root DIR --evidence-dir DIR | --rollback BACKUP --merged-sha SHA --platform-root DIR]" >&2
  exit 2
}

while (($#)); do
  case "$1" in
    --manifest) manifest="${2:-}"; shift 2 ;;
    --config) config="${2:-}"; shift 2 ;;
    --check) mode=check; shift ;;
    --apply) mode=apply; shift ;;
    --rollback) mode=rollback; backup="${2:-}"; shift 2 ;;
    --merged-sha) merged_sha="${2:-}"; shift 2 ;;
    --platform-root) platform_root="${2:-}"; shift 2 ;;
    --evidence-dir) evidence_dir="${2:-}"; shift 2 ;;
    *) usage ;;
  esac
done

[[ -n "$manifest" && -n "$config" ]] || usage
[[ -f "$config" && ! -L "$config" ]] || {
  printf '%s\n' 'BLOCKED_EXTERNAL: config must be a regular non-symlink file' >&2
  exit 2
}

for command in python3 jq git install mktemp stat; do
  command -v "$command" >/dev/null || {
    printf 'BLOCKED_EXTERNAL: required command is missing: %s\n' "$command" >&2
    exit 2
  }
done

export PYTHONPATH="$ROOT/codex/runtime${PYTHONPATH:+:$PYTHONPATH}"
python3 -m aisoft_gitea_governance.cli --manifest "$manifest" validate >/dev/null

expected_disable_registration="$(jq -r '.server_policy.disable_registration' "$manifest")"
expected_default_private="$(jq -r '.server_policy.default_private' "$manifest")"
expected_force_private="$(jq -r '.server_policy.force_private' "$manifest")"
expected_require_signin="$(jq -r '.server_policy.require_signin_view' "$manifest")"

check_policy() {
  local target="$1"
  local values disable_registration default_private force_private require_signin result
  values="$(python3 -m aisoft_gitea_governance.service_policy \
    --manifest "$manifest" read --config "$target")"
  disable_registration="$(jq -r '.disable_registration' <<<"$values")"
  default_private="$(jq -r '.default_private' <<<"$values")"
  force_private="$(jq -r '.force_private' <<<"$values")"
  require_signin="$(jq -r '.require_signin_view' <<<"$values")"
  result=PASS
  [[ "$disable_registration" == "$expected_disable_registration" ]] || result=DRIFT
  [[ "$default_private" == "$expected_default_private" ]] || result=DRIFT
  [[ "$force_private" == "$expected_force_private" ]] || result=DRIFT
  [[ "$require_signin" == "$expected_require_signin" ]] || result=DRIFT
  jq -cn \
    --arg disable_registration "$disable_registration" \
    --arg default_private "$default_private" \
    --arg force_private "$force_private" \
    --arg require_signin "$require_signin" \
    --arg result "$result" \
    '{disable_registration:$disable_registration,default_private:$default_private,force_private:$force_private,require_signin_view:$require_signin,result:$result}'
  [[ "$result" == PASS ]]
}

if [[ "$mode" == check ]]; then
  check_policy "$config"
  exit $?
fi

[[ "${AISOFT_SERVICE_POLICY_MODE:-}" == "approved-issue-35" ]] || {
  printf '%s\n' 'BLOCKED_EXTERNAL: AISOFT_SERVICE_POLICY_MODE=approved-issue-35 is required' >&2
  exit 2
}
[[ -n "$merged_sha" && -n "$platform_root" ]] || usage
if [[ "${AISOFT_ALLOW_TEST_CONFIG:-}" != true ]]; then
  python3 -m aisoft_gitea_governance.cli --manifest "$manifest" verify-merged \
    --issue 35 --merged-sha "$merged_sha" --platform-root "$platform_root" >/dev/null
fi
[[ "$(id -u)" == 0 || "${AISOFT_ALLOW_TEST_CONFIG:-}" == true ]] || {
  printf '%s\n' 'BLOCKED_EXTERNAL: service policy mutation must run as root' >&2
  exit 2
}

GITEA_BIN="${GITEA_BIN:-/usr/local/bin/gitea}"
GITEA_HEALTH_URL="${GITEA_HEALTH_URL:-http://127.0.0.1:3000/api/healthz}"
SYSTEMCTL_BIN="${SYSTEMCTL_BIN:-systemctl}"
[[ -x "$GITEA_BIN" ]] || {
  printf '%s\n' 'BLOCKED_EXTERNAL: Gitea binary is unavailable' >&2
  exit 2
}

config_uid="$(stat -c '%u' "$config" 2>/dev/null || stat -f '%u' "$config")"
config_gid="$(stat -c '%g' "$config" 2>/dev/null || stat -f '%g' "$config")"
config_mode="$(stat -c '%a' "$config" 2>/dev/null || stat -f '%Lp' "$config")"

restart_and_verify() {
  "$SYSTEMCTL_BIN" restart gitea.service
  "$SYSTEMCTL_BIN" is-active --quiet gitea.service
  curl --fail --silent --show-error "$GITEA_HEALTH_URL" >/dev/null
}

install_config() {
  if [[ "${AISOFT_ALLOW_TEST_CONFIG:-}" == true ]]; then
    install -m "$config_mode" "$1" "$config"
  else
    install -o "$config_uid" -g "$config_gid" -m "$config_mode" "$1" "$config"
  fi
}

sha256_file() {
  if command -v sha256sum >/dev/null; then
    sha256sum "$1" | awk '{print $1}'
  elif command -v shasum >/dev/null; then
    shasum -a 256 "$1" | awk '{print $1}'
  else
    printf '%s\n' 'BLOCKED_EXTERNAL: sha256sum or shasum is required' >&2
    return 2
  fi
}

if [[ "$mode" == rollback ]]; then
  [[ -n "$backup" && -f "$backup" && ! -L "$backup" ]] || {
    printf '%s\n' 'BLOCKED_EXTERNAL: rollback backup must be a regular file' >&2
    exit 2
  }
  install_config "$backup"
  restart_and_verify
  checksum="$(sha256_file "$config")"
  jq -cn --arg result rollback-applied --arg checksum "$checksum" \
    '{result:$result,config_sha256:$checksum,health:"PASS"}'
  exit 0
fi

[[ -n "$evidence_dir" ]] || usage
if [[ "${AISOFT_ALLOW_TEST_CONFIG:-}" != true ]]; then
  case "$evidence_dir" in
    /var/lib/aisoft/backups/gitea-policy/*) ;;
    *)
      printf '%s\n' 'BLOCKED_EXTERNAL: evidence directory must be under /var/lib/aisoft/backups/gitea-policy' >&2
      exit 2
      ;;
  esac
fi
[[ ! -e "$evidence_dir" ]] || {
  printf '%s\n' 'BLOCKED_EXTERNAL: refusing to overwrite service policy evidence directory' >&2
  exit 2
}
mkdir -p "$evidence_dir"
chmod 700 "$evidence_dir"

tmp_dir="$(mktemp -d)"
chmod 700 "$tmp_dir"
trap 'rm -rf -- "$tmp_dir"' EXIT
cp -p "$config" "$evidence_dir/app.ini.pre"
chmod 600 "$evidence_dir/app.ini.pre"
python3 -m aisoft_gitea_governance.service_policy \
  --manifest "$manifest" render --config "$config" \
  --output "$tmp_dir/app.ini.candidate" >/dev/null
check_policy "$tmp_dir/app.ini.candidate" >/dev/null

"$GITEA_BIN" --config "$tmp_dir/app.ini.candidate" doctor check --all >/dev/null
install_config "$tmp_dir/app.ini.candidate"

if ! restart_and_verify; then
  install_config "$evidence_dir/app.ini.pre"
  restart_and_verify || true
  printf '%s\n' 'BLOCKED_EXTERNAL: service restart/health failed; original config restored' >&2
  exit 2
fi

cp -p "$config" "$evidence_dir/app.ini.post"
chmod 600 "$evidence_dir/app.ini.post"
pre_checksum="$(sha256_file "$evidence_dir/app.ini.pre")"
post_checksum="$(sha256_file "$evidence_dir/app.ini.post")"
policy="$(check_policy "$config")"
jq -cn \
  --arg result applied \
  --arg pre_checksum "$pre_checksum" \
  --arg post_checksum "$post_checksum" \
  --argjson policy "$policy" \
  '{result:$result,pre_config_sha256:$pre_checksum,post_config_sha256:$post_checksum,policy:$policy,health:"PASS"}'

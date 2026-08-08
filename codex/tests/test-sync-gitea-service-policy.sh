#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf -- "$TMP"' EXIT
mkdir -p "$TMP/bin"

cat >"$TMP/app.ini" <<'INI'
[service]
DISABLE_REGISTRATION = false
REQUIRE_SIGNIN_VIEW = false

[repository]
DEFAULT_PRIVATE = last
FORCE_PRIVATE = false
INI
chmod 600 "$TMP/app.ini"

cat >"$TMP/bin/gitea" <<'MOCK'
#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' "$*" >>"$MOCK_ROOT/gitea-argv.log"
[[ "$*" == *"doctor check --all"* ]]
[[ ! -f "$MOCK_ROOT/doctor-fail" ]]
MOCK

cat >"$TMP/bin/sudo" <<'MOCK'
#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' "$*" >>"$MOCK_ROOT/sudo-argv.log"
[[ "${1:-}" == -n ]]
[[ "${2:-}" == -u ]]
[[ "${3:-}" == git ]]
shift 3
exec "$@"
MOCK

cat >"$TMP/bin/systemctl" <<'MOCK'
#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' "$*" >>"$MOCK_ROOT/systemctl-argv.log"
case "$1" in
  restart) exit 0 ;;
  is-active) exit 0 ;;
  *) exit 2 ;;
esac
MOCK

cat >"$TMP/bin/curl" <<'MOCK'
#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' "$*" >>"$MOCK_ROOT/curl-argv.log"
printf '{"status":"pass"}\n'
MOCK

chmod +x "$TMP/bin/gitea" "$TMP/bin/sudo" "$TMP/bin/systemctl" "$TMP/bin/curl"
export MOCK_ROOT="$TMP"
export PATH="$TMP/bin:$PATH"
export AISOFT_ALLOW_TEST_CONFIG=true
export AISOFT_SERVICE_POLICY_MODE=approved-issue-35
export GITEA_BIN="$TMP/bin/gitea"
export SUDO_BIN="$TMP/bin/sudo"
export SYSTEMCTL_BIN="$TMP/bin/systemctl"
export GITEA_HEALTH_URL=http://127.0.0.1:3000/api/healthz

if bash "$ROOT/codex/tools/sync-gitea-service-policy.sh" \
  --manifest "$ROOT/codex/config/gitea-governance.json" \
  --config "$TMP/app.ini" --check >"$TMP/check-before.json"; then
  printf '%s\n' 'drifted service policy unexpectedly passed' >&2
  exit 1
fi
[[ "$(jq -r '.result' "$TMP/check-before.json")" == DRIFT ]]

result="$(bash "$ROOT/codex/tools/sync-gitea-service-policy.sh" \
  --manifest "$ROOT/codex/config/gitea-governance.json" \
  --config "$TMP/app.ini" --apply \
  --merged-sha 1111111111111111111111111111111111111111 \
  --platform-root "$ROOT" \
  --evidence-dir "$TMP/evidence")"
[[ "$(jq -r '.result' <<<"$result")" == applied ]]
grep -Eq '^DISABLE_REGISTRATION = true$' "$TMP/app.ini"
grep -Eq '^REQUIRE_SIGNIN_VIEW = false$' "$TMP/app.ini"
grep -Eq '^DEFAULT_PRIVATE = private$' "$TMP/app.ini"
grep -Eq '^FORCE_PRIVATE = false$' "$TMP/app.ini"
[[ "$(grep -c '^restart gitea.service$' "$TMP/systemctl-argv.log")" == 1 ]]

bash "$ROOT/codex/tools/sync-gitea-service-policy.sh" \
  --manifest "$ROOT/codex/config/gitea-governance.json" \
  --config "$TMP/app.ini" --check >"$TMP/check-after.json"
[[ "$(jq -r '.result' "$TMP/check-after.json")" == PASS ]]

bash "$ROOT/codex/tools/sync-gitea-service-policy.sh" \
  --manifest "$ROOT/codex/config/gitea-governance.json" \
  --config "$TMP/app.ini" --rollback "$TMP/evidence/app.ini.pre" \
  --merged-sha 1111111111111111111111111111111111111111 \
  --platform-root "$ROOT" >"$TMP/rollback.json"
[[ "$(jq -r '.result' "$TMP/rollback.json")" == rollback-applied ]]
grep -Eq '^DISABLE_REGISTRATION = false$' "$TMP/app.ini"
grep -Eq '^DEFAULT_PRIVATE = last$' "$TMP/app.ini"

cp "$TMP/app.ini" "$TMP/app.ini.before-failure"
touch "$TMP/doctor-fail"
if bash "$ROOT/codex/tools/sync-gitea-service-policy.sh" \
  --manifest "$ROOT/codex/config/gitea-governance.json" \
  --config "$TMP/app.ini" --apply \
  --merged-sha 1111111111111111111111111111111111111111 \
  --platform-root "$ROOT" \
  --evidence-dir "$TMP/evidence-failure" \
  >"$TMP/failure.out" 2>"$TMP/failure.err"; then
  printf '%s\n' 'invalid candidate unexpectedly restarted' >&2
  exit 1
fi
cmp "$TMP/app.ini.before-failure" "$TMP/app.ini"
[[ "$(grep -c '^restart gitea.service$' "$TMP/systemctl-argv.log")" == 2 ]]
[[ "$(grep -c '^-n -u git .*doctor check --all$' "$TMP/sudo-argv.log")" == 2 ]]

if GITEA_SERVICE_USER='git;root' bash "$ROOT/codex/tools/sync-gitea-service-policy.sh" \
  --manifest "$ROOT/codex/config/gitea-governance.json" \
  --config "$TMP/app.ini" --apply \
  --merged-sha 1111111111111111111111111111111111111111 \
  --platform-root "$ROOT" \
  --evidence-dir "$TMP/evidence-unsafe-user" \
  >"$TMP/unsafe-user.out" 2>"$TMP/unsafe-user.err"; then
  printf '%s\n' 'unsafe Gitea service user unexpectedly passed' >&2
  exit 1
fi
grep -Fq 'unsafe Gitea service user' "$TMP/unsafe-user.err"

printf '%s\n' 'Gitea service policy tests passed'

#!/usr/bin/env bash
set -euo pipefail

root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
script="$root/codex/tools/gitea-readonly.sh"
test_root="$(mktemp -d)"
trap 'rm -rf "$test_root"' EXIT

mkdir -p "$test_root/bin"
cat >"$test_root/bin/curl" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
config="$(cat)"
printf '%s' "$config" >"$CAPTURE_CONFIG"
printf '%s\n' "$*" >"$CAPTURE_ARGV"
printf '{"ok":true}\n'
EOF
chmod 755 "$test_root/bin/curl"

profile="$test_root/project.env"
cat >"$profile" <<'EOF'
GITEA_URL=http://gitea.test:3000
GITEA_OWNER=admin
GITEA_REPO=private-repo
GITEA_TOKEN=sentinel-profile-token
EOF
chmod 600 "$profile"

export PATH="$test_root/bin:$PATH"
export CAPTURE_CONFIG="$test_root/config"
export CAPTURE_ARGV="$test_root/argv"

output="$(
  AGENT_ENV_FILE="$profile" \
  GITEA_EXPECT_OWNER=admin \
  GITEA_EXPECT_REPO=private-repo \
    "$script" 'issues?state=all&type=issues&limit=20'
)"
[[ "$output" == '{"ok":true}' ]]
grep -Fq 'Authorization: token sentinel-profile-token' "$CAPTURE_CONFIG"
grep -Fq -- '--request GET' "$CAPTURE_ARGV"
grep -Fq '/api/v1/repos/admin/private-repo/issues?state=all&type=issues&limit=20' \
  "$CAPTURE_ARGV"
if grep -Fq 'sentinel-profile-token' "$CAPTURE_ARGV" ||
   grep -Fq 'sentinel-profile-token' <<<"$output"; then
  echo 'token leaked into argv or output' >&2
  exit 1
fi

credential_file="$test_root/credentials"
printf '%s\n' 'admin token: sentinel-admin-token' >"$credential_file"
chmod 600 "$credential_file"
output="$(
  GITEA_URL=http://127.0.0.1:3000 \
  GITEA_OWNER=admin \
  GITEA_REPO=private-repo \
  GITEA_CREDENTIAL_FILE="$credential_file" \
    "$script" repo
)"
[[ "$output" == '{"ok":true}' ]]
grep -Fq 'Authorization: token sentinel-admin-token' "$CAPTURE_CONFIG"
if grep -Fq 'sentinel-admin-token' "$CAPTURE_ARGV" ||
   grep -Fq 'sentinel-admin-token' <<<"$output"; then
  echo 'fallback token leaked into argv or output' >&2
  exit 1
fi

# #416: without GITEA_CREDENTIAL_FILE the default file is
# $HOME/<site.orbstack_machine>-credentials.txt from the manifest beside the script.
site_layout="$test_root/site-layout"
mkdir -p "$site_layout/codex/tools" "$site_layout/codex/config" "$test_root/home"
cp "$script" "$site_layout/codex/tools/gitea-readonly.sh"
printf '%s\n' '{"site": {}}' >"$site_layout/codex/config/host-access-broker.json"
if HOME="$test_root/home" GITEA_URL=http://127.0.0.1:3000 GITEA_OWNER=admin \
  GITEA_REPO=private-repo "$site_layout/codex/tools/gitea-readonly.sh" repo \
  >/dev/null 2>"$test_root/no-site.err"; then
  echo 'missing site.orbstack_machine should fail' >&2
  exit 1
fi
grep -Fq 'set GITEA_CREDENTIAL_FILE or site.orbstack_machine' "$test_root/no-site.err"
printf '%s\n' '{"site": {"orbstack_machine": "sample-vm"}}' \
  >"$site_layout/codex/config/host-access-broker.json"
printf '%s\n' 'admin token: sentinel-site-token' >"$test_root/home/sample-vm-credentials.txt"
chmod 600 "$test_root/home/sample-vm-credentials.txt"
output="$(
  HOME="$test_root/home" GITEA_URL=http://127.0.0.1:3000 GITEA_OWNER=admin \
  GITEA_REPO=private-repo "$site_layout/codex/tools/gitea-readonly.sh" repo
)"
[[ "$output" == '{"ok":true}' ]]
grep -Fq 'Authorization: token sentinel-site-token' "$CAPTURE_CONFIG"

if AGENT_ENV_FILE="$profile" GITEA_EXPECT_REPO=wrong \
  "$script" repo >/dev/null 2>&1; then
  echo 'target mismatch should fail' >&2
  exit 1
fi

if AGENT_ENV_FILE="$profile" "$script" '../users' >/dev/null 2>&1; then
  echo 'unsafe resource should fail' >&2
  exit 1
fi
if AGENT_ENV_FILE="$profile" "$script" '%2e%2e/users' >/dev/null 2>&1; then
  echo 'encoded path traversal should fail' >&2
  exit 1
fi

chmod 644 "$profile"
if AGENT_ENV_FILE="$profile" "$script" repo >/dev/null 2>&1; then
  echo 'permissive profile mode should fail' >&2
  exit 1
fi

printf '%s\n' 'gitea-readonly tests passed'

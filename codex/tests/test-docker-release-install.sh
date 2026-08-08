#!/usr/bin/env bash
set -euo pipefail

root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
test_root="$(mktemp -d)"
trap 'rm -rf "$test_root"' EXIT

mkdir -p "$test_root/bin"
cat >"$test_root/bin/docker" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' 'installer unexpectedly called Docker' >>"${FAKE_DOCKER_LOG:?}"
exit 99
SH
chmod 0755 "$test_root/bin/docker"
export PATH="$test_root/bin:$PATH"
export FAKE_DOCKER_LOG="$test_root/docker.log"
export AISOFT_DOCKER_RELEASE_INSTALL_ROOT="$test_root/root"

first_output="$(bash "$root/docker-release/install.sh")"
grep -Fq 'no target profile, secret, Docker login, systemd unit or deployment was created' \
  <<<"$first_output"

first_manifest="$test_root/first.manifest"
second_manifest="$test_root/second.manifest"
find "$test_root/root" -type f -print0 | sort -z | xargs -0 shasum -a 256 >"$first_manifest"
second_output="$(bash "$root/docker-release/install.sh")"
grep -Fq 'no target profile, secret, Docker login, systemd unit or deployment was created' \
  <<<"$second_output"
find "$test_root/root" -type f -print0 | sort -z | xargs -0 shasum -a 256 >"$second_manifest"
cmp "$first_manifest" "$second_manifest"

test -x "$test_root/root/usr/local/bin/aisoft-docker-release"
test -x "$test_root/root/usr/local/bin/aisoft-docker-release-gate"
test -f "$test_root/root/opt/aisoft-docker-release/docker-release-v1/schema/release-manifest-v1.schema.json"
test -f "$test_root/root/opt/aisoft-docker-release/docker-release-v1/schema/release-manifest-v2.schema.json"
test -f "$test_root/root/opt/aisoft-docker-release/docker-release-v1/schema/state-v2.schema.json"
test -f "$test_root/root/opt/aisoft-docker-release/docker-release-v1/schema/command-gate-v1.schema.json"
test -f "$test_root/root/opt/aisoft-docker-release/docker-release-v1/schema/offline-inventory-v2.schema.json"
test -f "$test_root/root/opt/aisoft-docker-release/docker-release-v1/schema/image-store-compatibility-v1.schema.json"
test -f "$test_root/root/opt/aisoft-docker-release/docker-release-v1/compatibility/image-stores-v1.json"
test -f "$test_root/root/etc/aisoft-docker-release/examples/docker-release-v1/target-profile.example.json"
test -f "$test_root/root/etc/aisoft-docker-release/examples/docker-release-v1/action-grant.example.json"
test ! -e "$test_root/root/etc/aisoft-docker-release/targets"
test ! -e "$test_root/root/var/lib/aisoft-docker-release"
test ! -e "$test_root/root/etc/systemd/system"
test ! -e "$FAKE_DOCKER_LOG"

AISOFT_DOCKER_RELEASE_RUNTIME_DIR="$test_root/root/opt/aisoft-docker-release/docker-release-v1/runtime" \
  "$test_root/root/usr/local/bin/aisoft-docker-release" --help >/dev/null
installed_matrix="$(
  PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH="$test_root/root/opt/aisoft-docker-release/docker-release-v1/runtime" \
    python3 -B -c 'from aisoft_release.compatibility import default_compatibility_path; print(default_compatibility_path())'
)"
expected_matrix="$(
  cd -- "$test_root/root/opt/aisoft-docker-release/docker-release-v1/compatibility"
  pwd -P
)/image-stores-v1.json"
test "$installed_matrix" = \
  "$expected_matrix"
test ! -e "$FAKE_DOCKER_LOG"

printf '%s\n' 'docker release install tests passed'

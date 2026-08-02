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
test -f "$test_root/root/opt/aisoft-docker-release/docker-release-v1/schema/release-manifest-v1.schema.json"
test -f "$test_root/root/etc/aisoft-docker-release/examples/docker-release-v1/target-profile.example.json"
test ! -e "$test_root/root/etc/aisoft-docker-release/targets"
test ! -e "$test_root/root/var/lib/aisoft-docker-release"
test ! -e "$test_root/root/etc/systemd/system"
test ! -e "$FAKE_DOCKER_LOG"

AISOFT_DOCKER_RELEASE_RUNTIME_DIR="$test_root/root/opt/aisoft-docker-release/docker-release-v1/runtime" \
  "$test_root/root/usr/local/bin/aisoft-docker-release" --help >/dev/null
test ! -e "$FAKE_DOCKER_LOG"

printf '%s\n' 'docker release install tests passed'

#!/usr/bin/env bash
set -euo pipefail

source_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd -- "$source_root/.." && pwd)"
install_root="${AISOFT_DOCKER_RELEASE_INSTALL_ROOT:-/}"
runtime_root="$install_root/opt/aisoft-docker-release/docker-release-v1"
runtime_dir="$runtime_root/runtime/aisoft_release"
schema_dir="$runtime_root/schema"
example_dir="$install_root/etc/aisoft-docker-release/examples/docker-release-v1"
bin_dir="$install_root/usr/local/bin"

install -d -m 0755 "$runtime_dir" "$schema_dir" "$example_dir" "$bin_dir"
for source in "$repo_root"/codex/runtime/aisoft_release/*.py; do
  install -m 0644 "$source" "$runtime_dir/$(basename "$source")"
done
for source in "$source_root"/schema/*.json; do
  install -m 0644 "$source" "$schema_dir/$(basename "$source")"
done
install -m 0644 "$source_root/templates/target-profile.example.json" \
  "$example_dir/target-profile.example.json"
install -m 0755 "$source_root/bin/aisoft-docker-release" \
  "$bin_dir/aisoft-docker-release"

printf '%s\n' 'installed Docker release runtime, schemas, CLI and non-secret example'
printf '%s\n' 'no target profile, secret, Docker login, systemd unit or deployment was created'

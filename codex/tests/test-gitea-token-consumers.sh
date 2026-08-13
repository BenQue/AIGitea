#!/usr/bin/env bash
# Drift guard (#111): every shell script that consumes an inline GITEA_TOKEN
# must also support the post-#61 GITEA_TOKEN_FILE profile form — either
# directly or by sourcing the shared resolver codex/agent/gitea-token.sh.
# This blocks new inline-only consumers from landing after profile migration.
set -euo pipefail

root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"

scanned=0
violations=''
while IFS= read -r script; do
  scanned=$((scanned + 1))
  # Inline usage means GITEA_TOKEN not immediately followed by an underscore
  # (which would be the GITEA_TOKEN_FILE identifier).
  grep -Eq 'GITEA_TOKEN([^_]|$)' "$script" || continue
  if grep -Fq 'GITEA_TOKEN_FILE' "$script" ||
    grep -Fq 'gitea-token.sh' "$script"; then
    continue
  fi
  violations="$violations$script"$'\n'
done < <(
  find "$root/codex/tools" "$root/codex/agent" "$root/sync" \
    -maxdepth 1 -type f -name '*.sh' | LC_ALL=C sort
)

if ((scanned == 0)); then
  echo 'no consumer scripts were scanned; the drift guard is misconfigured' >&2
  exit 1
fi

if [[ -n "$violations" ]]; then
  printf '%s\n' \
    'inline-only GITEA_TOKEN consumers detected; they must accept GITEA_TOKEN_FILE or source codex/agent/gitea-token.sh (#111):' >&2
  printf '%s' "$violations" >&2
  exit 1
fi

printf 'gitea token consumer drift check passed (%d scripts scanned)\n' \
  "$scanned"

#!/usr/bin/env bash
# Fixed-manifest host access entrypoint. No URL, path, credential, shell, or merge input.
set -euo pipefail
set +x

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_ROOT="$(cd -- "$SCRIPT_DIR/../.." 2>/dev/null && pwd || true)"
if [[ -f "$SOURCE_ROOT/codex/config/host-access-broker.json" ]]; then
  RUNTIME_ROOT="$SOURCE_ROOT/codex/runtime"
  ACCESS_MANIFEST="$SOURCE_ROOT/codex/config/host-access-broker.json"
  GOVERNANCE_MANIFEST="$SOURCE_ROOT/codex/config/gitea-governance.json"
else
  RUNTIME_ROOT=/usr/local/lib/aisoft-host-access
  ACCESS_MANIFEST=/usr/local/share/aisoft/host-access-broker.json
  GOVERNANCE_MANIFEST=/usr/local/share/aisoft/gitea-governance.json
fi

export PYTHONPATH="$RUNTIME_ROOT${PYTHONPATH:+:$PYTHONPATH}"
exec python3 -m aisoft_host_access.cli \
  --access-manifest "$ACCESS_MANIFEST" \
  --governance-manifest "$GOVERNANCE_MANIFEST" \
  broker "$@"

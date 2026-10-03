#!/usr/bin/env bash
# Fixed operator entrypoint. Secret data may traverse only the private VM pipe.
set -euo pipefail
set +x

if [[ "${1:-}" == --vm-operation && ( -t 0 || -t 1 ) ]]; then
  printf '%s\n' '{"status":"BLOCKED_EXTERNAL","code":"ROTATION_PIPE_REQUIRED"}' >&2
  exit 20
fi

# No source-tree fallback and no caller PYTHONPATH/env-selected backend.
export PYTHONPATH=/usr/local/lib/aisoft-host-access
unset PYTHONHOME
exec python3 -I -c 'import sys; sys.path.insert(0,"/usr/local/lib/aisoft-host-access"); from aisoft_host_access.credential_rotation import operator_main; sys.exit(operator_main())' "$@"

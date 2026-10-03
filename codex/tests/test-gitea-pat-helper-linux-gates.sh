#!/usr/bin/env bash
# Black-box download gates: optimize mode cannot bypass checksum/path checks.
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf -- "$TMP"' EXIT
mkdir -p "$TMP/bin" "$TMP/repo/codex/tests" "$TMP/repo/codex/tools/gitea-pat-helper"
cp "$ROOT/codex/tests/test-gitea-pat-helper-linux.sh" "$TMP/repo/codex/tests/"
cat >"$TMP/bin/uname" <<'SH'
#!/usr/bin/env bash
[[ "$1" == -s ]] && printf 'Linux\n' || printf 'x86_64\n'
SH
cat >"$TMP/bin/curl" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
previous=''
for value in "$@"; do
  if [[ "$previous" == -o ]]; then cp "$GATE_ARCHIVE" "$value"; exit 0; fi
  previous="$value"
done
exit 2
SH
cat >"$TMP/bin/tar" <<'SH'
#!/usr/bin/env bash
touch "$GATE_TAR_CALLED"
exit 2
SH
chmod +x "$TMP/bin/"*
export GATE_ARCHIVE="$TMP/archive.tar.gz" GATE_TAR_CALLED="$TMP/tar-called"
for scenario in checksum traversal; do
  python3 - "$TMP" "$scenario" <<'PY'
import hashlib, io, json, sys, tarfile
from pathlib import Path
root=Path(sys.argv[1])
archive=root/'archive.tar.gz'
with tarfile.open(archive, 'w:gz') as packed:
 member=tarfile.TarInfo('go/../../escape')
 member.size=1
 packed.addfile(member, io.BytesIO(b'x'))
digest='0'*64 if sys.argv[2]=='checksum' else hashlib.sha256(archive.read_bytes()).hexdigest()
(root/'repo/codex/tools/gitea-pat-helper/build-lock.json').write_text(json.dumps({
 'version':'go1.26.3','files':[{'filename':'go1.26.3.linux-amd64.tar.gz','os':'linux','sha256':digest}]}))
PY
  if PATH="$TMP/bin:$PATH" PYTHONOPTIMIZE=1 bash "$TMP/repo/codex/tests/test-gitea-pat-helper-linux.sh" \
      --output "$TMP/no-artifact" >"$TMP/stdout" 2>"$TMP/stderr"; then
    printf '%s\n' 'FAIL: unsafe archive accepted' >&2; exit 1
  fi
  [[ ! -e "$GATE_TAR_CALLED" && ! -e "$TMP/no-artifact" ]]
  case "$scenario" in
    checksum) rg -q '^TOOLCHAIN_ARCHIVE_MISMATCH$' "$TMP/stderr" ;;
    traversal) rg -q '^TOOLCHAIN_ARCHIVE_UNSAFE$' "$TMP/stderr" ;;
  esac
done
printf '%s\n' 'PASS: optimized Linux download checksum/path gates reject before extraction'

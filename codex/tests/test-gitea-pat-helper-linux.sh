#!/usr/bin/env bash
# Native, pinned Linux build/test only. No installation or live Gitea access.
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
[[ "$(uname -s)" == Linux ]] || { printf '%s\n' 'LINUX_TEST_HOST_REQUIRED' >&2; exit 2; }
[[ $# == 2 && "$1" == --output && "$2" == /* ]] || { printf '%s\n' 'LINUX_TEST_OUTPUT_REQUIRED' >&2; exit 2; }
OUTPUT="$2"
HELPER="$ROOT/codex/tools/gitea-pat-helper"
TMP="$(mktemp -d)"
trap 'rm -rf -- "$TMP"' EXIT
case "$(uname -m)" in
  x86_64) ARCH=amd64 ;;
  aarch64|arm64) ARCH=arm64 ;;
  *) printf '%s\n' 'LINUX_TEST_ARCH_UNSUPPORTED' >&2; exit 2 ;;
esac
ARCHIVE="go1.26.3.linux-$ARCH.tar.gz"
python3 -I - "$HELPER/build-lock.json" "$ARCHIVE" >"$TMP/pin" <<'PY'
import json, sys
lock=json.load(open(sys.argv[1]))
pins=[p for p in lock['files'] if p['filename']==sys.argv[2] and p['os']=='linux']
if lock['version']!='go1.26.3' or len(pins)!=1:
 raise SystemExit('TOOLCHAIN_PIN_MISMATCH')
print(pins[0]['sha256'])
PY
curl --fail --silent --show-error --location --proto '=https' --proto-redir '=https' \
  --connect-timeout 15 --max-time 300 "https://go.dev/dl/$ARCHIVE" -o "$TMP/$ARCHIVE"
python3 -I - "$TMP/$ARCHIVE" "$TMP/pin" <<'PY'
from pathlib import Path, PurePosixPath
import hashlib, sys, tarfile
archive=Path(sys.argv[1])
if hashlib.sha256(archive.read_bytes()).hexdigest()!=Path(sys.argv[2]).read_text().strip():
 raise SystemExit('TOOLCHAIN_ARCHIVE_MISMATCH')
with tarfile.open(archive) as source:
 for member in source:
  parts=PurePosixPath(member.name).parts
  if not (parts and parts[0]=='go' and '..' not in parts and (member.isfile() or member.isdir())):
   raise SystemExit('TOOLCHAIN_ARCHIVE_UNSAFE')
PY
tar -xzf "$TMP/$ARCHIVE" -C "$TMP"
export GOROOT="$TMP/go" GOTOOLCHAIN=local GOENV=off GOWORK=off GOFLAGS='' CGO_ENABLED=1
# A CI job uses a private module/build cache unless its isolated caller supplied one.
export GOPATH="${GOPATH:-$TMP/gopath}" GOCACHE="${GOCACHE:-$TMP/go-cache}"
python3 -I -m unittest discover -s "$HELPER" -p test_build.py
python3 -I "$HELPER/build.py" --go "$TMP/go/bin/go" --toolchain-archive "$TMP/$ARCHIVE" --output "$OUTPUT"
(cd "$HELPER" && "$TMP/go/bin/go" test -mod=readonly -race -tags sqlite,sqlite_unlock_notify ./...)
# Export a synthetic upstream-model DB for an optional disposable-container
# process test; this .test-fixture.db is not a release/installation artifact.
[[ ! -e "$OUTPUT.test-fixture.db" ]] || { printf '%s\n' 'PROCESS_FIXTURE_ALREADY_EXISTS' >&2; exit 2; }
(cd "$HELPER" && AISOFT_HELPER_PROCESS_FIXTURE="$OUTPUT.test-fixture.db" \
  "$TMP/go/bin/go" test -mod=readonly -tags sqlite,sqlite_unlock_notify -run '^TestExportProcessFixture$' ./...)
python3 -I "$ROOT/codex/tests/integration/test-gitea-pat-helper-process.py" --binary "$OUTPUT"
printf '%s\n' 'PASS: pinned native Linux helper build/model/race/process checks (no installation/live)'

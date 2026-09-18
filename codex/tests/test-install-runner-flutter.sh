#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
TOOL="$ROOT/codex/tools/install-runner-flutter.sh"
TMP="$(mktemp -d)"
trap 'rm -rf -- "$TMP"' EXIT

REVISION=edada7c56edf4a183c1735310e123c7f923584f1
WRONG_REVISION=0000000000000000000000000000000000000000
SHIM="$TMP/bin"
mkdir -p "$SHIM"

# The tool writes to /opt and runs apt-get and sudo, so every host-mutating
# command is shimmed and every path is redirected under $TMP. What is actually
# under test is the control flow: the revision assertion, idempotence, the disk
# gate and the staging cleanup on failure.
cat >"$SHIM/git" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
# Mirrors git's dubious-ownership refusal: once the tree has been chowned away
# from the caller, a read without a scoped safe.directory fails with 128.
safe=""
if [[ "${1:-}" == "-c" ]]; then
  case "${2:-}" in safe.directory=*) safe="${2#safe.directory=}" ;; esac
  shift 2
fi
if [[ "${1:-}" == "-C" ]]; then
  dir="$2"; shift 2
  [[ "${1:-}" == "rev-parse" ]] || exit 2
  if [[ -f "$dir/.foreign-owner" && "$safe" != "$dir" ]]; then
    printf 'fatal: detected dubious ownership in repository at %s\n' "$dir" >&2
    exit 128
  fi
  [[ -f "$dir/.revision" ]] || exit 1
  cat "$dir/.revision"
  exit 0
fi
if [[ "${1:-}" == "clone" ]]; then
  dest="${!#}"
  mkdir -p "$dest/.git" "$dest/bin"
  printf '%s\n' "${FAKE_CLONE_REVISION:?}" >"$dest/.revision"
  cat >"$dest/bin/flutter" <<'INNER'
#!/usr/bin/env bash
printf 'Flutter 3.32.8 revision %s\n' "${FAKE_CLONE_REVISION:-unknown}"
INNER
  chmod +x "$dest/bin/flutter"
  exit 0
fi
exit 2
SH

cat >"$SHIM/id" <<'SH'
#!/usr/bin/env bash
if [[ "${1:-}" == "-u" ]]; then printf '0\n'; exit 0; fi
exec /usr/bin/id "$@"
SH

cat >"$SHIM/df" <<'SH'
#!/usr/bin/env bash
# Real df fails on a path that does not exist; the shim must too, or it hides
# the case where the tool probes $INSTALL_ROOT before creating it.
target="${!#}"
if [[ ! -d "$target" ]]; then
  printf 'df: %s: No such file or directory\n' "$target" >&2
  exit 1
fi
if [[ "${1:-}" == "--output=pcent" ]]; then
  printf 'Use%%\n %s%%\n' "${FAKE_DISK_PERCENT:-22}"
  exit 0
fi
printf 'Filesystem Size Used Avail Use%% Mounted\nfake 253G 54G 199G %s%% %s\n' "${FAKE_DISK_PERCENT:-22}" "$target"
SH

cat >"$SHIM/sudo" <<'SH'
#!/usr/bin/env bash
[[ "${1:-}" == "-u" ]] && shift 2
exec "$@"
SH

cat >"$SHIM/chown" <<'SH'
#!/usr/bin/env bash
# chown -R away from the caller is exactly what makes root's later git reads
# "dubious", so the shim records it instead of being a plain no-op.
target="${!#}"
[[ -d "$target" ]] && touch "$target/.foreign-owner"
exit 0
SH

cat >"$SHIM/install" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
args=()
while (($# > 0)); do
  case "$1" in
    -m|-o|-g) shift 2 ;;
    *) args+=("$1"); shift ;;
  esac
done
cp "${args[0]}" "${args[1]}"
SH

cat >"$SHIM/apt-get" <<'SH'
#!/usr/bin/env bash
exit 0
SH

cat >"$SHIM/unzip" <<'SH'
#!/usr/bin/env bash
exit 0
SH

chmod +x "$SHIM"/*
export PATH="$SHIM:$PATH"

INSTALL_ROOT="$TMP/opt/flutter"
PUB_CACHE_DIR="$TMP/opt/act-runner/.pub-cache"
export INSTALL_ROOT PUB_CACHE_DIR
export RUNNER_USER; RUNNER_USER="$(/usr/bin/id -un)"
export FLUTTER_REVISION="$REVISION"
export FAKE_CLONE_REVISION="$REVISION"

run() { bash "$TOOL" "$@" 2>&1; }
status() { set +e; bash "$TOOL" "$@" >"$TMP/out" 2>&1; printf '%s' "$?"; set -e; }

# 1. an unknown argument is rejected before anything else happens
[[ "$(status --bogus)" == 2 ]]
grep -Fq 'unknown argument: --bogus' "$TMP/out"

# 2. --check is read-only: it reports and creates nothing
first_check="$(run --check)"
grep -Fq 'no existing checkout' <<<"$first_check"
grep -Fq 'check: install would run' <<<"$first_check"
[[ ! -e "$INSTALL_ROOT/3.32.8" ]]

# 3. a full install clones, asserts the revision and writes the marker
first="$(run)"
grep -Fq 'cloning' <<<"$first"
grep -Fq "revision assertion passed: $REVISION" <<<"$first"
grep -Fq 'contract=gitea-runner-flutter-runtime/v1' "$INSTALL_ROOT/3.32.8/.aisoft-runtime-source"
grep -Fq "flutter_revision=$REVISION" "$INSTALL_ROOT/3.32.8/.aisoft-runtime-source"
grep -Fq 'runner_env=not injected' "$INSTALL_ROOT/3.32.8/.aisoft-runtime-source"
[[ -d "$PUB_CACHE_DIR" ]]

# 4. the second run is a no-op: no clone, no bootstrap, and no mtime moves
before="$(find "$INSTALL_ROOT/3.32.8" -exec ls -ld {} + | sort)"
second="$(run)"
grep -Fq "already installed at $REVISION" <<<"$second"
grep -Fq 'provenance marker unchanged' <<<"$second"
grep -Fq 'skipping ownership, bootstrap and precache' <<<"$second"
grep -Fq 'bootstrapping Dart SDK' <<<"$second" && exit 1
grep -Fq 'cloning' <<<"$second" && exit 1
after="$(find "$INSTALL_ROOT/3.32.8" -exec ls -ld {} + | sort)"
[[ "$before" == "$after" ]]

# 4b. --repair forces the bootstrap back on for the same already-installed tree
grep -Fq 'bootstrapping Dart SDK' <<<"$(run --repair)"

# 5. --check on an installed tree reports the match instead of planning work
grep -Fq 'check: already installed and revision matches' <<<"$(run --check)"

# 6. a moved tag fails closed and leaves no half-installed tree behind
rm -rf "$INSTALL_ROOT"
FAKE_CLONE_REVISION="$WRONG_REVISION" bash "$TOOL" >"$TMP/out" 2>&1 && exit 1
grep -Fq "resolved to $WRONG_REVISION" "$TMP/out"
[[ ! -e "$INSTALL_ROOT/3.32.8" ]]
[[ -z "$(find "$INSTALL_ROOT" -maxdepth 1 -name '.staging-*' 2>/dev/null)" ]]

# 7. the disk gate refuses before touching anything
rm -rf "$INSTALL_ROOT"
FAKE_DISK_PERCENT=91 bash "$TOOL" >"$TMP/out" 2>&1 && exit 1
grep -Fq 'disk usage 91% >= 80% threshold' "$TMP/out"
[[ ! -e "$INSTALL_ROOT/3.32.8" ]]

# 8. --no-pub-cache skips the cache directory (authorization gate 2 denied)
rm -rf "$INSTALL_ROOT" "$PUB_CACHE_DIR"
grep -Fq 'skipping pub cache' <<<"$(run --no-pub-cache)"
[[ ! -e "$PUB_CACHE_DIR" ]]

# 9. a fresh host has neither $INSTALL_ROOT nor its parent; the disk probe must
#    walk up to an existing ancestor instead of failing the whole run
rm -rf "$TMP/opt"
fresh="$(run)"
grep -Fq 'cloning' <<<"$fresh"
grep -Fq "flutter_revision=$REVISION" "$INSTALL_ROOT/3.32.8/.aisoft-runtime-source"

printf 'PASS: install-runner-flutter\n'

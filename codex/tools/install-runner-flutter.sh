#!/usr/bin/env bash
# Install a pinned Flutter SDK for the gitea-ci act_runner host (Issue #309).
#
# The host is aarch64 and Flutter publishes Linux archives for x64 only, so the
# arm64 install path is "clone the tag, then let the SDK bootstrap its own Dart".
# Bootstrapping unzips dartsdk-linux-arm64, which needs unzip on PATH.
#
# Idempotent: a second run with the same version/revision changes nothing and
# exits 0. Run it as root on the runner host:
#
#   sudo bash codex/tools/install-runner-flutter.sh
#   sudo bash codex/tools/install-runner-flutter.sh --check   # read-only
#
# It never touches act_runner: no config edit, no systemd change, no restart.
set -euo pipefail

FLUTTER_VERSION="${FLUTTER_VERSION:-3.32.8}"
FLUTTER_REVISION="${FLUTTER_REVISION:-edada7c56edf4a183c1735310e123c7f923584f1}"
FLUTTER_REPO="${FLUTTER_REPO:-https://github.com/flutter/flutter.git}"
RUNNER_USER="${RUNNER_USER:-gitea-runner}"
INSTALL_ROOT="${INSTALL_ROOT:-/opt/flutter}"
PUB_CACHE_DIR="${PUB_CACHE_DIR:-/opt/act-runner/.pub-cache}"
DISK_FULL_PERCENT="${DISK_FULL_PERCENT:-80}"
MARKER_CONTRACT="gitea-runner-flutter-runtime/v1"

INSTALL_DIR="$INSTALL_ROOT/$FLUTTER_VERSION"
MARKER="$INSTALL_DIR/.aisoft-runtime-source"
CHECK_ONLY=0
WANT_PUB_CACHE=1

usage() {
  cat <<USAGE
usage: install-runner-flutter.sh [--check] [--no-pub-cache]

  --check          read-only: report state and exit, write nothing
  --no-pub-cache   skip creating $PUB_CACHE_DIR (authorization gate 2 denied)

Environment overrides: FLUTTER_VERSION FLUTTER_REVISION FLUTTER_REPO
RUNNER_USER INSTALL_ROOT PUB_CACHE_DIR DISK_FULL_PERCENT
USAGE
}

while (($# > 0)); do
  case "$1" in
    --check) CHECK_ONLY=1 ;;
    --no-pub-cache) WANT_PUB_CACHE=0 ;;
    -h|--help) usage; exit 0 ;;
    *) printf 'unknown argument: %s\n' "$1" >&2; usage >&2; exit 2 ;;
  esac
  shift
done

say() { printf '[install-runner-flutter] %s\n' "$*"; }
die() { printf '[install-runner-flutter] ERROR: %s\n' "$*" >&2; exit 1; }

installed_revision() {
  [[ -d "$INSTALL_DIR/.git" ]] || return 1
  git -C "$INSTALL_DIR" rev-parse HEAD 2>/dev/null
}

report_disk() {
  say "df -h $INSTALL_ROOT:"
  df -h "$INSTALL_ROOT" 2>/dev/null || df -h /
}

# --- state report -----------------------------------------------------------
say "target $INSTALL_DIR at revision $FLUTTER_REVISION for user $RUNNER_USER"
current=""
if current="$(installed_revision)"; then
  say "found existing checkout at revision $current"
else
  say "no existing checkout at $INSTALL_DIR"
fi
if command -v unzip >/dev/null; then say "unzip: $(command -v unzip)"; else say "unzip: MISSING"; fi
report_disk

if ((CHECK_ONLY)); then
  if [[ "$current" == "$FLUTTER_REVISION" ]] && command -v unzip >/dev/null; then
    say "check: already installed and revision matches"
    exit 0
  fi
  say "check: install would run"
  exit 0
fi

[[ "$(id -u)" -eq 0 ]] || die "must run as root (writes $INSTALL_ROOT)"
id "$RUNNER_USER" >/dev/null 2>&1 || die "runner user $RUNNER_USER does not exist"

# --- disk gate --------------------------------------------------------------
use_percent="$(df --output=pcent "$INSTALL_ROOT" 2>/dev/null | tail -1 | tr -dc '0-9')"
if [[ -n "$use_percent" ]] && ((use_percent >= DISK_FULL_PERCENT)); then
  die "disk usage ${use_percent}% >= ${DISK_FULL_PERCENT}% threshold; refusing to install"
fi

# --- unzip ------------------------------------------------------------------
if command -v unzip >/dev/null; then
  say "unzip already present, skipping apt-get"
else
  say "installing unzip"
  DEBIAN_FRONTEND=noninteractive apt-get update -qq
  DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends unzip
fi

# --- SDK --------------------------------------------------------------------
if [[ "$current" == "$FLUTTER_REVISION" ]]; then
  say "already installed at $FLUTTER_REVISION, skipping clone and bootstrap"
else
  if [[ -n "$current" ]]; then
    die "$INSTALL_DIR holds revision $current, expected $FLUTTER_REVISION; remove it first"
  fi
  if [[ -e "$INSTALL_DIR" ]]; then
    die "$INSTALL_DIR exists but is not a git checkout; remove it first"
  fi

  mkdir -p "$INSTALL_ROOT"
  staging="$(mktemp -d "$INSTALL_ROOT/.staging-$FLUTTER_VERSION.XXXXXX")"
  # A failed clone or a revision mismatch must not leave a half-installed tree
  # behind: everything happens in staging and is only moved into place once the
  # revision assertion passes.
  trap 'rm -rf "$staging"' EXIT

  say "cloning $FLUTTER_REPO tag $FLUTTER_VERSION"
  git clone --depth 1 --branch "$FLUTTER_VERSION" "$FLUTTER_REPO" "$staging/flutter"

  cloned="$(git -C "$staging/flutter" rev-parse HEAD)"
  if [[ "$cloned" != "$FLUTTER_REVISION" ]]; then
    die "revision mismatch: tag $FLUTTER_VERSION resolved to $cloned, expected $FLUTTER_REVISION"
  fi
  say "revision assertion passed: $cloned"

  mv "$staging/flutter" "$INSTALL_DIR"
  trap - EXIT
  rm -rf "$staging"
fi

# A self-bootstrapping SDK writes inside its own root (bin/cache, and version
# stamp files whose location has moved between releases), so the tree is owned
# by the runner user rather than root. /opt/node22 on the same host is already
# gitea-runner-owned; /opt/node24.18.0 is root-owned because Node ships a
# complete tree and never writes into it.
chown -R "$RUNNER_USER":"$RUNNER_USER" "$INSTALL_DIR"
chmod -R a+rX "$INSTALL_DIR"

say "bootstrapping Dart SDK as $RUNNER_USER (first run downloads ~187 MiB)"
sudo -u "$RUNNER_USER" env HOME=/opt/act-runner "$INSTALL_DIR/bin/flutter" --version
sudo -u "$RUNNER_USER" env HOME=/opt/act-runner "$INSTALL_DIR/bin/flutter" precache --linux

# --- pub cache --------------------------------------------------------------
if ((WANT_PUB_CACHE)); then
  if [[ -d "$PUB_CACHE_DIR" ]]; then
    say "pub cache $PUB_CACHE_DIR already present"
  else
    say "creating pub cache $PUB_CACHE_DIR"
    mkdir -p "$PUB_CACHE_DIR"
  fi
  chown "$RUNNER_USER":"$RUNNER_USER" "$PUB_CACHE_DIR"
else
  say "skipping pub cache (--no-pub-cache)"
fi

# --- provenance marker ------------------------------------------------------
marker_tmp="$(mktemp)"
{
  printf 'contract=%s\n' "$MARKER_CONTRACT"
  printf 'installed_at=%s\n' "$(date -u +%Y-%m-%d)"
  printf 'flutter_version=%s\n' "$FLUTTER_VERSION"
  printf 'flutter_revision=%s\n' "$FLUTTER_REVISION"
  printf 'flutter_source=%s tag %s\n' "$FLUTTER_REPO" "$FLUTTER_VERSION"
  printf 'arch_note=%s\n' "official Linux archives are x64 only; arm64 bootstraps from a tag clone"
  printf 'runner_user=%s\n' "$RUNNER_USER"
  printf 'pub_cache=%s\n' "$PUB_CACHE_DIR"
  printf 'runner_env=%s\n' "not injected; consumer workflows declare PUB_CACHE and PATH in job env"
  printf 'rollback=%s\n' "remove-$INSTALL_DIR; act_runner-config-and-unit-unchanged"
} >"$marker_tmp"
# Rewrite the marker only when its content actually changes, so a no-op run
# leaves every mtime under the install root untouched (AC-2).
if [[ -f "$MARKER" ]] && cmp -s "$marker_tmp" "$MARKER"; then
  say "provenance marker unchanged"
  rm -f "$marker_tmp"
else
  install -m 644 -o "$RUNNER_USER" -g "$RUNNER_USER" "$marker_tmp" "$MARKER"
  rm -f "$marker_tmp"
  say "wrote provenance marker $MARKER"
fi

report_disk
say "done: $INSTALL_DIR"

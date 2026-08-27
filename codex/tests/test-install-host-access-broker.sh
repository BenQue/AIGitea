#!/usr/bin/env bash
# Cover the source provenance output and the staleness gate (#162).
#
# Every case builds a throwaway checkout and, where a remote is needed, a local
# bare repository to push into. Nothing here touches the network: the failure
# this guards against was 'fetched but never fast-forwarded', which is entirely
# a property of refs already on disk.
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf -- "$TMP"' EXIT

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

expected_operations="$(
  python3 -c 'import json,sys; print(len(json.load(open(sys.argv[1]))["operations"]))' \
    "$ROOT/codex/config/host-access-broker.json"
)"

# Exactly the sources install-host-access-broker.sh reads. Copying more would
# hide a missing source; copying less would make the installer fail for the
# wrong reason.
make_source_tree() {
  local dest="$1"
  mkdir -p "$dest/codex/runtime" "$dest/codex/config" "$dest/codex/tools" \
    "$dest/codex/lib"
  cp "$ROOT/codex/install-host-access-broker.sh" "$dest/codex/"
  cp "$ROOT/codex/lib/install-source-guard.sh" "$dest/codex/lib/"
  cp -R "$ROOT/codex/runtime/aisoft_host_access" "$dest/codex/runtime/"
  cp -R "$ROOT/codex/runtime/aisoft_gitea_governance" "$dest/codex/runtime/"
  cp "$ROOT/codex/runtime/aisoft_change_name.py" "$dest/codex/runtime/"
  cp "$ROOT/codex/config/host-access-broker.json" "$dest/codex/config/"
  cp "$ROOT/codex/config/gitea-governance.json" "$dest/codex/config/"
  cp "$ROOT/codex/config/gitea-labels.json" "$dest/codex/config/"
  cp "$ROOT/codex/tools/host-access-broker.sh" "$dest/codex/tools/"
  cp "$ROOT/codex/tools/git-credential-aisoft-host.sh" "$dest/codex/tools/"
  cp "$ROOT/codex/tools/project-profile-migration.sh" "$dest/codex/tools/"
  cp "$ROOT/codex/tools/bootstrap-gitea-service-account.sh" "$dest/codex/tools/"
  cp "$ROOT/codex/tools/rollback-gitea-routine-pilot.sh" "$dest/codex/tools/"
}

# Repository-local identity only: the host may have no global git user, and a
# global commit.gpgsign would otherwise break these commits.
init_repo() {
  local dir="$1"
  git -C "$dir" init -q
  git -C "$dir" symbolic-ref HEAD refs/heads/main
  git -C "$dir" config user.name 'aisoft test'
  git -C "$dir" config user.email 'aisoft-test@example.invalid'
  git -C "$dir" config commit.gpgsign false
  git -C "$dir" add -A
  git -C "$dir" commit -q -m 'base'
}

attach_remote() {
  local dir="$1" remote="$2"
  git init -q --bare "$remote"
  git -C "$dir" remote add origin "$remote"
  git -C "$dir" push -q -u origin main
}

run_installer() {
  local checkout="$1" install_root="$2"
  AISOFT_HOST_ACCESS_INSTALL_ROOT="$install_root" \
    bash "$checkout/codex/install-host-access-broker.sh" 2>&1
}

assert_provenance() {
  local output="$1" label="$2"
  grep -Fq 'source checkout:' <<<"$output" ||
    fail "$label: missing source checkout line"
  grep -Eq '^source commit:     [0-9a-f]+ \(' <<<"$output" ||
    fail "$label: missing or unreadable source commit line"
  grep -Fq "source operations: $expected_operations" <<<"$output" ||
    fail "$label: source operations line does not report $expected_operations"
}

assert_installed() {
  local install_root="$1" label="$2"
  [[ -f "$install_root/usr/local/share/aisoft/host-access-broker.json" ]] ||
    fail "$label: manifest was not installed"
  [[ -x "$install_root/usr/local/libexec/aisoft/host-access-broker" ]] ||
    fail "$label: broker entrypoint was not installed"
  [[ -x "$install_root/usr/local/libexec/aisoft/bootstrap-gitea-service-account" ]] ||
    fail "$label: bootstrap tool was not installed"
  [[ -x "$install_root/usr/local/libexec/aisoft/rollback-gitea-routine-pilot" ]] ||
    fail "$label: rollback tool was not installed"
  cmp -s "$ROOT/codex/tools/bootstrap-gitea-service-account.sh" \
    "$install_root/usr/local/libexec/aisoft/bootstrap-gitea-service-account" ||
    fail "$label: bootstrap tool bytes differ"
  cmp -s "$ROOT/codex/tools/rollback-gitea-routine-pilot.sh" \
    "$install_root/usr/local/libexec/aisoft/rollback-gitea-routine-pilot" ||
    fail "$label: rollback tool bytes differ"
}

# --- level with upstream: installs, and prints what it installed -------------
level="$TMP/level"
make_source_tree "$level"
init_repo "$level"
attach_remote "$level" "$TMP/level-remote.git"

if ! level_out="$(run_installer "$level" "$TMP/root-level")"; then
  fail "level checkout install failed: $level_out"
fi
assert_provenance "$level_out" 'level'
grep -Fq 'level with origin/main' <<<"$level_out" ||
  fail 'level: sync state should report being level with origin/main'
grep -Fq 'installed host-access-broker/v1 candidate' <<<"$level_out" ||
  fail 'level: installer did not report an install'
assert_installed "$TMP/root-level" 'level'

# The no-op path is the one misread in #162, so provenance has to survive it.
if ! repeat_out="$(run_installer "$level" "$TMP/root-level")"; then
  fail "level checkout re-install failed: $repeat_out"
fi
assert_provenance "$repeat_out" 'no-op'
grep -Fq 'already current (no-op)' <<<"$repeat_out" ||
  fail 'no-op: second install should be a no-op'

# --- behind upstream: refuses, before writing anything -----------------------
behind="$TMP/behind"
make_source_tree "$behind"
init_repo "$behind"
attach_remote "$behind" "$TMP/behind-remote.git"
git -C "$behind" commit -q --allow-empty -m 'merged upstream commit'
git -C "$behind" push -q origin main
git -C "$behind" reset -q --hard HEAD~1

if behind_out="$(run_installer "$behind" "$TMP/root-behind")"; then
  fail "behind checkout must not install: $behind_out"
fi
grep -Fq '1 commit(s) behind origin/main' <<<"$behind_out" ||
  fail 'behind: refusal must state how far behind the checkout is'
grep -Fq 'merge --ff-only origin/main' <<<"$behind_out" ||
  fail 'behind: refusal must name the fast-forward remedy'
assert_provenance "$behind_out" 'behind'
[[ ! -e "$TMP/root-behind" ]] ||
  fail 'behind: refusal must happen before any filesystem write'

# --- no remote: warns, then installs ----------------------------------------
solo="$TMP/no-remote"
make_source_tree "$solo"
init_repo "$solo"

if ! solo_out="$(run_installer "$solo" "$TMP/root-no-remote")"; then
  fail "no-remote checkout install failed: $solo_out"
fi
grep -Fq 'has no upstream' <<<"$solo_out" ||
  fail 'no-remote: expected an unchecked-staleness warning'
grep -Fq 'WARNING: install-host-access-broker:' <<<"$solo_out" ||
  fail 'no-remote: warning must be labelled'
assert_provenance "$solo_out" 'no-remote'
assert_installed "$TMP/root-no-remote" 'no-remote'

# --- detached HEAD: warns, then installs ------------------------------------
detached="$TMP/detached"
make_source_tree "$detached"
init_repo "$detached"
attach_remote "$detached" "$TMP/detached-remote.git"
git -C "$detached" checkout -q --detach

if ! detached_out="$(run_installer "$detached" "$TMP/root-detached")"; then
  fail "detached checkout install failed: $detached_out"
fi
grep -Fq 'detached HEAD' <<<"$detached_out" ||
  fail 'detached: expected a detached-HEAD warning'
assert_installed "$TMP/root-detached" 'detached'

# --- not a git checkout: warns, then installs -------------------------------
plain="$TMP/plain"
make_source_tree "$plain"

# The temp checkout has no repository of its own; the ceiling stops git from
# discovering some unrelated repository above it and reporting a commit.
if ! plain_out="$(export GIT_CEILING_DIRECTORIES="$TMP"; run_installer "$plain" "$TMP/root-plain")"; then
  fail "non-git checkout install failed: $plain_out"
fi
grep -Fq 'not a git checkout' <<<"$plain_out" ||
  fail 'non-git: expected a not-a-git-checkout warning'
grep -Fq "source operations: $expected_operations" <<<"$plain_out" ||
  fail 'non-git: operations count must still be reported'
assert_installed "$TMP/root-plain" 'non-git'

printf '%s\n' 'host-access-broker installer tests passed'

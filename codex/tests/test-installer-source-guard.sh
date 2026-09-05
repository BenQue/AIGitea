#!/usr/bin/env bash
# Cover the shared source provenance output and staleness gate on the
# installers wired to it (#171; #162 for the broker installer alone).
#
# One throwaway checkout is rewritten through three git states -- level, behind,
# no remote -- and every installer runs against each state into its own install
# root. Six near-identical test files would drift exactly the way six copies of
# the gate would, which is what #171 AC-3 is about.
#
# Nothing here touches the network: the failure this guards against is 'fetched
# but never fast-forwarded', which is entirely a property of refs already on
# disk. The remote is a local bare repository.
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf -- "$TMP"' EXIT

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

INSTALLERS=(
  install-host-access-broker
  install-host-role
  install-vm
  install-skills
  architecture/install
  docker-release/install
  sync/install
  skill-for-claude/install
)

# Expected identity quantities, recomputed here through jq/find rather than the
# python3/glob the installers use. An assertion that reruns the implementation
# proves only that it is deterministic.
expected_operations="$(jq '.operations | length' "$ROOT/codex/config/host-access-broker.json")"
expected_capabilities="$(jq '.capabilities | length' "$ROOT/codex/config/host-capabilities.json")"
expected_components="$(jq '.components | length' "$ROOT/architecture/catalog.json")"
expected_catalog_revision="$(jq -r '.revision' "$ROOT/architecture/catalog.json")"
expected_matrix_revision="$(
  jq -r '.matrix_revision' "$ROOT/docker-release/compatibility/image-stores-v1.json"
)"
expected_schemas="$(
  find "$ROOT/docker-release/schema" -maxdepth 1 -type f -name '*.json' | wc -l | tr -d ' '
)"
expected_sync_units="$(
  find "$ROOT/sync/systemd" -maxdepth 1 -type f | wc -l | tr -d ' '
)"
# The payload scripts are every top-level sync/*.sh except the installer itself,
# which is a different statement of the set than the two paths install.sh names.
expected_sync_scripts="$(
  find "$ROOT/sync" -maxdepth 1 -type f -name '*.sh' ! -name 'install.sh' |
    wc -l | tr -d ' '
)"
expected_runtime_modules="$(
  find \
    "$ROOT/codex/runtime/aisoft_loop" \
    "$ROOT/codex/runtime/aisoft_host_access" \
    "$ROOT/codex/runtime/aisoft_gitea_governance" \
    -maxdepth 1 -type f -name '*.py' | wc -l | tr -d ' '
)"
expected_runtime_modules=$((expected_runtime_modules + 1)) # aisoft_change_name.py
expected_skills="$(
  find "$ROOT/codex/skills" -maxdepth 2 -type f -name SKILL.md | wc -l | tr -d ' '
)"
expected_skills=$((expected_skills + 1)) # skill-for-codex, installed as aisoft-platform
# The Claude-side installer declares its own skill set and copies the shared
# reference files into every skill declared `shared`; those two counts are the
# whole managed tree it writes.
expected_claude_skills="$(
  find "$ROOT/skill-for-claude" -maxdepth 2 -type f -name SKILL.md | wc -l | tr -d ' '
)"
expected_claude_references="$(
  find "$ROOT/skill-for-codex/references" -maxdepth 1 -type f -name '*.md' | wc -l | tr -d ' '
)"
expected_matt_version="$(
  awk -F'"' '/^matt_version=/ { print $2 }' "$ROOT/codex/install-skills.sh"
)"
[[ -n "$expected_matt_version" ]] || fail 'could not read matt_version from install-skills.sh'

# The union of what the seven installers read. Copying whole top-level directories
# is coarser than a per-file list, but the union is these directories anyway.
make_source_tree() {
  local dest="$1" directory
  mkdir -p "$dest"
  for directory in \
    codex architecture docker-release templates skill-for-codex sync skill-for-claude; do
    cp -R "$ROOT/$directory" "$dest/"
  done
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

run_installer() {
  local name="$1" checkout="$2" root="$3"
  case "$name" in
    install-host-access-broker)
      AISOFT_HOST_ACCESS_INSTALL_ROOT="$root" \
        bash "$checkout/codex/install-host-access-broker.sh" 2>&1
      ;;
    install-host-role)
      AISOFT_HOST_ROLE_INSTALL_ROOT="$root" \
        bash "$checkout/codex/install-host-role.sh" 2>&1
      ;;
    install-vm) bash "$checkout/codex/install-vm.sh" "$root" 2>&1 ;;
    install-skills) bash "$checkout/codex/install-skills.sh" "$root" 2>&1 ;;
    architecture/install) bash "$checkout/architecture/install.sh" --prefix "$root" 2>&1 ;;
    docker-release/install)
      AISOFT_DOCKER_RELEASE_INSTALL_ROOT="$root" \
        bash "$checkout/docker-release/install.sh" 2>&1
      ;;
    sync/install)
      AISOFT_SYNC_INSTALL_ROOT="$root" bash "$checkout/sync/install.sh" 2>&1
      ;;
    skill-for-claude/install)
      bash "$checkout/skill-for-claude/install.sh" "$root" 2>&1
      ;;
    *) fail "unknown installer: $name" ;;
  esac
}

# A path that exists only if the installer actually installed something.
installed_marker() {
  case "$1" in
    install-host-access-broker) printf 'usr/local/libexec/aisoft/host-access-broker' ;;
    install-host-role) printf 'usr/local/libexec/aisoft/verify-host-role' ;;
    install-vm) printf '.local/lib/aisoft-loop/aisoft_loop/cli.py' ;;
    install-skills) printf '.agents/skills/aisoft-platform/SKILL.md' ;;
    architecture/install) printf 'bin/aisoft-architecture' ;;
    docker-release/install) printf 'usr/local/bin/aisoft-docker-release' ;;
    sync/install) printf 'opt/aisoft-sync/inbound-sync.sh' ;;
    skill-for-claude/install) printf '.claude/skills/aisoft-platform/SKILL.md' ;;
    *) fail "unknown installer: $1" ;;
  esac
}

assert_source_line() {
  local output="$1" label="$2" value="$3" who="$4" pattern
  pattern="${value//./\\.}"
  grep -Eq "^source ${label}: +${pattern}\$" <<<"$output" ||
    fail "$who: expected 'source ${label}: ${value}'"
}

# AC-1: the commit plus the quantity that says which version this is.
assert_provenance() {
  local name="$1" output="$2" who="$3"
  grep -Fq 'source checkout:' <<<"$output" || fail "$who: missing source checkout line"
  grep -Eq '^source commit:     [0-9a-f]+ \(' <<<"$output" ||
    fail "$who: missing or unreadable source commit line"
  case "$name" in
    install-host-access-broker)
      assert_source_line "$output" operations "$expected_operations" "$who"
      ;;
    install-host-role)
      assert_source_line "$output" capabilities "$expected_capabilities" "$who"
      ;;
    install-vm)
      assert_source_line "$output" 'runtime modules' "$expected_runtime_modules" "$who"
      assert_source_line "$output" operations "$expected_operations" "$who"
      ;;
    install-skills)
      assert_source_line "$output" skills "$expected_skills" "$who"
      assert_source_line "$output" 'matt snapshot' "$expected_matt_version" "$who"
      ;;
    architecture/install)
      assert_source_line "$output" 'catalog revision' "$expected_catalog_revision" "$who"
      assert_source_line "$output" components "$expected_components" "$who"
      ;;
    docker-release/install)
      assert_source_line "$output" 'matrix revision' "$expected_matrix_revision" "$who"
      assert_source_line "$output" schemas "$expected_schemas" "$who"
      ;;
    sync/install)
      assert_source_line "$output" units "$expected_sync_units" "$who"
      assert_source_line "$output" 'runtime scripts' "$expected_sync_scripts" "$who"
      ;;
    skill-for-claude/install)
      assert_source_line "$output" skills "$expected_claude_skills" "$who"
      assert_source_line "$output" references "$expected_claude_references" "$who"
      ;;
  esac
}

install_root_for() {
  printf '%s/roots/%s/%s' "$TMP" "$1" "${2//\//-}"
}

SOURCE="$TMP/source"
make_source_tree "$SOURCE"
init_repo "$SOURCE"
git init -q --bare "$TMP/remote.git"
git -C "$SOURCE" remote add origin "$TMP/remote.git"
git -C "$SOURCE" push -q -u origin main

# --- level with upstream: installs, and prints what it installed -------------
for installer in "${INSTALLERS[@]}"; do
  label="level/$installer"
  root="$(install_root_for level "$installer")"
  if ! output="$(run_installer "$installer" "$SOURCE" "$root")"; then
    fail "$label: install failed: $output"
  fi
  assert_provenance "$installer" "$output" "$label"
  grep -Fq 'level with origin/main' <<<"$output" ||
    fail "$label: sync state should report being level with origin/main"
  [[ -e "$root/$(installed_marker "$installer")" ]] ||
    fail "$label: installer reported success without installing"
done

# --- behind upstream: refuses, before writing anything -----------------------
git -C "$SOURCE" commit -q --allow-empty -m 'merged upstream commit'
git -C "$SOURCE" push -q origin main
git -C "$SOURCE" reset -q --hard HEAD~1

mkdir -p "$TMP/roots/behind"
for installer in "${INSTALLERS[@]}"; do
  label="behind/$installer"
  root="$(install_root_for behind "$installer")"
  if output="$(run_installer "$installer" "$SOURCE" "$root")"; then
    fail "$label: behind checkout must not install: $output"
  fi
  assert_provenance "$installer" "$output" "$label"
  grep -Fq "ERROR: $installer: source checkout is 1 commit(s) behind origin/main" <<<"$output" ||
    fail "$label: refusal must be labelled and state how far behind the checkout is"
  grep -Fq 'merge --ff-only origin/main' <<<"$output" ||
    fail "$label: refusal must name the fast-forward remedy"
  [[ ! -e "$root" ]] ||
    fail "$label: refusal must happen before any filesystem write"
done

# --- no remote: warns, then installs ----------------------------------------
git -C "$SOURCE" branch --unset-upstream
git -C "$SOURCE" remote remove origin

for installer in "${INSTALLERS[@]}"; do
  label="no-remote/$installer"
  root="$(install_root_for no-remote "$installer")"
  if ! output="$(run_installer "$installer" "$SOURCE" "$root")"; then
    fail "$label: install failed: $output"
  fi
  assert_provenance "$installer" "$output" "$label"
  grep -Fq "WARNING: $installer: branch main has no upstream" <<<"$output" ||
    fail "$label: expected a labelled unchecked-staleness warning"
  [[ -e "$root/$(installed_marker "$installer")" ]] ||
    fail "$label: installer warned but did not install"
done

printf 'installer source guard tests passed (%s installers x 3 source states)\n' \
  "${#INSTALLERS[@]}"

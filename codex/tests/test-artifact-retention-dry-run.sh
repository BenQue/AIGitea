#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
TOOL="$ROOT/codex/tools/artifact-retention-dry-run.sh"
TMP="$(mktemp -d)"
trap 'rm -rf -- "$TMP"' EXIT

ARTIFACT_ROOT="$TMP/artifacts"
mkdir -p "$ARTIFACT_ROOT"
sha_current=1111111111111111111111111111111111111111
sha_old=2222222222222222222222222222222222222222
sha_unreferenced=3333333333333333333333333333333333333333
sha_bad=4444444444444444444444444444444444444444
for sha in "$sha_current" "$sha_old" "$sha_unreferenced" "$sha_bad"; do
  printf 'artifact-%s\n' "$sha" >"$ARTIFACT_ROOT/demo-$sha.tar.gz"
  sha256sum "$ARTIFACT_ROOT/demo-$sha.tar.gz" >"$ARTIFACT_ROOT/demo-$sha.tar.gz.sha256"
done
printf '%s  %s\n' \
  0000000000000000000000000000000000000000000000000000000000000000 \
  "demo-$sha_bad.tar.gz" >"$ARTIFACT_ROOT/demo-$sha_bad.tar.gz.sha256"
touch -t 202001010000 "$ARTIFACT_ROOT/demo-$sha_old.tar.gz" \
  "$ARTIFACT_ROOT/demo-$sha_unreferenced.tar.gz" "$ARTIFACT_ROOT/demo-$sha_bad.tar.gz"

POLICY="$TMP/policy.json"
REFERENCES="$TMP/references.json"
AUDIT="$TMP/audit.log"
jq -n --arg root "$ARTIFACT_ROOT" '
  {contract_version: "1.0", artifact_root: $root, projects: [{
    name: "demo", filename_prefix: "demo-", filename_suffix: ".tar.gz",
    minimum_retained: 1, minimum_age_days: 30,
    required_reference_kinds: ["current", "rollback", "workflow", "test-attestation", "production-manifest"]
  }]}
' >"$POLICY"
jq -n --arg current "$sha_current" --arg old "$sha_old" '
  {contract_version: "1.0", references: [
    {project: "demo", kind: "current", sha: $current, source: "current"},
    {project: "demo", kind: "rollback", sha: $old, source: "rollback"},
    {project: "demo", kind: "workflow", sha: $current, source: "workflow"},
    {project: "demo", kind: "test-attestation", sha: $current, source: "attestation"},
    {project: "demo", kind: "production-manifest", sha: $current, source: "manifest"}
  ]}
' >"$REFERENCES"

ledger="$(bash "$TOOL" --policy "$POLICY" --references "$REFERENCES" --audit-ledger "$AUDIT")"
grep -Fq "sha=$sha_current status=KEEP reason=protected-reference" <<<"$ledger"
grep -Fq "sha=$sha_old status=KEEP reason=protected-reference" <<<"$ledger"
grep -Fq "sha=$sha_unreferenced status=CANDIDATE reason=unreferenced-past-policy" <<<"$ledger"
grep -Fq "sha=$sha_bad status=BLOCKED reason=checksum-mismatch" <<<"$ledger"
grep -Fxq 'summary candidates=1 keep=2 blocked=1' <<<"$ledger"
grep -Fq 'mode=DRY-RUN' "$AUDIT"

jq 'del(.references[] | select(.kind == "workflow"))' "$REFERENCES" >"$TMP/references-incomplete.json"
incomplete="$(bash "$TOOL" --policy "$POLICY" --references "$TMP/references-incomplete.json")"
grep -Fq "sha=$sha_unreferenced status=BLOCKED reason=incomplete-references" <<<"$incomplete"

printf 'unallowlisted\n' >"$ARTIFACT_ROOT/unallowlisted.tar.gz"
unknown="$(bash "$TOOL" --policy "$POLICY" --references "$REFERENCES")"
grep -Fq 'artifact=unallowlisted.tar.gz status=BLOCKED reason=unknown-project-or-non-sha-name' <<<"$unknown"

if rg -n -- '--apply|rm[[:space:]]' "$TOOL"; then
  echo 'retention dry-run tool exposes a deletion path' >&2
  exit 1
fi
printf '%s\n' 'artifact retention dry-run tests passed'

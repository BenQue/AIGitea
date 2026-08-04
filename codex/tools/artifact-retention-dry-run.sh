#!/usr/bin/env bash
# Produce a fail-closed artifact-retention ledger. This tool never deletes files.
set -euo pipefail

POLICY=''
REFERENCES=''
AUDIT_LEDGER=''

usage() {
  cat <<'EOF'
Usage: artifact-retention-dry-run --policy POLICY.json --references REFERENCES.json [--audit-ledger PATH]

The policy allowlists projects and sets each project's minimum retained count and
minimum age. The references ledger must account for current, rollback, workflow,
test-attestation and production-manifest references declared by that policy.

This command only writes an optional audit ledger; it never removes artifacts.
EOF
}

fail() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 2
}

while (($#)); do
  case "$1" in
    --policy) (($# >= 2)) || fail '--policy requires a path'; POLICY="$2"; shift 2 ;;
    --references) (($# >= 2)) || fail '--references requires a path'; REFERENCES="$2"; shift 2 ;;
    --audit-ledger) (($# >= 2)) || fail '--audit-ledger requires a path'; AUDIT_LEDGER="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) usage >&2; exit 2 ;;
  esac
done

[[ -n "$POLICY" && -n "$REFERENCES" ]] || { usage >&2; exit 2; }
command -v jq >/dev/null 2>&1 || fail 'jq is required'
command -v sha256sum >/dev/null 2>&1 || fail 'sha256sum is required'
[[ -f "$POLICY" && ! -L "$POLICY" ]] || fail "policy is not a regular file: $POLICY"
[[ -f "$REFERENCES" && ! -L "$REFERENCES" ]] || fail "references is not a regular file: $REFERENCES"
jq empty "$POLICY" "$REFERENCES" >/dev/null || fail 'policy or references is invalid JSON'

jq -e '
  type == "object" and (keys | sort) == ["artifact_root", "contract_version", "projects"] and
  .contract_version == "1.0" and
  (.artifact_root | type == "string" and startswith("/") and length > 1) and
  (.projects | type == "array" and length > 0 and (map(.name) | unique | length) == length) and
  all(.projects[];
    type == "object" and
    (keys | sort) == ["filename_prefix", "filename_suffix", "minimum_age_days", "minimum_retained", "name", "required_reference_kinds"] and
    (.name | type == "string" and test("^[a-z0-9][a-z0-9-]*$")) and
    (.filename_prefix | type == "string" and endswith("-")) and
    (.filename_suffix | type == "string" and startswith(".")) and
    (.minimum_retained | type == "number" and floor == . and . >= 1) and
    (.minimum_age_days | type == "number" and floor == . and . >= 0) and
    (.required_reference_kinds | type == "array" and length > 0 and (unique | length) == length and
      all(.[]; type == "string" and test("^[a-z][a-z-]*$")))
  )
' "$POLICY" >/dev/null || fail 'invalid retention policy contract'

jq -e --slurpfile policy "$POLICY" '
  type == "object" and (keys | sort) == ["contract_version", "references"] and
  .contract_version == "1.0" and (.references | type == "array") and
  all(.references[];
    type == "object" and (keys | sort) == ["kind", "project", "sha", "source"] and
    (.project | type == "string") and
    (.kind | type == "string" and test("^[a-z][a-z-]*$")) and
    (.sha | type == "string" and test("^[0-9a-f]{40}$")) and
    (.source | type == "string" and length > 0)
  ) and
  ([.references[] | [.project, .kind]] | unique | length) == (.references | length) and
  all(.references[]; . as $ref | ($policy[0].projects | map(.name) | index($ref.project)) != null)
' "$REFERENCES" >/dev/null || fail 'invalid retention references contract'

ARTIFACT_ROOT="$(jq -r '.artifact_root' "$POLICY")"
[[ -d "$ARTIFACT_ROOT" && ! -L "$ARTIFACT_ROOT" ]] || fail "artifact root is not a directory: $ARTIFACT_ROOT"

emit() {
  printf '%s\n' "$*"
  [[ -z "$AUDIT_LEDGER" ]] || printf '%s\n' "$*" >>"$AUDIT_LEDGER"
}

if [[ -n "$AUDIT_LEDGER" ]]; then
  audit_parent="$(dirname -- "$AUDIT_LEDGER")"
  [[ -d "$audit_parent" && ! -L "$audit_parent" ]] || fail "audit parent is not a directory: $audit_parent"
  [[ ! -e "$AUDIT_LEDGER" || ( -f "$AUDIT_LEDGER" && ! -L "$AUDIT_LEDGER" ) ]] || fail "audit ledger is not a regular file: $AUDIT_LEDGER"
  printf '# artifact-retention-dry-run timestamp=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >>"$AUDIT_LEDGER"
fi

declare -a artifact_files=()
while IFS= read -r -d '' artifact; do artifact_files+=("$artifact"); done < <(
  find "$ARTIFACT_ROOT" -maxdepth 1 -type f -print0 | sort -z
)

emit 'mode=DRY-RUN'
emit "artifact_root=$ARTIFACT_ROOT"
candidate_count=0
keep_count=0
blocked_count=0

for artifact in "${artifact_files[@]}"; do
  filename="$(basename -- "$artifact")"
  [[ "$filename" == *.sha256 ]] && continue
  matching_project=''
  matching_sha=''
  project_count="$(jq '.projects | length' "$POLICY")"
  for ((project_index = 0; project_index < project_count; project_index++)); do
    project="$(jq -r ".projects[$project_index].name" "$POLICY")"
    prefix="$(jq -r ".projects[$project_index].filename_prefix" "$POLICY")"
    suffix="$(jq -r ".projects[$project_index].filename_suffix" "$POLICY")"
    if [[ "$filename" == "$prefix"*"$suffix" ]]; then
      sha="${filename#"$prefix"}"
      sha="${sha%"$suffix"}"
      if [[ "$sha" =~ ^[0-9a-f]{40}$ ]]; then
        [[ -z "$matching_project" ]] || { matching_project='AMBIGUOUS'; break; }
        matching_project="$project"
        matching_sha="$sha"
      fi
    fi
  done
  if [[ -z "$matching_project" || "$matching_project" == AMBIGUOUS ]]; then
    emit "artifact=$filename status=BLOCKED reason=unknown-project-or-non-sha-name"
    blocked_count=$((blocked_count + 1))
    continue
  fi

  checksum_file="$artifact.sha256"
  if [[ ! -f "$checksum_file" || -L "$checksum_file" ]]; then
    emit "artifact=$filename project=$matching_project sha=$matching_sha status=BLOCKED reason=missing-checksum"
    blocked_count=$((blocked_count + 1))
    continue
  fi
  expected_checksum="$(awk 'NF { print $1; exit }' "$checksum_file")"
  actual_checksum="$(sha256sum "$artifact" | awk '{print $1}')"
  if [[ ! "$expected_checksum" =~ ^[0-9a-f]{64}$ || "$actual_checksum" != "$expected_checksum" ]]; then
    emit "artifact=$filename project=$matching_project sha=$matching_sha status=BLOCKED reason=checksum-mismatch"
    blocked_count=$((blocked_count + 1))
    continue
  fi

  policy_project="$(jq -c --arg project "$matching_project" '.projects[] | select(.name == $project)' "$POLICY")"
  reference_complete=1
  while IFS= read -r kind; do
    [[ -n "$kind" ]] || continue
    jq -e --arg project "$matching_project" --arg kind "$kind" \
      '.references[] | select(.project == $project and .kind == $kind)' "$REFERENCES" >/dev/null || reference_complete=0
  done < <(jq -r '.required_reference_kinds[]' <<<"$policy_project")
  if [[ "$reference_complete" != 1 ]]; then
    emit "artifact=$filename project=$matching_project sha=$matching_sha status=BLOCKED reason=incomplete-references"
    blocked_count=$((blocked_count + 1))
    continue
  fi
  if jq -e --arg sha "$matching_sha" '.references[] | select(.sha == $sha)' "$REFERENCES" >/dev/null; then
    emit "artifact=$filename project=$matching_project sha=$matching_sha status=KEEP reason=protected-reference checksum=$actual_checksum"
    keep_count=$((keep_count + 1))
    continue
  fi

  minimum_retained="$(jq -r '.minimum_retained' <<<"$policy_project")"
  minimum_age_days="$(jq -r '.minimum_age_days' <<<"$policy_project")"
  newer_or_equal=0
  prefix="$(jq -r '.filename_prefix' <<<"$policy_project")"
  suffix="$(jq -r '.filename_suffix' <<<"$policy_project")"
  for sibling in "${artifact_files[@]}"; do
    sibling_name="$(basename -- "$sibling")"
    [[ "$sibling_name" == *.sha256 ]] && continue
    if [[ "$sibling_name" == "$prefix"*"$suffix" ]] && [[ "$sibling" -nt "$artifact" || "$sibling" -ef "$artifact" ]]; then
      newer_or_equal=$((newer_or_equal + 1))
    fi
  done
  if ((newer_or_equal <= minimum_retained)); then
    emit "artifact=$filename project=$matching_project sha=$matching_sha status=KEEP reason=minimum-retained checksum=$actual_checksum"
    keep_count=$((keep_count + 1))
  elif find "$artifact" -maxdepth 0 -mtime "+$minimum_age_days" -print -quit | grep -q .; then
    emit "artifact=$filename project=$matching_project sha=$matching_sha status=CANDIDATE reason=unreferenced-past-policy checksum=$actual_checksum"
    candidate_count=$((candidate_count + 1))
  else
    emit "artifact=$filename project=$matching_project sha=$matching_sha status=KEEP reason=minimum-age checksum=$actual_checksum"
    keep_count=$((keep_count + 1))
  fi
done

emit "summary candidates=$candidate_count keep=$keep_count blocked=$blocked_count"

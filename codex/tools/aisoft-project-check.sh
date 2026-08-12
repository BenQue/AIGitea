#!/usr/bin/env bash
set -euo pipefail

# The checker is read-only. Disable inherited xtrace before loading credentials;
# remote authentication is sent to curl through stdin configuration only.
set +x

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
POINTER_TEMPLATE="$ROOT/templates/project/AGENTS.md"
CLAUDE_TEMPLATE="$ROOT/templates/project/CLAUDE.md"
CHANGE_TEMPLATE_ROOT="$ROOT/templates/docs/changes/_template"
LABEL_MANIFEST="$ROOT/codex/config/gitea-labels.json"
GOVERNANCE_MANIFEST="$ROOT/codex/config/gitea-governance.json"
ARCHITECTURE_CLI="$ROOT/architecture/bin/aisoft-architecture"

repo=''
kind=software
remote=false
today=''
pass_count=0
gap_count=0
skip_count=0

usage() {
  echo 'usage: aisoft-project-check.sh --repo <absolute-checkout> [--kind software|docs] [--remote] [--today YYYY-MM-DD]' >&2
  exit 64
}

while (($# > 0)); do
  case "$1" in
    --repo)
      (($# >= 2)) || usage
      repo="$2"
      shift 2
      ;;
    --kind)
      (($# >= 2)) || usage
      kind="$2"
      shift 2
      ;;
    --remote)
      remote=true
      shift
      ;;
    --today)
      (($# >= 2)) || usage
      today="$2"
      shift 2
      ;;
    *) usage ;;
  esac
done

[[ -n "$repo" && "$repo" == /* ]] || usage
[[ "$kind" == software || "$kind" == docs ]] || usage
[[ -d "$repo" ]] || usage
git -C "$repo" rev-parse --is-inside-work-tree >/dev/null 2>&1 || usage
if [[ -n "$today" ]]; then
  [[ "$today" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]] || usage
  python3 - "$today" <<'PY' >/dev/null 2>&1 || usage
import datetime
import sys

datetime.date.fromisoformat(sys.argv[1])
PY
fi

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

pass() {
  printf 'PASS: %s\n' "$1"
  pass_count=$((pass_count + 1))
}

gap() {
  printf 'GAP: %s — %s\n' "$1" "$2"
  gap_count=$((gap_count + 1))
}

skip() {
  printf 'SKIP: %s — %s\n' "$1" "$2"
  skip_count=$((skip_count + 1))
}

extract_pointer_sections() {
  awk '
    $0 == "## 平台声明（常驻指针）" {
      in_pointer = 1
      saw_platform = 1
    }
    in_pointer {
      if ($0 == "## 每 Issue 开发路径") {
        saw_path = 1
      } else if (saw_path && $0 ~ /^## /) {
        exit
      }
      print
    }
    END {
      if (!saw_platform || !saw_path) exit 1
    }
  ' "$1"
}

template_pointer="$tmp_dir/template-pointer"
repo_pointer="$tmp_dir/repo-pointer"
if [[ -f "$repo/AGENTS.md" && -f "$repo/CLAUDE.md" ]] &&
  extract_pointer_sections "$POINTER_TEMPLATE" >"$template_pointer" 2>/dev/null &&
  extract_pointer_sections "$repo/AGENTS.md" >"$repo_pointer" 2>/dev/null &&
  cmp -s "$template_pointer" "$repo_pointer" &&
  cmp -s "$CLAUDE_TEMPLATE" "$repo/CLAUDE.md"; then
  pass pointer-sections
else
  gap pointer-sections '平台指针两节或 CLAUDE.md 与模板不一致'
fi

templates_match=true
for document in summary spec plan verification; do
  if [[ ! -f "$repo/docs/changes/_template/$document.md" ]] ||
    ! cmp -s "$CHANGE_TEMPLATE_ROOT/$document.md" \
      "$repo/docs/changes/_template/$document.md"; then
    templates_match=false
    break
  fi
done
if [[ "$templates_match" == true ]]; then
  pass change-templates
else
  gap change-templates 'docs/changes/_template 与平台模板不一致'
fi

if [[ "$kind" == docs ]]; then
  skip architecture-lock 'docs 仓库不要求 architecture lock'
else
  architecture_project="$repo/.aisoft/architecture.json"
  architecture_lock="$repo/.aisoft/architecture.lock.json"
  if [[ ! -f "$architecture_project" ]]; then
    gap architecture-lock '.aisoft/architecture.json 缺失'
  elif [[ ! -f "$architecture_lock" ]]; then
    gap architecture-lock '.aisoft/architecture.lock.json 缺失'
  elif ! git -C "$repo" cat-file -e 'HEAD:.aisoft/architecture.lock.json' 2>/dev/null; then
    gap architecture-lock '.aisoft/architecture.lock.json 未提交'
  elif ! git -C "$repo" diff --quiet HEAD -- '.aisoft/architecture.lock.json'; then
    gap architecture-lock '.aisoft/architecture.lock.json 存在未提交变更'
  else
    architecture_args=(
      validate
      --catalog "$ROOT/architecture/catalog.json"
      --profiles-dir "$ROOT/architecture/profiles"
      --schema-dir "$ROOT/architecture/schemas"
      --project "$architecture_project"
      --lock "$architecture_lock"
    )
    if [[ -n "$today" ]]; then
      architecture_args+=(--today "$today")
    fi
    if "$ARCHITECTURE_CLI" "${architecture_args[@]}" >/dev/null 2>&1; then
      pass architecture-lock
    else
      gap architecture-lock 'strict JSON 或 architecture lock 校验失败'
    fi
  fi
fi

remote_ready=false
remote_reason=''
if [[ "$remote" == true ]]; then
  ENV_FILE="${AGENT_ENV_FILE:-$HOME/.agent.env}"
  if [[ ! -f "$ENV_FILE" ]]; then
    remote_reason='AGENT_ENV_FILE 缺失'
  else
    # shellcheck disable=SC1090
    source "$ENV_FILE" >/dev/null 2>&1
    set +x
    missing_env=''
    for name in GITEA_URL GITEA_OWNER GITEA_REPO GITEA_TOKEN; do
      if [[ -z "${!name:-}" ]]; then
        if [[ -n "$missing_env" ]]; then
          missing_env="$missing_env,$name"
        else
          missing_env="$name"
        fi
      fi
    done
    if [[ -n "$missing_env" ]]; then
      remote_reason="远程配置缺失: $missing_env"
    elif ! command -v jq >/dev/null || ! command -v curl >/dev/null; then
      remote_reason='远程检查需要 jq 与 curl'
    else
      remote_ready=true
      API="${GITEA_URL%/}/api/v1/repos/$GITEA_OWNER/$GITEA_REPO"
    fi
  fi
fi

api_get() {
  local url="$1" output_file="$2" http_status curl_status
  set +e
  http_status="$(
    printf 'header = "Authorization: token %s"\n' "$GITEA_TOKEN" |
      curl --config - --silent --output "$output_file" \
        --write-out '%{http_code}' "$url" 2>/dev/null
  )"
  curl_status=$?
  set -e
  [[ "$curl_status" == 0 && "$http_status" =~ ^[0-9]{3}$ ]] || return 1
  printf '%s' "$http_status"
}

check_remote_labels() {
  local page=1 http_status page_count name drift_names conflict_names
  local labels_all="$tmp_dir/labels-all.json"
  local labels_page="$tmp_dir/labels-page.json"
  local labels_next="$tmp_dir/labels-next.json"
  local unmanaged="$tmp_dir/unmanaged-labels"
  local problems=''
  printf '[]\n' >"$labels_all"

  while :; do
    if ! http_status="$(api_get "$API/labels?limit=50&page=$page" "$labels_page")"; then
      gap labels-readback '远程标签读取失败'
      return
    fi
    if [[ "$http_status" != 200 ]]; then
      gap labels-readback "远程标签读取返回 HTTP $http_status"
      return
    fi
    if ! jq -e 'type == "array" and all(.[]; type == "object" and
      (.name | type == "string") and (.color | type == "string") and
      (.description | type == "string"))' "$labels_page" >/dev/null 2>&1; then
      gap labels-readback '远程标签响应格式无效'
      return
    fi
    jq -s '.[0] + .[1]' "$labels_all" "$labels_page" >"$labels_next"
    mv "$labels_next" "$labels_all"
    page_count="$(jq 'length' "$labels_page")"
    ((page_count < 50)) && break
    page=$((page + 1))
    if ((page > 1000)); then
      gap labels-readback '远程标签分页超过安全上限'
      return
    fi
  done

  drift_names="$(
    jq -r --slurpfile actual "$labels_all" '
      .[] as $expected |
      select(([$actual[0][] |
        select(.name == $expected.name and .color == $expected.color and
          .description == $expected.description)] | length) != 1) |
      $expected.name
    ' "$LABEL_MANIFEST" | LC_ALL=C sort | paste -sd, -
  )"
  if [[ -n "$drift_names" ]]; then
    problems="缺失或漂移: $drift_names"
  fi

  jq -r --slurpfile canonical "$LABEL_MANIFEST" '
    [$canonical[0][].name] as $managed |
    .[] | .name as $name |
    select(($managed | index($name)) == null) |
    $name
  ' "$labels_all" | LC_ALL=C sort >"$unmanaged"

  conflict_names=''
  while IFS= read -r name; do
    [[ -n "$name" ]] || continue
    case "$name" in
      type/*|complexity/*|triage/*)
        if [[ -n "$conflict_names" ]]; then
          conflict_names="$conflict_names,$name"
        else
          conflict_names="$name"
        fi
        ;;
      *) printf 'INFO: labels-readback — 非受管标签 %s\n' "$name" ;;
    esac
  done <"$unmanaged"
  if [[ -n "$conflict_names" ]]; then
    if [[ -n "$problems" ]]; then
      problems="$problems; 受管命名空间冲突: $conflict_names"
    else
      problems="受管命名空间冲突: $conflict_names"
    fi
  fi

  if [[ -n "$problems" ]]; then
    gap labels-readback "$problems"
  else
    pass labels-readback
  fi
}

check_ci_context() {
  local expected_contexts http_status
  local protection="$tmp_dir/protection.json"
  if ! expected_contexts="$(
    jq -ce --arg owner "$GITEA_OWNER" --arg repo "$GITEA_REPO" '
      if .owner != $owner then error("owner mismatch")
      else [.repositories[] | select(.name == $repo)] |
        if length == 1 then .[0].status_check_contexts
        else error("repository missing or duplicated") end
      end
    ' "$GOVERNANCE_MANIFEST" 2>/dev/null
  )"; then
    gap ci-context '仓库不在 governance manifest 或坐标不匹配'
    return
  fi
  if ! http_status="$(api_get "$API/branch_protections/main" "$protection")"; then
    gap ci-context 'main protection 读取失败'
    return
  fi
  if [[ "$http_status" == 403 ]]; then
    skip ci-context '需要 manager/audit 权限'
    return
  fi
  if [[ "$http_status" != 200 ]]; then
    gap ci-context "main protection 读取返回 HTTP $http_status"
    return
  fi
  if jq -e --argjson expected "$expected_contexts" '
    (.status_check_contexts // []) as $actual |
    type == "object" and
    (.enable_push == false) and
    ($actual | type == "array") and
    (($actual | sort) == ($expected | sort)) and
    (.enable_status_check == (($expected | length) > 0))
  ' "$protection" >/dev/null 2>&1; then
    pass ci-context
  else
    gap ci-context 'required contexts 或禁止直推保护与 manifest 不一致'
  fi
}

if [[ "$remote" != true ]]; then
  skip labels-readback '未启用 --remote'
  skip ci-context '未启用 --remote'
elif [[ "$remote_ready" != true ]]; then
  gap labels-readback "$remote_reason"
  gap ci-context "$remote_reason"
else
  check_remote_labels
  check_ci_context
fi

if [[ "$kind" == docs ]]; then
  skip delivery-profile 'docs 仓库不声明交付形态'
elif [[ ! -f "$repo/AGENTS.md" ]]; then
  gap delivery-profile 'AGENTS.md 缺失'
else
  delivery_found=false
  placeholder_found=false
  delivery_block="$tmp_dir/delivery-profile-block"
  awk '
    /^[-*+] / {
      if (in_delivery) exit
      if ($0 ~ /交付形态/) in_delivery = 1
    }
    in_delivery && /^#{1,6}[[:space:]]/ { exit }
    in_delivery { print }
  ' "$repo/AGENTS.md" >"$delivery_block"

  while IFS= read -r line; do
    case "$line" in
      *docker-release/v2*|*PM2*|*Windows/IIS*)
        delivery_found=true
        if grep -Eq '<[^>]+>' <<<"$line"; then
          placeholder_found=true
        fi
        ;;
    esac
  done <"$repo/AGENTS.md"

  if [[ -s "$delivery_block" ]]; then
    if grep -Eq '<[^>]+>' "$delivery_block"; then
      placeholder_found=true
    elif awk '
      NR == 1 {
        line = $0
        sub(/^.*[：:][[:space:]]*/, "", line)
        gsub(/[[:space:]`*_；;]+/, "", line)
        if (length(line) > 0) found = 1
        next
      }
      /流程不变量/ { exit }
      {
        line = $0
        gsub(/[[:space:]`*_；;]+/, "", line)
        if (length(line) > 0) found = 1
      }
      END { exit(found ? 0 : 1) }
    ' "$delivery_block"; then
      delivery_found=true
    fi
  fi
  if [[ "$placeholder_found" == true ]]; then
    gap delivery-profile '交付形态命中行仍含占位符'
  elif [[ "$delivery_found" == true ]]; then
    pass delivery-profile
  else
    gap delivery-profile 'AGENTS.md 未声明明确交付形态'
  fi
fi

printf 'result: pass=%d gap=%d skip=%d\n' \
  "$pass_count" "$gap_count" "$skip_count"
if ((gap_count > 0)); then
  exit 1
fi
exit 0

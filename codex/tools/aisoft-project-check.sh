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

# Shared token resolution (#111): same-directory copy first (flat VM install
# layout), then the repository layout.
TOOL_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
if [[ -f "$TOOL_DIR/gitea-token.sh" ]]; then
  # shellcheck disable=SC1090,SC1091
  source "$TOOL_DIR/gitea-token.sh"
elif [[ -f "$TOOL_DIR/../agent/gitea-token.sh" ]]; then
  # shellcheck disable=SC1090,SC1091
  source "$TOOL_DIR/../agent/gitea-token.sh"
else
  echo 'shared gitea token resolver is unavailable' >&2
  exit 1
fi

# Shared canonical label manifest access (#108), same dual-path convention.
if [[ -f "$TOOL_DIR/gitea-label-manifest.sh" ]]; then
  # shellcheck disable=SC1090,SC1091
  source "$TOOL_DIR/gitea-label-manifest.sh"
elif [[ -f "$TOOL_DIR/../agent/gitea-label-manifest.sh" ]]; then
  # shellcheck disable=SC1090,SC1091
  source "$TOOL_DIR/../agent/gitea-label-manifest.sh"
else
  echo 'shared gitea label manifest library is unavailable' >&2
  exit 1
fi

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

# ci-merge-preview's verdict, kept for ci-outdated-branch (#299): an internal
# application may only leave block_on_outdated_branch off when this is PASS.
merge_preview_verdict=''

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

# Every change directory must resolve through resolve-documents, and no summary
# whose lifecycle claims a PR exists may leave pr_url empty (#142). Porcelain is
# tab separated so a Chinese-punctuated detail string cannot be mistaken for a
# field separator. A crash of the audit itself is reported as a GAP rather than
# skipped: "the checker did not run" must never read as "the repository is fine".
if [[ ! -d "$repo/docs/changes" ]]; then
  skip change-documents '仓库尚无 docs/changes'
  skip change-pr-url '仓库尚无 docs/changes'
else
  change_audit="$tmp_dir/change-audit"
  audit_status=0
  PYTHONPATH="$ROOT/codex/runtime" python3 -m aisoft_loop.cli \
    check-change-documents --repo "$repo" --porcelain >"$change_audit" 2>"$tmp_dir/change-audit.err" ||
    audit_status=$?
  if ((audit_status > 1)) || [[ ! -s "$change_audit" ]]; then
    gap change-documents "巡检未能运行（退出码 $audit_status）"
    gap change-pr-url "巡检未能运行（退出码 $audit_status）"
  else
    while IFS=$'\t' read -r audit_name audit_result audit_detail; do
      [[ -n "$audit_name" ]] || continue
      if [[ "$audit_result" == PASS ]]; then
        pass "$audit_name"
      else
        gap "$audit_name" "${audit_detail:-未给出细节}"
      fi
    done <"$change_audit"
  fi
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

# #223: a pull_request workflow that checks out the PR head runs a tree nobody
# will ever merge. Two parallel PRs that touch the same hand-maintained constant
# then go green independently and turn main red once both land — git sees the
# same text on both sides, calls it "both made the same change", and merges
# cleanly. This check is read-only and judges the mechanism, not one spelling of
# it: an in-run three-way merge and refs/pull/N/merge both satisfy it, because
# the merge ref is refreshed by a Gitea background task whose freshness this run
# does not control, and the project that fixed this first deliberately avoided
# it for exactly that reason.
check_ci_merge_preview() {
  local verdict detail
  local output="$tmp_dir/merge-preview-verdict"
  if ! python3 - "$repo" >"$output" 2>"$tmp_dir/merge-preview.err" <<'MERGE_PREVIEW_PY'
import pathlib
import re
import sys

repo = pathlib.Path(sys.argv[1])

CHECKOUT = re.compile(r"uses\s*:\s*\S*actions/checkout(?:@|\s|$)")
REF = re.compile(r"^\s*ref\s*:\s*(.+?)\s*$", re.MULTILINE)
MERGE_REF = re.compile(r"refs/pull/.*/merge")
CONTINUE_ON_ERROR = re.compile(r"continue-on-error\s*:\s*(?:true|True|yes|'true'|\"true\")")
SCRIPT_PATH = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_./-]*\.(?:sh|bash|mjs|cjs|js|py)\b")
# A real merge invocation: `git`, then only global flags, then `merge` as the
# subcommand. A loose pattern is worse than no check — the first draft matched
# the file names `git-credential-...sh` and `change-merge-range.sh` sitting in a
# ShellCheck list and reported a repository that runs the PR head as protected.
# `git merge-base` only asks for the common ancestor and must not read as a
# merge either.
GIT_COMMAND = (
    r"\bgit(?:\s+(?:-c\s+\S*?=(?:'[^']*'|\"[^\"]*\"|\S*)"
    r"|-C\s+\S+|--no-pager|--git-dir=\S+|--work-tree=\S+))*\s+"
)
REAL_MERGE = re.compile(GIT_COMMAND + r"merge(?![-\w])")
# Not every repository uses actions/checkout: some hand-roll the checkout with
# git init plus a shallow fetch of the event ref. Those run the PR head just the
# same, so the judged set must include them rather than silently skipping the
# repositories that are most exposed.
HAND_ROLLED_CHECKOUT = re.compile(GIT_COMMAND + r"(?:checkout|clone|fetch)(?![-\w])")
# The mechanism cannot be proven statically, so the platform requires the
# merge-preview step or the script it invokes to name itself. The reference
# implementation carries the token in its environment variables and in its
# failure codes, so a faithful adaptation satisfies this for free.
MERGE_PREVIEW_MARKER = "MERGE_PREVIEW"
MAX_SCRIPT_BYTES = 512 * 1024


def strip_noise(text):
    kept = []
    for line in text.splitlines():
        if line.lstrip().startswith("#"):
            continue
        kept.append(line)
    return "\n".join(kept).replace("\\\n", " ")


def indent_of(line):
    return len(line) - len(line.lstrip(" "))


def workflow_files():
    for relative in (".gitea/workflows", ".github/workflows"):
        directory = repo / relative
        if not directory.is_dir():
            continue
        files = sorted(
            path for path in directory.iterdir()
            if path.is_file() and path.suffix in (".yml", ".yaml")
        )
        if files:
            return relative, files
    return None, []


def significant(text):
    return [
        line for line in text.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


def triggers_pull_request(lines):
    for index, line in enumerate(lines):
        if indent_of(line) != 0:
            continue
        match = re.match(r"""(?:on|"on"|'on')\s*:\s*(.*)$""", line)
        if not match:
            continue
        inline = match.group(1).strip()
        if inline:
            return bool(re.search(r"\bpull_request\b", inline))
        body = []
        for following in lines[index + 1:]:
            if indent_of(following) == 0:
                break
            body.append(following)
        return bool(re.search(r"\bpull_request\b", "\n".join(body)))
    return False


def steps(lines):
    collected = []
    for index, line in enumerate(lines):
        if not re.match(r"^\s*steps\s*:\s*$", line):
            continue
        base = indent_of(line)
        body = []
        for following in lines[index + 1:]:
            if indent_of(following) <= base:
                break
            body.append(following)
        item_indents = [
            indent_of(item) for item in body if re.match(r"^\s*-\s", item)
        ]
        if not item_indents:
            continue
        item_indent = min(item_indents)
        current = None
        for item in body:
            if re.match(r"^\s*-\s", item) and indent_of(item) == item_indent:
                if current is not None:
                    collected.append("\n".join(current))
                current = [item]
            elif current is not None:
                current.append(item)
        if current is not None:
            collected.append("\n".join(current))
    return collected


def step_blob(step):
    parts = [strip_noise(step)]
    for candidate in SCRIPT_PATH.findall(step):
        relative = candidate.lstrip("./")
        if ".." in pathlib.PurePosixPath(relative).parts:
            continue
        target = repo / relative
        if not target.is_file():
            continue
        try:
            if target.stat().st_size > MAX_SCRIPT_BYTES:
                continue
            parts.append(strip_noise(
                target.read_text(encoding="utf-8", errors="replace")
            ))
        except OSError:
            continue
    return "\n".join(parts)


def checks_out(step_list):
    for step in step_list:
        if CHECKOUT.search(step):
            return True
        if HAND_ROLLED_CHECKOUT.search(strip_noise(step)):
            return True
    return False


def satisfied(step_list):
    for step in step_list:
        # A preview that may fail silently is not a gate.
        if CONTINUE_ON_ERROR.search(step):
            continue
        if CHECKOUT.search(step):
            for value in REF.findall(step):
                if MERGE_REF.search(value):
                    return True
        blob = step_blob(step)
        if MERGE_PREVIEW_MARKER in blob and REAL_MERGE.search(blob):
            return True
    return False


def main():
    relative, files = workflow_files()
    if relative is None:
        print("SKIP\t仓库没有 .gitea/workflows 或 .github/workflows")
        return
    judged = []
    failing = []
    for path in files:
        lines = significant(path.read_text(encoding="utf-8", errors="replace"))
        if not triggers_pull_request(lines):
            continue
        step_list = steps(lines)
        if not checks_out(step_list):
            continue
        judged.append(path.name)
        if not satisfied(step_list):
            failing.append(f"{relative}/{path.name}")
    if not judged:
        print("SKIP\t没有既由 pull_request 触发又检出仓库的 workflow")
    elif failing:
        print(
            "GAP\t" + ", ".join(failing)
            + " 在 pull_request 上跑的是 PR head，不是与 base 的合并结果；"
            + "参考 templates/project/ci/"
        )
    else:
        print("PASS\t")


main()
MERGE_PREVIEW_PY
  then
    gap ci-merge-preview '合并预览判定未能运行'
    return
  fi
  IFS=$'\t' read -r verdict detail <"$output"
  merge_preview_verdict="$verdict"
  case "$verdict" in
    PASS) pass ci-merge-preview ;;
    SKIP) skip ci-merge-preview "${detail:-未给出原因}" ;;
    GAP) gap ci-merge-preview "${detail:-未给出细节}" ;;
    *) gap ci-merge-preview '合并预览判定输出无法解析' ;;
  esac
}

check_ci_merge_preview

# #201: npm ci 命中 runner 缓存时根本不发起网络请求，所以 registry 停掉之后，
# 只用既有依赖的 PR 仍然全绿——2026-08 那次 Verdaccio 停机因此静默潜伏约 28 小时。
# 本检查只读地判断：装依赖之前有没有一条真的会去 registry 取一次东西的断言。
# 判的是机制不是拼写：任何在装依赖之前、带 AISOFT_REGISTRY_PREFLIGHT 标记、
# 且真的发起 HTTP 请求的步骤都算数。只回显标记而不请求的桩不算。
check_ci_registry_preflight() {
  local verdict detail
  local output="$tmp_dir/registry-preflight-verdict"
  if ! python3 - "$repo" >"$output" 2>"$tmp_dir/registry-preflight.err" <<'REGISTRY_PREFLIGHT_PY'
import pathlib
import re
import sys

repo = pathlib.Path(sys.argv[1])

# 判定集合只含真的装 npm 依赖的 workflow；不装依赖的仓库与本故障无关。
INSTALL = re.compile(
    r"\b(?:npm\s+(?:ci|install|i)\b|pnpm\s+(?:install|i)\b|yarn\s+install\b)"
)
CONTINUE_ON_ERROR = re.compile(
    r"continue-on-error\s*:\s*(?:true|True|yes|'true'|\"true\")"
)
SCRIPT_PATH = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_./-]*\.(?:sh|bash|mjs|cjs|js|py)\b")
MARKER = "AISOFT_REGISTRY_PREFLIGHT"
# 真的发起一次请求。只 echo 标记的桩不算断言，正如只写 MERGE_PREVIEW 而不做
# 三方合并的步骤不算合并预览。
REAL_FETCH = re.compile(r"\b(?:curl|wget)\b")
MAX_SCRIPT_BYTES = 512 * 1024


def strip_noise(text):
    kept = [line for line in text.splitlines() if not line.lstrip().startswith("#")]
    return "\n".join(kept).replace("\\\n", " ")


def indent_of(line):
    return len(line) - len(line.lstrip(" "))


def significant(text):
    return [
        line for line in text.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


def workflow_files():
    for relative in (".gitea/workflows", ".github/workflows"):
        directory = repo / relative
        if not directory.is_dir():
            continue
        files = sorted(
            path for path in directory.iterdir()
            if path.is_file() and path.suffix in (".yml", ".yaml")
        )
        if files:
            return relative, files
    return None, []


def steps(lines):
    collected = []
    for index, line in enumerate(lines):
        if not re.match(r"^\s*steps\s*:\s*$", line):
            continue
        base = indent_of(line)
        body = []
        for following in lines[index + 1:]:
            if indent_of(following) <= base:
                break
            body.append(following)
        item_indents = [
            indent_of(item) for item in body if re.match(r"^\s*-\s", item)
        ]
        if not item_indents:
            continue
        item_indent = min(item_indents)
        current = None
        for item in body:
            if re.match(r"^\s*-\s", item) and indent_of(item) == item_indent:
                if current is not None:
                    collected.append("\n".join(current))
                current = [item]
            elif current is not None:
                current.append(item)
        if current is not None:
            collected.append("\n".join(current))
    return collected


def step_blob(step):
    parts = [strip_noise(step)]
    for candidate in SCRIPT_PATH.findall(step):
        relative = candidate.lstrip("./")
        if ".." in pathlib.PurePosixPath(relative).parts:
            continue
        target = repo / relative
        if not target.is_file():
            continue
        try:
            if target.stat().st_size > MAX_SCRIPT_BYTES:
                continue
            parts.append(strip_noise(
                target.read_text(encoding="utf-8", errors="replace")
            ))
        except OSError:
            continue
    return "\n".join(parts)


def analyse(step_list):
    """回答两件事：这个 workflow 装不装依赖，以及每次安装前面有没有断言。

    先认断言再认安装，两者在同一次遍历里的顺序不能反过来：断言脚本自己的
    失败提示里会出现 npm ci 这类字样（那正是它要解释的东西），当成一次
    依赖安装就会把出厂参考自己判成 GAP。
    """
    guarded = False
    has_install = False
    protected = True
    for step in step_list:
        blob = step_blob(step)
        if MARKER in blob and REAL_FETCH.search(blob):
            # 可以静默失败的断言不是闸门，但它同样不是一次依赖安装。
            if not CONTINUE_ON_ERROR.search(step):
                guarded = True
            continue
        if INSTALL.search(blob):
            has_install = True
            if not guarded:
                protected = False
    return has_install, protected


def main():
    relative, files = workflow_files()
    if relative is None:
        print("SKIP\t仓库没有 .gitea/workflows 或 .github/workflows")
        return
    judged = []
    failing = []
    for path in files:
        lines = significant(path.read_text(encoding="utf-8", errors="replace"))
        has_install, protected = analyse(steps(lines))
        if not has_install:
            continue
        judged.append(path.name)
        if not protected:
            failing.append(f"{relative}/{path.name}")
    if not judged:
        print("SKIP\t没有安装 npm 依赖的 workflow")
    elif failing:
        print(
            "GAP\t" + ", ".join(failing)
            + " 在装依赖之前没有 registry 存活断言；registry 停掉时暖缓存会让 CI 继续变绿，"
            + "参考 templates/project/ci/registry-preflight.sh"
        )
    else:
        print("PASS\t")


main()
REGISTRY_PREFLIGHT_PY
  then
    gap ci-registry-preflight 'registry 存活断言判定未能运行'
    return
  fi
  IFS=$'\t' read -r verdict detail <"$output"
  case "$verdict" in
    PASS) pass ci-registry-preflight ;;
    SKIP) skip ci-registry-preflight "${detail:-未给出原因}" ;;
    GAP) gap ci-registry-preflight "${detail:-未给出细节}" ;;
    *) gap ci-registry-preflight 'registry 存活断言判定输出无法解析' ;;
  esac
}

check_ci_registry_preflight

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
    for name in GITEA_URL GITEA_OWNER GITEA_REPO; do
      if [[ -z "${!name:-}" ]]; then
        if [[ -n "$missing_env" ]]; then
          missing_env="$missing_env,$name"
        else
          missing_env="$name"
        fi
      fi
    done
    token_rc=0
    if [[ -z "$missing_env" ]]; then
      aisoft_resolve_gitea_token || token_rc=$?
    fi
    if [[ -n "$missing_env" ]]; then
      remote_reason="远程配置缺失: $missing_env"
    elif [[ "$token_rc" -eq 1 ]]; then
      remote_reason='远程配置缺失: GITEA_TOKEN_FILE 或 GITEA_TOKEN'
    elif [[ "$token_rc" -ne 0 ]]; then
      remote_reason='GITEA_TOKEN_FILE 未通过安全闸门'
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

# Issue numbers that still carry a label, as "#3,#12" (possibly with a trailing
# "…" when the safety bound truncates). Returns non-zero when the list could not
# be read; the caller reports that rather than silently claiming zero Issues,
# because "nothing references this label" is the answer that would authorize
# deleting it by hand.
issue_numbers_for_label() {
  local name="$1" encoded page=1 http_status page_count
  local issues_page="$tmp_dir/issues-page.json"
  local issues_all="$tmp_dir/issue-numbers"
  local truncated=false
  encoded="$(jq -rn --arg name "$name" '$name | @uri')"
  : >"$issues_all"

  while :; do
    if ! http_status="$(
      api_get "$API/issues?state=all&type=issues&labels=$encoded&limit=50&page=$page" \
        "$issues_page"
    )"; then
      return 1
    fi
    [[ "$http_status" == 200 ]] || return 1
    if ! jq -e 'type == "array" and all(.[]; type == "object" and
      (.number | type == "number"))' "$issues_page" >/dev/null 2>&1; then
      return 1
    fi
    jq -r '.[].number' "$issues_page" >>"$issues_all"
    page_count="$(jq 'length' "$issues_page")"
    ((page_count < 50)) && break
    page=$((page + 1))
    if ((page > 20)); then
      truncated=true
      break
    fi
  done

  LC_ALL=C sort -n -u "$issues_all" |
    awk -v truncated="$truncated" '
      { printf "%s#%s", (NR > 1 ? "," : ""), $0 }
      END {
        if (truncated == "true") printf "%s…", (NR > 0 ? "," : "")
        if (NR > 0 || truncated == "true") printf "\n"
      }
    '
}

# "type/legacy(#3,#12)" — a GAP the reader can act on without a second query.
label_with_issues() {
  local name="$1" numbers
  if ! numbers="$(issue_numbers_for_label "$name")"; then
    printf '%s(Issue 清单读取失败)' "$name"
    return
  fi
  if [[ -z "$numbers" ]]; then
    printf '%s(无 Issue 引用)' "$name"
    return
  fi
  printf '%s(%s)' "$name" "$numbers"
}

append_csv() {
  local accumulated="$1" entry="$2"
  if [[ -n "$accumulated" ]]; then
    printf '%s,%s' "$accumulated" "$entry"
  else
    printf '%s' "$entry"
  fi
}

check_remote_labels() {
  local page=1 http_status page_count name drift_names prefix retired_name
  local labels_all="$tmp_dir/labels-all.json"
  local labels_page="$tmp_dir/labels-page.json"
  local labels_next="$tmp_dir/labels-next.json"
  local extra="$tmp_dir/extra-labels"
  local problems='' conflict_entries='' retired_entries='' undeclared_entries=''
  local matched
  local retired_names=() declared_prefixes=()
  printf '[]\n' >"$labels_all"

  # Judge against a manifest that has been proven well-formed. A manifest whose
  # structure is unverified could turn an empty canonical set into a
  # confidently green project.
  if ! aisoft_label_manifest_validate "$LABEL_MANIFEST" 2>/dev/null; then
    gap labels-readback 'canonical label manifest 结构无效'
    return
  fi
  while IFS= read -r retired_name; do
    [[ -n "$retired_name" ]] || continue
    retired_names+=("$retired_name")
  done < <(aisoft_label_manifest_retired "$LABEL_MANIFEST")
  while IFS= read -r prefix; do
    [[ -n "$prefix" ]] || continue
    declared_prefixes+=("$prefix")
  done < <(aisoft_label_manifest_prefixes "$LABEL_MANIFEST")

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
    jq -r --slurpfile actual "$labels_all" \
      "$AISOFT_LABEL_JQ_NORMALIZE"'
        [$actual[0][] | aisoft_label_norm] as $live |
        .canonical[] | aisoft_label_norm as $want |
        select(($live | any(. == $want)) | not) |
        $want.name
      ' "$LABEL_MANIFEST" | LC_ALL=C sort | paste -sd, -
  )"
  if [[ -n "$drift_names" ]]; then
    problems="缺失或漂移: $drift_names"
  fi

  jq -r --slurpfile manifest "$LABEL_MANIFEST" '
    [$manifest[0].canonical[].name] as $canonical |
    .[] | .name as $name |
    select(($canonical | index($name)) == null) |
    $name
  ' "$labels_all" | LC_ALL=C sort -u >"$extra"

  # Every remote label outside canonical is judged against what the manifest
  # declares, not against a hard-coded allow list: retired values and managed
  # namespaces are platform-owned closed sets and stay GAPs, declared extension
  # prefixes are legitimate project dimensions, and anything else is undeclared
  # — which is what catches a typo such as aera/web that a prefix check alone
  # would wave through.
  while IFS= read -r name; do
    [[ -n "$name" ]] || continue

    matched=false
    if ((${#retired_names[@]} > 0)); then
      for retired_name in "${retired_names[@]}"; do
        if [[ "$name" == "$retired_name" ]]; then
          matched=true
          break
        fi
      done
    fi
    if [[ "$matched" == true ]]; then
      retired_entries="$(append_csv "$retired_entries" "$(label_with_issues "$name")")"
      continue
    fi

    if aisoft_label_is_managed_namespace "$name"; then
      conflict_entries="$(append_csv "$conflict_entries" "$(label_with_issues "$name")")"
      continue
    fi

    matched=false
    if ((${#declared_prefixes[@]} > 0)); then
      for prefix in "${declared_prefixes[@]}"; do
        if [[ "$name" == "$prefix"?* ]]; then
          matched=true
          break
        fi
      done
    fi
    if [[ "$matched" == true ]]; then
      printf 'INFO: labels-readback — 声明扩展标签 %s\n' "$name"
      continue
    fi

    undeclared_entries="$(append_csv "$undeclared_entries" "$(label_with_issues "$name")")"
  done <"$extra"

  if [[ -n "$conflict_entries" ]]; then
    problems="${problems:+$problems; }受管命名空间冲突: $conflict_entries"
  fi
  if [[ -n "$retired_entries" ]]; then
    problems="${problems:+$problems; }退役取值仍在用: $retired_entries"
  fi
  if [[ -n "$undeclared_entries" ]]; then
    problems="${problems:+$problems; }未声明标签: $undeclared_entries"
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

# #223 gap 2: running the merge preview is only half of it. That preview is
# computed when the workflow runs, and the merge happens later; nothing reruns
# it when someone else's PR advances base in between. block_on_outdated_branch
# is what closes that window, and the platform ruled on 2026-09-05 that it is on
# for the platform repository and every internal application. broker has no
# protection.set, so a human flips it in the Gitea UI — this check only reads it
# back, which is exactly why it belongs here rather than in a mutation path.
#
# #299 (2026-09-16) narrowed that ruling. With N open PRs the flag costs N-1 CI
# rounds per merge on a capacity-1 runner, and the internal applications already
# carry the merge preview plus a push-on-main CI run that catches the residual
# case after the fact. So for internal-application the flag is no longer
# required — provided ci-merge-preview passed in this same run. Without the
# preview the two gaps are open at once, which is exactly the #223 incident, so
# that still reads as GAP. A permitted false reads back as SKIP with the ruling
# named, never as a silent PASS, because the value still matters when a
# main-red incident is being reconstructed. The platform repository keeps the
# requirement: its ci.yml only runs on pull_request, so nothing would catch an
# expired green after merge.
check_outdated_branch() {
  local classification http_status
  local protection="$tmp_dir/protection-outdated.json"
  if ! classification="$(
    jq -re --arg owner "$GITEA_OWNER" --arg repo "$GITEA_REPO" '
      if .owner != $owner then error("owner mismatch")
      else [.repositories[] | select(.name == $repo)] |
        if length == 1 then .[0].classification
        else error("repository missing or duplicated") end
      end
    ' "$GOVERNANCE_MANIFEST" 2>/dev/null
  )"; then
    gap ci-outdated-branch '仓库不在 governance manifest 或坐标不匹配'
    return
  fi
  case "$classification" in
    public-platform | internal-application) ;;
    *)
      skip ci-outdated-branch "classification=$classification 不在裁定范围内"
      return
      ;;
  esac
  if ! http_status="$(api_get "$API/branch_protections/main" "$protection")"; then
    gap ci-outdated-branch 'main protection 读取失败'
    return
  fi
  if [[ "$http_status" == 403 ]]; then
    skip ci-outdated-branch '需要 manager/audit 权限'
    return
  fi
  if [[ "$http_status" != 200 ]]; then
    gap ci-outdated-branch "main protection 读取返回 HTTP $http_status"
    return
  fi
  if jq -e 'type == "object" and (.block_on_outdated_branch == true)' \
    "$protection" >/dev/null 2>&1; then
    pass ci-outdated-branch
    return
  fi
  case "$classification" in
    internal-application)
      if [[ "$merge_preview_verdict" == PASS ]]; then
        skip ci-outdated-branch 'block_on_outdated_branch 未打开；#299 裁决已有合并预览的 internal-application 不再要求，残余风险见 06 踩坑集 #299 条目'
      else
        gap ci-outdated-branch 'block_on_outdated_branch 未打开且 pull_request 未检出合并预览，两道保证同时缺失；#299 只允许 ci-merge-preview PASS 的 internal-application 关闭'
      fi
      ;;
    *)
      gap ci-outdated-branch 'block_on_outdated_branch 未打开，base 前进后过期的绿仍可合并'
      ;;
  esac
}

if [[ "$remote" != true ]]; then
  skip labels-readback '未启用 --remote'
  skip ci-context '未启用 --remote'
  skip ci-outdated-branch '未启用 --remote'
elif [[ "$remote_ready" != true ]]; then
  gap labels-readback "$remote_reason"
  gap ci-context "$remote_reason"
  gap ci-outdated-branch "$remote_reason"
else
  check_remote_labels
  check_ci_context
  check_outdated_branch
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

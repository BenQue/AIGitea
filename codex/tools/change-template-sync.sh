#!/usr/bin/env bash
set -euo pipefail

# Issue #190：change 文档模板以 vendored 副本形式存在于每个接入项目的
# docs/changes/_template/ 里，而 aisoft-project-check.sh 的 change-templates 查的是
# 逐字节相等。副本没有版本号也没有依赖声明，所以平台一改模板，所有下游同时静默过期。
#
# 本工具是**上游广播**：把「谁持有副本」从口头知识变成 gitea-governance.json 的
# vendors_change_templates 声明，把「模板是哪一版」变成 change-template-sync.json 里
# 钉住的 template_digest。改动模板而不刷新 digest，平台自己的 required CI 会红；
# 刷新 digest 时工具打印完整的下游同步清单。
#
# 明确不做的事（#190 验收标准三）：**不在任何下游项目引入阻塞式 required check。**
# 那要求下游每个 PR 去 clone 平台仓做比对，等于把上游演进变成下游全部在途 PR 的阻塞，
# 而这条 GAP 的修复代价只是一次复制覆盖。约束由 change-template-sync.json 的
# downstream_required_check: forbidden 与 codex/tests/smoke.sh 一起钉住。
#
# 只读，除非显式 --refresh-digest；后者只改本仓库的 manifest，不访问远端、不碰凭据。
#
# 退出码：0 = 无需动作；3 = 需要动作（digest 漂移，或有 holder 副本过期/缺失）；
# 64 = 用法错误；1 = 硬错误。

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
SYNC_MANIFEST="$ROOT/codex/config/change-template-sync.json"
GOVERNANCE_MANIFEST="$ROOT/codex/config/gitea-governance.json"
ACCESS_MANIFEST="$ROOT/codex/config/host-access-broker.json"

mode=plan
porcelain=false
today=''

usage() {
  cat >&2 <<'USAGE'
usage: change-template-sync.sh [--porcelain]
       change-template-sync.sh --verify-digest
       change-template-sync.sh --refresh-digest [--today YYYY-MM-DD] [--porcelain]

  (默认) plan          打印 digest 状态与每个 holder 的副本状态
  --verify-digest      只核对钉住的 digest 是否等于当前模板内容（平台 CI 用）
  --refresh-digest     把 digest 刷新为当前模板内容，并打印下游同步清单
USAGE
  exit 64
}

while (($# > 0)); do
  case "$1" in
    --porcelain)
      porcelain=true
      shift
      ;;
    --verify-digest)
      [[ "$mode" == plan ]] || usage
      mode=verify
      shift
      ;;
    --refresh-digest)
      [[ "$mode" == plan ]] || usage
      mode=refresh
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

[[ "$mode" != verify || "$porcelain" == false ]] || usage

command -v jq >/dev/null || {
  echo 'change-template-sync 需要 jq' >&2
  exit 1
}

for manifest in "$SYNC_MANIFEST" "$GOVERNANCE_MANIFEST" "$ACCESS_MANIFEST"; do
  jq empty "$manifest" >/dev/null 2>&1 || {
    printf 'manifest 不是合法 JSON: %s\n' "$manifest" >&2
    exit 1
  }
done

jq -e '.contract_version == "change-template-sync/v1"' "$SYNC_MANIFEST" >/dev/null || {
  echo 'change-template-sync.json 的 contract_version 不受支持' >&2
  exit 1
}

# 非阻塞是本机制的合同面，不是默认值：声明被改掉时工具停机，而不是安静地继续跑。
jq -e '.downstream_required_check == "forbidden"' "$SYNC_MANIFEST" >/dev/null || {
  echo '本机制禁止下游阻塞式 required check；downstream_required_check 必须是 forbidden' >&2
  exit 1
}

template_root_rel="$(jq -r '.template_root' "$SYNC_MANIFEST")"
template_root="$ROOT/$template_root_rel"
pinned_digest="$(jq -r '.template_digest' "$SYNC_MANIFEST")"

# 计数用独立的整数而不是 ${#array[@]}：空数组在 bash 3.2 的 set -u 下会报 unbound，
# 而把长度和缺省写在一起（${#array[@]:-0}）在 bash 5 里是 bad substitution——本机是
# bash 3.2、CI runner 是 bash 5，只有绕开这个构造才两边都成立。
documents=()
document_count=0
while IFS= read -r document; do
  [[ -n "$document" ]] || continue
  documents+=("$document")
  document_count=$((document_count + 1))
done < <(jq -r '.documents[]' "$SYNC_MANIFEST")
((document_count > 0)) || {
  echo 'change-template-sync.json 的 documents 为空' >&2
  exit 1
}
for document in "${documents[@]}"; do
  [[ "$document" == *.md && "$document" != */* && "$document" != .* ]] || {
    printf 'documents 只接受本目录下的 .md 文件名: %s\n' "$document" >&2
    exit 1
  }
  [[ -f "$template_root/$document" ]] || {
    printf '合同源模板缺失: %s/%s\n' "$template_root_rel" "$document" >&2
    exit 1
  }
done

if [[ -n "$today" ]]; then
  # 形状对了不等于日期存在：2026-13-99 能通过正则，写进 manifest 就是一个假日期。
  [[ "$today" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]] || usage
  python3 - "$today" <<'DATEPY' >/dev/null 2>&1 || usage
import datetime
import sys

datetime.date.fromisoformat(sys.argv[1])
DATEPY
fi

# digest 覆盖「文件名 + 内容」两者：改名或增删一份模板同样必须刷新 manifest。
compute_digest() {
  python3 - "$template_root" "${documents[@]}" <<'PY'
import hashlib
import sys
from pathlib import Path

root = Path(sys.argv[1])
outer = hashlib.sha256()
for name in sys.argv[2:]:
    inner = hashlib.sha256((root / name).read_bytes()).hexdigest()
    outer.update(f"{name}\n{inner}\n".encode("utf-8"))
print("sha256:" + outer.hexdigest())
PY
}

computed_digest="$(compute_digest)"

if [[ "$mode" == verify ]]; then
  if [[ "$pinned_digest" == "$computed_digest" ]]; then
    printf 'digest: pinned %s\n' "$pinned_digest"
    exit 0
  fi
  cat >&2 <<EOF
digest 漂移：$template_root_rel 的内容与 codex/config/change-template-sync.json 钉住的值不一致。
  pinned:   $pinned_digest
  computed: $computed_digest
改动模板的这次变更必须同时刷新 digest 并广播下游：
  bash codex/tools/change-template-sync.sh --refresh-digest
EOF
  exit 3
fi

digest_message=''
if [[ "$mode" == refresh ]]; then
  if [[ "$pinned_digest" == "$computed_digest" ]]; then
    digest_message="digest: 已是当前值，manifest 未改动 $computed_digest"
  else
    stamp="${today:-$(date +%F)}"
    python3 - "$SYNC_MANIFEST" "$computed_digest" "$stamp" <<'PY'
import json
import sys
from pathlib import Path

path, digest, stamp = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
manifest = json.loads(path.read_text(encoding="utf-8"))
manifest["template_digest"] = digest
manifest["digest_updated"] = stamp
path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8")
PY
    digest_message="digest: 已刷新 $pinned_digest -> $computed_digest"
  fi
  # 刷新之后 digest 不再是待办；退出码只反映下游副本的状态。
  pinned_digest="$computed_digest"
fi

# holder 的判定只看声明，不看下游内容：平台一改模板，所有声明持有副本的项目按定义
# 全部过期，本机有没有该项目的 checkout 不影响这个结论。下面的逐项比对只是附加信息，
# 用来区分「已经同步过」与「还没同步」。
holders=()
holder_count=0
while IFS= read -r holder; do
  [[ -n "$holder" ]] || continue
  holders+=("$holder")
  holder_count=$((holder_count + 1))
done < <(
  jq -r '.repositories[]
         | select(if has("vendors_change_templates")
                  then .vendors_change_templates else true end)
         | .name' \
    "$GOVERNANCE_MANIFEST"
)
not_vendored_count="$(
  jq '[.repositories[]
       | select(has("vendors_change_templates") and
                .vendors_change_templates == false)] | length' \
    "$GOVERNANCE_MANIFEST"
)"

((holder_count > 0)) || {
  echo 'gitea-governance.json 里没有任何声明持有模板副本的仓库' >&2
  exit 1
}

# 结论取自本机 checkout 的**工作树**，不是该仓库 main 的当前状态。checkout 落后或停在
# 别的分支时，stale/missing 可能是 checkout 的状态而不是仓库的状态，因此非 main 分支
# 一律标注出来——否则一个停在 feature 分支的 checkout 会读成「这个仓库没有模板」。
checkout_branch_note() {
  local checkout="$1" branch
  branch="$(git -C "$checkout" rev-parse --abbrev-ref HEAD 2>/dev/null || true)"
  if [[ -n "$branch" && "$branch" != main ]]; then
    printf '（checkout 停在分支 %s）' "$branch"
  fi
}

checkout_for() {
  jq -r --arg name "$1" \
    '(.projects[] | select(.repository == $name) | .mac_checkout) // "" | tostring' \
    "$ACCESS_MANIFEST"
}

# porcelain 模式的 stdout 是给机器读的制表符流；digest 侧的说明走 stderr，
# 免得刷新动作把机器输出污染成「多了一行不认识的记录」。
notice() {
  if [[ "$porcelain" == true ]]; then
    printf '%s\n' "$1" >&2
  else
    printf '%s\n' "$1"
  fi
}

current_count=0
stale_count=0
missing_count=0
unverified_count=0

emit() {
  local name="$1" status="$2" detail="$3" checkout="$4"
  if [[ "$porcelain" == true ]]; then
    printf '%s\t%s\t%s\t%s\n' "$name" "$status" "$checkout" "$detail"
  else
    printf '%-18s %-11s %s\n' "$name" "$status" "$detail"
  fi
}

if [[ -n "$digest_message" ]]; then
  notice "$digest_message"
fi
if [[ "$porcelain" == false ]]; then
  printf 'holders: %s（另有 %s 个仓库声明不持有副本）\n' \
    "$holder_count" "$not_vendored_count"
fi

for name in "${holders[@]}"; do
  checkout="$(checkout_for "$name")"
  if [[ -z "$checkout" || "$checkout" == null ]]; then
    unverified_count=$((unverified_count + 1))
    emit "$name" unverified '本机无 checkout，必须由持有 checkout 的主机复核' ''
    continue
  fi
  if [[ ! -d "$checkout/docs/changes/_template" ]]; then
    if [[ ! -d "$checkout" ]]; then
      unverified_count=$((unverified_count + 1))
      emit "$name" unverified "checkout 路径不存在: $checkout" "$checkout"
    else
      missing_count=$((missing_count + 1))
      emit "$name" missing \
        "缺少 docs/changes/_template$(checkout_branch_note "$checkout")" "$checkout"
    fi
    continue
  fi
  drifted=''
  for document in "${documents[@]}"; do
    if ! cmp -s "$template_root/$document" "$checkout/docs/changes/_template/$document"; then
      if [[ -n "$drifted" ]]; then
        drifted="$drifted,$document"
      else
        drifted="$document"
      fi
    fi
  done
  if [[ -z "$drifted" ]]; then
    current_count=$((current_count + 1))
    emit "$name" current '' "$checkout"
  else
    stale_count=$((stale_count + 1))
    emit "$name" stale "$drifted$(checkout_branch_note "$checkout")" "$checkout"
  fi
done

if [[ "$porcelain" == false ]]; then
  printf 'result: current=%s stale=%s missing=%s unverified=%s\n' \
    "$current_count" "$stale_count" "$missing_count" "$unverified_count"
  if ((stale_count > 0 || missing_count > 0 || unverified_count > 0)); then
    cat <<'EOF'
同步方式（每个项目一条独立的 Issue → change 分支 → PR，不在下游加任何阻塞闸门）：
  cp <平台仓>/templates/docs/changes/_template/*.md <目标仓>/docs/changes/_template/
unverified 不等于已同步：本机读不到那个 checkout，结论必须由能读到的主机给出。
EOF
  fi
fi

if ((stale_count > 0 || missing_count > 0)) || [[ "$pinned_digest" != "$computed_digest" ]]; then
  exit 3
fi
exit 0

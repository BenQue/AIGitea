#!/usr/bin/env bash
# 合并预览参考实现（AISoft 平台 Issue #223）。
#
# 把工作区从「PR 分支自己的 head」推进到「head 与 base 当前尖端的合并结果」，
# 让 pull_request 那一路的必需检查验的是合并后的树。
#
# 为什么需要它：pull_request 事件上的 checkout 默认取的是 PR 分支自己的 head。
# 两个并行 PR 只要触碰同一个手工维护的常数——断言里的条目数、错误码总数、
# 迁移编号、显式枚举的清单长度——就会各自绿、合并后主干红：三方合并的 base 是旧值、
# 两侧文本恰好相同，git 判为「双方做了相同修改」，干净合并、零冲突标记，
# 留下的却是两侧各自算对、合起来算错的那个值。冲突检测比较文本，
# 这里两侧文本相同而含义不同，所以它看不见。
#
# 为什么不用 refs/pull/N/merge：Gitea 确实维护这个 ref，但它由后台任务在
# 「计算可合并性」时刷新，新鲜度不由本次 CI 运行决定。base 刚前进而 ref 尚未重算时，
# 检出它会得到一个对着旧 base 的合并结果——一个静默的假绿，恰好是要消灭的东西。
# 改成在运行那一刻现取 base 尖端、现场做三方合并，「过期」这个失败模式从根上不存在；
# 剩下的只有「合不上」，而那一条本脚本明确报错退出。
#
# 失败即退出，绝不回退到 head 继续跑：一个跑在 head 上的绿，恰恰是事故里那个
# 骗过所有人的绿。宁可红着说清原因。
#
# 前置：调用它的 checkout 必须取到足以求 merge-base 的历史（fetch-depth: 0）。
# 只在 pull_request 事件上调用；push 那一路本来就跑在真实的目标分支上。
set -euo pipefail

REMOTE=${MERGE_PREVIEW_REMOTE:-origin}
BASE_REF=${MERGE_PREVIEW_BASE_REF:-}
HEAD_SHA_EXPECTED=${MERGE_PREVIEW_HEAD_SHA:-}
DEFAULT_BASE_REF=${MERGE_PREVIEW_DEFAULT_BASE_REF:-main}

fail() {
  echo "[merge-preview] $1" >&2
  echo "[merge-preview] 本次运行不会回退到 PR head 继续；合并预览拿不到就不给结论。" >&2
  exit 1
}

if [ -z "$BASE_REF" ]; then
  # 事件载荷没给 base 时退到 workflow 触发器钉死的那个分支。这是有依据的常量，
  # 不是对「合并预览拿不到」的静默回退——后者一律 fail。
  BASE_REF="$DEFAULT_BASE_REF"
  echo "[merge-preview] base ref 未由事件载荷给出，按触发器取 $BASE_REF"
else
  echo "[merge-preview] base ref = $BASE_REF（来自事件载荷）"
fi

if [ -n "$(git status --porcelain)" ]; then
  fail "MERGE_PREVIEW_DIRTY: 工作区在合并之前就不干净，无法判定合并结果"
fi

HEAD_SHA=$(git rev-parse HEAD)
if [ -n "$HEAD_SHA_EXPECTED" ] && [ "$HEAD_SHA" != "$HEAD_SHA_EXPECTED" ]; then
  fail "MERGE_PREVIEW_HEAD_MISMATCH: 工作区在 $HEAD_SHA，事件载荷说 PR head 是 $HEAD_SHA_EXPECTED"
fi

# 现取 base 尖端。取的是这一刻的 base，不是事件载荷里那个可能已经过期的 base.sha。
if ! git fetch --no-tags "$REMOTE" "+refs/heads/$BASE_REF:refs/remotes/$REMOTE/$BASE_REF"; then
  fail "MERGE_PREVIEW_BASE_UNREACHABLE: 取不到 $REMOTE/$BASE_REF"
fi
BASE_SHA=$(git rev-parse "refs/remotes/$REMOTE/$BASE_REF")

echo "[merge-preview] PR head = $HEAD_SHA"
echo "[merge-preview] base $BASE_REF 当前尖端 = $BASE_SHA"

if ! git merge-base "$BASE_SHA" "$HEAD_SHA" >/dev/null 2>&1; then
  # 浅克隆找不到共同祖先时会走到这里。给出错误结论比给出错误的合并更重要。
  fail "MERGE_PREVIEW_NO_MERGE_BASE: 找不到 $BASE_SHA 与 $HEAD_SHA 的共同祖先（克隆深度不够或历史无关）"
fi

if git merge-base --is-ancestor "$BASE_SHA" "$HEAD_SHA"; then
  echo "[merge-preview] MERGE_PREVIEW_ALREADY_UP_TO_DATE: base 已是 head 的祖先，"
  echo "[merge-preview] 合并结果与 head 的树逐字节相同，本次检出即合并预览。"
  echo "[merge-preview] 已检出 SHA = $HEAD_SHA"
  exit 0
fi

if ! git -c user.name='CI merge preview' -c user.email='ci@merge-preview.invalid' \
  merge --no-ff --no-edit \
  -m "merge-preview: $BASE_REF@$BASE_SHA into PR head@$HEAD_SHA" "$BASE_SHA"; then
  echo "[merge-preview] 冲突文件：" >&2
  git diff --name-only --diff-filter=U >&2 || true
  git merge --abort || true
  fail "MERGE_PREVIEW_CONFLICT: PR head 与 $BASE_REF@$BASE_SHA 有真实冲突，合并预览不存在"
fi

MERGE_SHA=$(git rev-parse HEAD)
echo "[merge-preview] 已检出 SHA = $MERGE_SHA"
echo "[merge-preview] 它的父提交 = $(git rev-list --parents -n 1 HEAD | cut -d' ' -f2-)"
echo "[merge-preview] 该 SHA 既不是 PR head（$HEAD_SHA）也不是 base（$BASE_SHA）；"
echo "[merge-preview] 下面所有步骤跑的都是这棵合并后的树。"

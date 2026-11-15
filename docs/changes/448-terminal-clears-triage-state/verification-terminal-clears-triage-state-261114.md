---
issue: 448
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/448
change_type: bugfix
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - shared-core
  - external-contract
depends_on: []
status: pending
branch: change/448-terminal-clears-triage-state
created: 2026-11-14
updated: 2026-11-15
---

# 终态写入清除 triage 状态标签 · 验证记录

## 基线与范围

- Commit SHA: 本地验证与 R1 审查的候选 `a1fdb1afe4b7a8113bbce6ef0ba0d0b64abe3086`；R1 修复后的候选见「交叉审查」R2 行。
- 基线：`origin/main` = `2c65c8371d7b92b7e25f7a9cec687b6d359e3e59`
- 环境: macOS 本机；Claude Opus 5.5（实现，provider claude）；Codex GPT-6-Astra high（只读交叉审查）
- 本记录负责证明的 acceptance criteria: AC-1–AC-8。AC-7 在合并前只证明命令与步骤就绪，执行结果在合并后写成 Issue 评论。

## Before：缺陷与已安装状态

| 观察 | 层 | 结果 |
|---|---|---|
| typed `gitea.issue.list --state all` 清点（2026-11-14，只读） | live | 已关闭且已终态、仍挂 triage state：aisoft-platform 13、hsdb 3、newemaint 13、localwms 34、sfm-digital-board 0；myapp、smoke-test `CREDENTIAL_UNAVAILABLE`，NOT RUN |
| `grep -c TRIAGE_WONTFIX_LABEL /usr/local/lib/aisoft-host-access/aisoft_host_access/broker.py` | installed | `0`：已安装 broker 没有本修复，合并后必须两台重装 |

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| 反向证明 T01：新增 broker/项目来源用例在旧 `_set_issue_lifecycle` 上运行 | RED（预期） | `PYTHONPATH=. python3 -m unittest tests.test_host_access tests.test_project_declared_source -k terminal -k replaces_only`：13 个子用例 FAIL（终态 8、重写 2、wontfix 2、项目来源 1），改写后的非终态用例照旧通过 |
| T01 修复后同一入口 | PASS | `Ran 206 tests ... OK`（两个模块全量） |
| 反向证明 T04：新增部署钩子用例在旧 `mark-deployed-issues.sh` 上运行 | RED（预期） | PUT 体为 `{"labels":[1,9,20,21,23,50]}`，期望 `{"labels":[1,9,21,50]}`：triage state 20、23 未移除 |
| T04 修复后 `bash codex/tests/test-mark-deployed-issues.sh` | PASS | `mark-deployed tests passed` |
| `bash -n` 与 `shellcheck` 两个改动的 shell 文件 | PASS | 无输出，退出码 0 |
| `bash codex/tools/usage-bundle.sh --release 1.24.1 ... --compatibility patch` 后 `--verify` | PASS | `VERIFIED 1.24.1 sha256:bf7058d9ea6f7e15c7da23d6e9c9cf717f03936cdbff404828db23f30b9f1218`；R1 修复改的 02/03、部署钩子不是发布包成员，修复后重跑仍同值 |
| `bash codex/tests/smoke.sh`（候选 `a1fdb1af`） | PASS | `smoke rc=0`；runtime `Ran 839 tests ... OK` |
| `bash codex/tests/smoke.sh`（R1 修复后候选） | 见 R2 行 | 修复提交后重跑 |
| `aisoft classify --verify 448` | PASS | `result: projected`，`bugfix` / `complex` |
| `aisoft check-change-documents` 与 `aisoft classify 448` 文档预检 | PASS | `gap=0`；`文档预检 #448: OK` |

## 已知边界

- `aisoft_loop/gitea.py` 的 `set_triage_labels` 要求写入目标「恰好一个 category 和一个 state」。它只约束写入时的目标集合，且仓库内没有生产调用方，与终态后只留 category 不冲突，不改。
- 项目自声明来源（`aisoft-access`）随使用发布包分发；项目升到 1.24.1 之前仍是旧行为。项目升包属于各项目自己的对齐动作。
- 已关闭但没有终态的 Issue、`triage/wontfix` 的 Issue 与开放 Issue 不做批量改写（spec 非范围）。

## 交叉审查

| 轮次 | 实现方 | 审查方 | 审查的 head | 结论 |
|---|---|---|---|---|
| R1 | Claude Opus 5.5 | Codex GPT-6-Astra / high，hc 终端 `review-448`（t3m），Herdr 标签页「AISoftPlatform #448 review (codex 只读)」可见，`-s read-only -a never` | `a1fdb1afe4b7a8113bbce6ef0ba0d0b64abe3086` | FAIL：2 P2 1 P3 |

R1 findings 与处置：

- [P2] `codex/tools/mark-deployed-issues.sh` 是第二个终态写者，直接 PUT `deployed`，不清 triage state，也不拦 wontfix。处置：属范围扩张，负责人 2026-11-15 选择并入 #448（spec D6、AC-8、plan T04）；钩子按同一规则收口，wontfix 跳过并告警且退出码仍为 0。
- [P2] verification 仍为占位稿，缺 AC-7 的重装命令与读回步骤。处置：本文件补齐「合并后：重装与读回」「合并后：存量清理（D5）」两节。
- [P3] 项目来源测试未覆盖 no-op 无 PUT、`deployed` 与拒写无 PUT。处置：`test_project_declared_source.py` 补三类断言。

R1 中 Codex 在只读沙箱里跑两模块全量 unittest 得到 116 个 errors，原因是沙箱不能建临时目录，不是代码失败；它单独跑的 8 个相关用例全部通过，并在内存里用 BASE 方法做了反向验证（12 个预期失败）。

## 合并后：重装与读回（AC-7，负责人执行 sudo）

broker 行为改变（D4），Mac 与 gitea-ci VM 两台都要重装。部署钩子与文档不经 installer，随合并生效。

1. 会话侧：broker `git.fetch.main`，确认 merge commit 在 `origin/main`，再把 Mac 主 checkout 快进：

   ```bash
   git -C /Users/benque/MyDocs/AISoftPlatform merge --ff-only origin/main
   ```

2. 负责人在 Mac 上执行（installer 会先打印 `source commit`，应等于 merge commit 且 level with origin/main）：

   ```bash
   cd /Users/benque/MyDocs/AISoftPlatform && sudo bash codex/install-host-access-broker.sh
   ```

3. 负责人在 VM 上执行（经 OrbStack，读同一检出）：

   ```bash
   orb -m gitea-ci sudo bash /mnt/mac/Users/benque/MyDocs/AISoftPlatform/codex/install-host-access-broker.sh
   ```

4. 会话读回：
   - Mac：`bash codex/tools/check-installed-drift.sh`；VM：`/usr/local/bin/orb -m gitea-ci bash /mnt/mac/Users/benque/MyDocs/AISoftPlatform/codex/tools/check-installed-drift.sh --host vm`；Mac 上 `bash codex/tools/aisoft-platform-readiness.sh`。
   - 两台 `grep -c TRIAGE_WONTFIX_LABEL /usr/local/lib/aisoft-host-access/aisoft_host_access/broker.py` 由 `0` 变为非零。
   - installed 层正向证据：对本 Issue #448 跑 `aisoft complete --project aisoft-platform --range <合并 range>` 看计划，再 `--apply 448`，读回 `gitea.issue.labels.read --number 448` 不再含 `triage/needs-triage`。
   - 结论写一条 #448 评论（`gitea.issue.comment`）。

## 合并后：存量清理（D5，重装读回 PASS 之后）

只走 typed 操作，不拼 token 或 URL。先 dry-run 出计划，负责人确认后再 apply，最后用同一读取复核。只处理「已关闭、恰有一个终态标签、挂 triage state、不挂 `triage/wontfix`」的 Issue，重写的是它现有的终态。

```bash
B=/usr/local/libexec/aisoft/host-access-broker
PLAN=<scratch>/triage-cleanup-plan.tsv
for p in aisoft-platform hsdb localwms newemaint sfm-digital-board; do
  "$B" --project "$p" --operation gitea.issue.list --state closed |
    jq -r --arg p "$p" '.issues[]
      | [.labels[]? | if type == "string" then . else .name end] as $l
      | ($l | map(select(. == "completed" or . == "deployed"))) as $t
      | select(($t | length) == 1)
      | select($l | index("triage/wontfix") | not)
      | select($l | any(startswith("triage/") and . != "triage/bug" and . != "triage/enhancement"))
      | "\($p)\t\(.number)\t\($t[0])\t\($l | map(select(startswith("triage/"))) | join(","))"'
done > "$PLAN"
```

人确认 `$PLAN` 后 apply，逐条记录返回体：

```bash
while IFS=$'\t' read -r p n t _; do
  "$B" --project "$p" --operation gitea.issue.labels.set --number "$n" --lifecycle "$t" |
    jq -c --arg p "$p" '{project: $p, issue, result, before, after}'
done < "$PLAN"
```

复核：重跑 dry-run 循环，计划应为空。myapp、smoke-test 无可用凭据，记 NOT RUN。dry-run 计划、apply 结果与复核写一条 #448 评论。

---
issue: 379
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/379
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - platform-governance
  - shared-core
depends_on: []
status: verified
branch: change/379-skills-single-source
created: 2026-10-18
updated: 2026-10-18
---

# #379 验证记录

## 基线与范围

- Commit SHA: 首轮实现 head `daa2f96`；审查修复后 head 见下文「Codex 交叉审查」；最终候选 head 见确认点 2
- 基线：`origin/main` = `8fa4458`
- 环境: macOS 本机（bash 3.2、`/opt/homebrew/bin/rg`），Cursor 3.24.12
- 本记录负责证明的 acceptance criteria: AC1–AC9

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| `bash codex/tests/smoke.sh`（`daa2f96`） | PASS | `Ran 1238 tests … OK`；`PASS: project-leak (14 baseline files, 92 hits)`；`Codex platform static smoke checks passed.` |
| `bash codex/tests/test-install-claude-skills.sh` | PASS | 含新断言：Claude 落点不含 `agents/`；未声明的 `skills/ghost-skill` 让安装 fail closed |
| `bash codex/tests/test-installer-source-guard.sh` | PASS | `8 installers x 3 source states` |
| `bash codex/tests/test-installed-drift.sh` | PASS | 35 个用例 OK；删除 `skills/` 下文件仍被源 scope 看到 |
| `PYTHONPATH=. python3 -m unittest tests.test_routine_merge.SessionContractTests`（`codex/runtime`） | PASS | 12 个用例，中文单份正文的钉子与突变拒绝 |
| `bash codex/tests/test-usage-bundle.sh` | PASS | 三种项目级落点；Codex 专用 `agents/` 不进 Claude/Cursor；仅 codex 的技能不进 Claude/Cursor |
| `bash codex/tests/test-external-skill-versions.sh` | PASS | Cursor 缺失、落后、一致、超前、无清单、两版本六种情形；读取前后 home 快照不变 |
| `bash codex/tools/usage-bundle.sh --verify --baseline-ref origin/main` | PASS | 审查修复后重发 `VERIFIED 1.1.0 sha256:926b9a4c…`（1.1.0 未上 main，按规则清空重发同号）；1.0.0 原样为前缀 |
| 临时 HOME 安装读回 | PASS | 两条安装命令后 `codex/check-drift.sh`、`skill-for-claude/check-drift.sh` 均 `CLEAN`；`check-installed-drift.sh --target-home` 中 `install-skills`（8/8）与 `skill-for-claude/install`（2 技能、3 references）为 `INSTALLED PASS` |
| 本机只读 `bash codex/tools/check-external-skill-versions.sh` | PASS | `SUPERPOWERS cursor BEHIND cached=6.1.1 adapted=7.0.0`；`MATT cursor BEHIND cached=1.2.0 pinned=1.3.1`；`RESULT PASS`（落后只提示，不升级） |
| 单家工具名守卫反向证明 | PASS | 往技能副本追加 `spawn_task` 后守卫的 `rg` 命中该行 |
| 合并后两侧重装与本机读回 | NOT RUN | 合并后按交接执行 |

## 正文合并对照（AC2）

| 来源独有内容 | 合并后位置 |
|---|---|
| Codex `aisoft-platform`：读合同与 TCC 路径 | `## 读合同` |
| Codex：project profile 选定、governance manifest、routine opt-in、`ci-bot` 退役、不把变更路径当检查捷径 | `## 目标项目与 governance manifest` |
| Codex：私有 Gitea 确定性访问七条 | `## 私有 Gitea 的确定性访问` |
| Codex：标签语义、显式 complex、spec/plan/verification 要求、Matt 初始化 | `## 现行合同` 对应条目 |
| Codex：受治理状态、Loop 自修复边界、配置上限 | `## approved 之后默认自主推进`、`## 只在这些情况暂停` |
| Codex：Controller 与 Mac 两条 PR URL 回填路径 | `## PR URL 回填的两条路径` |
| Codex：部署边界、保护平台七条、provider 对等、`gitea-*` adapter | `## 部署边界`、`## 保护平台`、`## 工具分工` |
| Claude `aisoft-platform`：会话标准动作、外部技能包边界、Common Mistakes | 原样保留；标准动作新增第 5 步交叉审核 |
| Codex `issue-session-flow`：默认自主推进的 push 边界 | `## approved 之后默认自主推进` 末句 |
| Codex：manual 候选模板、projection-mismatch 与不可读结果处置 | `## 确认点 2：准备提交最终 PR` |
| Codex：收尾“绝不推断已部署”、独立验收标准开新 Issue | `## 收尾` 第 3、6 步 |
| Codex：多 Issue 协调的分支隔离、不变量 | `## 派单`、`## 不变量` |
| Claude `issue-session-flow`：派单、标题、会话间消息、归档的工具调用 | 改为能力名并写降级做法（文首能力表） |

## Codex 交叉审查

审查方：Codex（Herdr 只读会话，`--sandbox read-only --ask-for-approval never`），未参与实现。

| 轮次 | 审查 head | 结论 | 发现与处置 |
|---|---|---|---|
| 1 | `605c196` | FAIL | major：`skills.manifest` 决定落点却不在发布摘要内 → 作为 skill 成员纳入，`--build` 不导出它，缺成员即拒绝，补 targets-only 突变用例；major：Cursor 缓存里非普通目录被报成 `NOT_INSTALLED` → 改报 `UNKNOWN`，补两个用例；major：共享解析器 `codex/lib/skills-manifest.sh` 未进安装指纹 → 加入 `INSTALLER_HELPER_PINS`、来源集合与 scope，补篡改用例；minor：终态钉子弱于旧版 → 恢复语义钉子并加三条突变；minor：缺交叉审核结构守卫 → smoke 补 `03`、`08`、两个技能的锚；minor：bash 与 Python 对 `claude,` 解析不一致 → 拆分前整体校验，补反例；minor：project-align 两条相对链接失效 → 改为 `../../../` |
| 2 | `4c9036b` | FAIL | 第 1 轮 7 条确认已修复；新 minor：smoke 逐字钉了平台技能里的一句正文 → 改钉它指向 `03` §「交叉审核」的引用；顺带修掉 ShellCheck SC2066（单元素 for 循环） |
| 3 | `d7be649` | PASS | 第 2 轮 minor 确认已修复；`git_scope` 精确覆盖 `8fa4458..d7be649` 的 77 个路径（含 17 次改名前后路径），无遗漏、多余或重复；无新发现 |

修复后全量 smoke：`4c9036b` 与 `d7be649` 均通过（各 1238 个用例）。最终候选只比 `d7be649` 多本记录这一处文档改动。

R6b（#380，PR 382，`a395f7a`）先合并后，按 broker 的 main 集成合同把 `a395f7a` 合入本分支（merge commit，父提交为 [本 Issue 分支, main]，树等于 `git merge-tree` 结果；已推送的 `22845ed` 保留在历史里）。唯一的重叠是路线表 R6b/R7 相邻两行：先把本分支的 R7 行退回 main 原文，合并后再单独恢复。合并结果与先前在 `a395f7a` 上 rebase 的版本内容逐字节相同（`git diff` 只差本段记录），rebase 版在 macOS 全量 smoke 通过（1238 个用例）；`git_scope` 与新 diff 一致；main 没有发布新的发布包版本，1.1.0 `--verify --baseline-ref origin/main` 仍通过。

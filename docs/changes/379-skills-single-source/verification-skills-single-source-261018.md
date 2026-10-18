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
status: pending
branch: change/379-skills-single-source
created: 2026-10-18
updated: 2026-10-18
---

# #379 验证记录

## 基线与范围

- Commit SHA: 实现 head `daa2f96`（T03–T04）；最终候选 head 见确认点 2
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
| `bash codex/tools/usage-bundle.sh --verify --baseline-ref origin/main` | PASS | `VERIFIED 1.1.0 sha256:82a6633c…`；1.0.0 原样为前缀 |
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

待执行。

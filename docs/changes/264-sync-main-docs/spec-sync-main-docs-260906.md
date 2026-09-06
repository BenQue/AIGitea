---
issue: 264
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/264
change_type: docs
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: unchanged
confidence: high
risk_flags:
  - agent-governance
  - platform-governance
depends_on: []
status: approved
branch: change/264-sync-main-docs
created: 2026-09-06
updated: 2026-09-06
---

# Spec · 主文档与 AGENTS.md 目录同步到 09-05 合并批次现状

## 目标与原因

把平台仓的总纲 README、根 `AGENTS.md` 目录节、`08`、`04` 与 onboarding-runbook 同步到 2026-09-03 之后
合并的八个 Issue（#222/#223/#225/#228/#243/#250/#252/#254）之后的仓库现状。Issue #264 正文列出的 7 项
漂移是合同源，本 spec 把每一项落成「文件:位置 → 现状 → 改后」的可核清单，不扩范围。行号以
`origin/main` = `54602a3d`（PR #263 merge）为准。

## 术语

- **目录节**：根 `AGENTS.md` 第 35–57 行 `## 目录` 段；本 Issue 只授权修改这一节，`## 工作原则` 与 `## Git`
  一字不动。
- **8 个 installer**：`codex/install-vm.sh`、`codex/install-skills.sh`、`codex/install-host-role.sh`、
  `codex/install-host-access-broker.sh`、`architecture/install.sh`、`sync/install.sh`、`docker-release/install.sh`、
  `skill-for-claude/install.sh`；`grep -l install-source-guard` 对这 8 个全部命中。
- **09-05 批次**：上述八个 Issue 的 merge（`af15294` #222、`6caeb2c` #223、`3df14be` #225、`a790c13` #228、
  `071b6b0` #243、`00f7d53` #250、`9a6a9fc` #252、`bc57edf` #254）。
- **`analysis_provider` 允许集合**：`codex/runtime/aisoft_host_access/contract.py:514` 的 `{"claude","codex","none"}`；
  `profiles.py:301` 把它渲染为该 VM profile 的 `ANALYSIS_PROVIDER=`。

## 逐条清单

### A · 根 `AGENTS.md` 目录节（Issue 第 1、2 条；独立原子 commit）

| # | 位置 | 现状 | 改后 |
|---|---|---|---|
| A-01 | `AGENTS.md:42` 之后（交付形态参考子列表内） | 无 `company-delivery/` | 新增子项：`company-delivery/`：Linux 容器化（两台公司 VM 离线交付）——operator bundle、脱敏 inventory、Stage 00–110 人工 runbook 与 evidence 的参考实现。参考、非部署步骤事实源。 |
| A-02 | `AGENTS.md:49` | `codex/skills/`…（含 `aisoft-matt-workflow`） | （含 `aisoft-matt-workflow` 与 `issue-session-flow`） |
| A-03 | `AGENTS.md:54` | 只列 `codex/install-*.sh` 四个 | 列全 8 个 installer，并注明全部经 `codex/lib/install-source-guard.sh` 做 source provenance 与 staleness 闸门，不复制凭据 |
| A-04 | `AGENTS.md:55` 之后 | 无 `skill-for-claude/` | 新增：`skill-for-claude/`：Claude 侧 skills 源（`aisoft-platform`、`issue-session-flow`）与 `skills.manifest`/`install.sh`/`check-drift.sh`；references 与 Codex 侧共用 `skill-for-codex/references/` |
| A-05 | `AGENTS.md:56` | 无 `templates/project/` | 在同一行补：`templates/project/`：项目 `AGENTS.md`/`CLAUDE.md` 指针模板与 `ci/`（CI workflow、merge-preview、registry-preflight 参考，#223） |

改后目录节必须与 `ls -d */` 的 10 个目录（`architecture/ archive/ codex/ company-delivery/ docker-release/ docs/
skill-for-claude/ skill-for-codex/ sync/ templates/`）一一对应；`docs/` 由 `docs/changes/` 语义文档与
`docs/agents/` Matt 配置构成，目录节以 `docs/changes/`、`docs/agents/` 形式覆盖（工作原则节已引用）。

### B · `README.md`（Issue 第 3、4、5 条）

| # | 位置 | 现状 | 改后 |
|---|---|---|---|
| B-01 | `README.md:3` | `更新：2026-09-03`；状态句只含 #208 | `更新：2026-09-06`；状态句改为「#252 后治理集合只保留 LocalWMS 与 NewEMaint；09-05 批次扩展 broker typed 操作、CI 停滞判定、项目 CI 参考模板、Issue 入口标签与 8 个 installer 共用 source guard；#208 routine small 受控合并 source 合同不变，全部 complex/major/阶段完结与强制风险变更仍须人工合并，installed/live 启用仍须单独验收」 |
| B-02 | `README.md:11` | `## 1. 当前状态（2026-09-03）` | `## 1. 当前状态（2026-09-06）` |
| B-03 | `README.md:19` 之后 | 无 09-05 批次 broker 条目 | 新增 🟡 条目：#222 `gitea.issue.list`/`gitea.issue.state.set`；#225 actions 日志头尾投影、零值时间戳 `null`；#228 `orbstack.runner.status` 停滞探针与 per-job 超时取值（判定手册 `06` §1.0.1/§1.0.2）；typed 操作生效需两台重装 |
| B-04 | 同上 | 无治理集合/入口标签条目 | 新增 ✅ 条目：#252 五个项目统一退出、治理 manifest 只保留 LocalWMS 与 NewEMaint；#243 `gitea.issue.create` 立案即带入口标签、调度会话清扫开放 Issue |
| B-05 | 同上 | 无安装面条目 | 新增 ✅ 条目：8 个 installer 共用 `codex/lib/install-source-guard.sh`（#162/#171 抽库，#182/#250/#254 补齐）；Claude 侧 skills 由 `skill-for-claude/install.sh` 安装、`check-drift.sh` 核对 |
| B-06 | 同上 | 无项目 CI 参考条目 | 新增 🟡 条目：#223 `templates/project/ci/`（CI workflow、merge-preview、registry-preflight）与 `aisoft-project-check.sh` 的 `ci-merge-preview`/`ci-outdated-branch`/`ci-registry-preflight` 回读；采纳由项目仓自行接入验收 |
| B-07 | `README.md:153` | `17 条实证踩坑` | `27 条实证踩坑、CI 停滞判定手册（§1.0.1/§1.0.2）` |
| B-08 | `README.md:160` 之后（§5 主表之后、「交付形态参考」之前） | 无 `skill-for-claude/` 入口 | 新增小节「技能安装与漂移核对」：Codex 侧 `codex/install-skills.sh <target-home>` → `~/.agents/skills/`，`codex/check-drift.sh`；Claude 侧 `skill-for-claude/install.sh <target-home>` → `~/.claude/skills/`，`skill-for-claude/check-drift.sh`（`CLEAN`/`DRIFT`/`NOT_INSTALLED`）；两侧共用 `skill-for-codex/references/`；8 个 installer 均经 source guard |

B-03～B-06 的每个 Issue 编号都必须以 `#N` 字面出现在 §1（验收第 2 条）。保留 `codex/runtime/tests` 钉住的
短语「两台公司」「本地 OrbStack」「exact `docker-release/v2` bytes」「Architecture declaration/lock」与
`smoke.sh` 钉住的 README 字面量。

### C · `08-双工具共存与实施.md`（Issue 第 5、7 条）

| # | 位置 | 现状 | 改后 |
|---|---|---|---|
| C-01 | `08:80` | 初始化段只写 `codex/install-skills.sh <target-home>` | 同句追加：Claude 侧等价入口 `skill-for-claude/install.sh <target-home>`（装到 `~/.claude/skills/`，两侧共用 `skill-for-codex/references/`），改动源后用 `skill-for-claude/check-drift.sh` 核对回 `CLEAN` |
| C-02 | `08:41` 之后（§3 配置与认证） | 无 `analysis_provider` 说明 | 新增一条：每项目 VM profile 的 `analysis_provider`/`implement_provider`（`codex/config/host-access-broker.json` `projects[].vm_profile`）取值 `codex`/`claude`/`none`，定义见 `04` §4；`implement_provider` 迁移期固定 `none` |

### D · `04-Agent编排与定时任务.md`（Issue 第 7 条，唯一定义处）

| # | 位置 | 现状 | 改后 |
|---|---|---|---|
| D-01 | `04:84` 之后（§4 末尾、`## 5` 之前） | 无 `analysis_provider` 定义 | 新增段落「每项目 `analysis_provider`」：由 `codex/config/host-access-broker.json` `projects[].vm_profile.analysis_provider` 声明（#164/#178），安装时渲染为该 VM profile 的 `ANALYSIS_PROVIDER`；`contract.py` 只接受 `codex`（该 VM 用 Codex CLI 经 `codex/agent/analyze-codex.sh` 跑 analyzer）、`claude`（用 Claude Code CLI 经 `analyze-claude.sh`）、`none`（该项目不跑自动 analyzer，判级由交互式会话完成）；取值必须是该 VM 服务层真实可执行的运行时，`implement_provider` 迁移期固定 `none` |

### E · `skill-for-codex/references/onboarding-runbook.md`（Issue 第 6 条）

| # | 位置 | 现状 | 改后 |
|---|---|---|---|
| E-01 | `runbook:113` 之后（§2 `CLAUDE.md` 条目之后） | 未提 `templates/project/ci/` | 新增条目：需要平台 CI 参考时从 `templates/project/ci/` 复制 `ci.yml`、`merge-preview.sh`、`registry-preflight.sh`（#223），按项目 required contexts 与 registry 调整；采纳由 `aisoft-project-check.sh` 的 `ci-merge-preview`/`ci-registry-preflight` 回读 |

该 references 由 `skill-for-claude/install.sh` 装进 Claude 侧 `aisoft-platform/references/`，改后本机
`check-drift.sh` 立即 `DRIFT`；本 Issue 内重装并回 `CLEAN`。

## Acceptance criteria

- [ ] AC-1 `AGENTS.md` 目录节与 `ls -d */` 的 10 个目录一一对应；installer 一行列全 8 个并含
  `codex/lib/install-source-guard.sh`；`codex/skills/` 一行含 `issue-session-flow`；
  `git diff origin/main...HEAD -- AGENTS.md` 只落在第 35–57 行范围内，且是独立 commit。
- [ ] AC-2 `README.md:3` 与 `:11` 日期均为 `2026-09-06`；§1 以 `#N` 字面含 #222、#223、#225、#228、#243、#250、
  #252、#254 各至少一次；§5 06 一行含 `27 条`，且 27 等于 `06` 表格最大编号。
- [ ] AC-3 `grep -c 'skill-for-claude/install.sh' README.md 08-*.md` 各 ≥ 1，`grep -c 'check-drift.sh'` 各 ≥ 1，
  且与 `codex/install-skills.sh` 出现在同一段。
- [ ] AC-4 runbook §2 含 `templates/project/ci/`；`04` §4 含 `analysis_provider` 及 `codex`/`claude`/`none` 三个取值的
  定义；`08` 引用 `04` §4 而不重复定义。
- [ ] AC-5 `bash codex/tests/smoke.sh` rc=0；`bash skill-for-claude/install.sh` 后 `bash skill-for-claude/check-drift.sh`
  输出 `CLEAN`；`check-change-documents --repo <worktree>` 全部 PASS。
- [ ] AC-6 `git diff --stat origin/main...HEAD -- codex/skills/` 为空；`docs/changes/*/summary` 的 `status` 与
  `09` 第 526 行不变。

## 接口、数据与兼容性影响

无代码、manifest、schema 或 broker 操作表变更。`04` §4 新增段落是对既有 manifest 字段的文档定义，
不改变 `contract.py` 的允许集合。安装到 Claude 侧的 references 字节随 E-01 变化，属安装面内容更新。

## 治理文件授权

本 spec 即修改根 `AGENTS.md` 的授权，范围**仅限**目录节（A-01～A-05），作为独立原子 commit；工作原则节与
`## Git` 节不得触碰，本 run 也没有任何依赖该目录节的 runtime 实施。onboarding-runbook 是安装到两侧 skill
的 Agent 行为源，改动范围仅限 E-01 一条。`codex/skills/*/SKILL.md` 正文不改（Codex 侧由人在 Codex 会话另行自查）。

## 风险与回滚约束

- `smoke.sh` 与 `codex/runtime/tests` 的 `grep -Fq`/`assertIn` 字面量：改动只增不删这些短语；实现前先
  `rg` 测试目录确认。
- README §1 条目文字不得把 source 合并写成 live 已启用：broker typed 操作「生效需两台重装」必须写明。
- 回滚 = revert 唯一 PR；Claude 侧已安装 references 用上一版源重跑 `skill-for-claude/install.sh` 即恢复。

## 非目标

- 不改 `03`、`06`、`09`、`codex/skills/`、`codex/runtime/`、`codex/tools/`、`codex/config/`、`templates/`、
  `docker-release/`、`architecture/`、`company-delivery/`、任何 manifest 或 Gitea live 状态。
- 不给 `check-drift.sh`/installer 加新检查；不重装 Codex 侧 `~/.agents/skills`。
- 不处理 GitHub 镜像落后、远端非 legacy 分支等盘点其它残留（另有裁决项）。

## 未决问题

无。两项解读（`analysis_provider` 定义放 `04` §4；README 的技能安装入口作为 §5 的独立小节）在确认点 1 认可。

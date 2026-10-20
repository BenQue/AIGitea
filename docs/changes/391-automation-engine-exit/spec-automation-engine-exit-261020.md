---
issue: 391
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/391
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - shared-core
  - schema-change
  - cross-module
  - rollback
  - agent-governance
  - platform-governance
depends_on:
  - 389
status: approved
branch: change/391-automation-engine-exit
created: 2026-10-20
updated: 2026-10-20
git_scope:
  - docs/changes/391-automation-engine-exit/summary-automation-engine-exit-261020.md
  - docs/changes/391-automation-engine-exit/spec-automation-engine-exit-261020.md
  - docs/changes/391-automation-engine-exit/plan-automation-engine-exit-261020.md
  - docs/changes/391-automation-engine-exit/verification-automation-engine-exit-261020.md
---

# #391 spec：自动化引擎退出（R10a，按 ADR 0002）

## 目标与原因

ADR 0002 D2/D4：VM 上的 Development Loop、routine 自动合并与 VM profile 退出平台 `main`，平台只剩一条在用的开发路径（交互会话 + 确定性会话工具）。代码、broker 操作、安装面、manifest、VM 单元与文档要一致。裁决输入 D1 a′、D2、D3 已齐（项目库 `platform-remediation-plan-261020-final.md` §2、§4 R10a）。

## 已核对的事实（2026-10-20，`origin/main` `0192a8e`，只读）

1. `aisoft_loop` 中 `controller`、`provider`、`verifier`、`state`、`routine_merge` 只被 `cli.py` 与彼此引用；`gitea.py:23` 只从 `verifier` 取 `redact`（纯函数），需先迁入 `gitea.py`。`analysis.py` 只被 `cli.py` 引用；`render-analysis` 一支只服务 analyzer 脚本。
2. `codex/agent` 中 `gitea-token.sh`、`gitea-label-manifest.sh`、`change-merge-range.sh`、`aisoft-project-target.sh` 被 `codex/tools/*` 引用，保留；其余 10 个脚本（含 `common.sh`）只服务 Loop，`common.sh` 的函数无一被保留脚本或工具使用。
3. CLI 子命令 `run`、`confirm-pr`、`validate-provider`、`validate-analysis`、`analysis-slug`、`parse-change-branch`、`extract-json`、`render-analysis` 只有 Loop 调用方。`get-issue`、`list-issues`、`apply-analysis` 在任务书保留清单里，但当前也只有 Loop 调用方（`apply-classification-labels.sh` 只用 `resolve-documents`）。
4. broker 有 39 个操作，其中 `gitea.pull.merge.routine` 与 `vm.profile.{plan,apply,read-back,rollback}` 待退役；登记点：两份 broker manifest（真实与夹具）、`aisoft_host_access/contract.py` 的 `EXPECTED_OPERATIONS` 与唯一 merge 例外、`broker.py` 分派、`runner.py` 的 `RoutineMergeRunner`、`cli.py` 的 `merge_operation_count`、`codex/tests/test-host-access-broker.sh` 的 39/1 计数、`test_host_access.py`。
5. `vm_profile_policy` 只有 `runtime_user` 仍有在用读者：`orbstack.vm.units.read`（#387，readiness 与 Mac 告警依赖）。其余键只服务 `profiles.py` 与 profile CLI。K1 凭据托管只读 `mac_host.credential_*` 与 `credential_rotation_policy`。
6. governance：真实 manifest 已无 `routine_live_pilot`（#385），只剩夹具里的 pilot 与非目标仓封印；`routine_merge_agent_policy` 有五个读者：governance contract/cli、broker 的 routine 合并与 audit 的 routine 段、`credential_rotation.py`（在 `project.routine_merge_agent` 非空的分支内）。七个仓库 `routine_auto_merge_enabled` 都是 `false`，只有 LocalWMS 仍声明 `localwms-routine-merger`。
7. `host.access.audit` 的 PASS/GAP 只来自 routine 段（`broker.py:4284`）；协作者分页盘点那一套（`_CollaboratorInventoryBudget` 等）只服务「已声明 merger 但账号缺失」的路径。
8. installer 7 个：`install-vm`、`install-skills`、`install-host-role`、`install-host-access-broker`、`architecture/install.sh`、`sync/install.sh`、`skill-for-claude/install.sh`。`check-installed-drift.py` 用 `INSTALLER_PINS` 钉每个 installer 的 sha256。
9. VM（broker `orbstack.vm.units.read`）：coder 用户只剩 `agent-poll.timer`（disabled，service failed）与 systemd 自带的 `systemd-tmpfiles-clean.timer`；没有 `aisoft-agent@*` 定时器。
10. 发布包当前 1.2.0；本批要改的成员有 `usage/CONTRACT.md`、`templates/project/AGENTS.md`、`templates/docs/agents/*`、`aisoft-platform` 技能及其两份 references、`issue-session-flow`、`aisoft-matt-workflow`。其它分支尚未占用 1.3.0。
11. `aisoft_main_integration.py` 有一支按 `aisoft-loop` 安装目录名解析模板路径；它在非目标里，本批不动，那一支成为死路径（R14/R16 清理）。

## 决定（确认点 1 默认值，负责人可覆盖）

- **routine 字段冻结而不删字段。** 删除 broker 操作、`RoutineMergeRunner`、`routine_merge.py`、`routine_merge_agent_policy`、`routine_live_pilot` 与非目标仓封印、audit 的 routine 段与只为它存在的协作者盘点；`routine_auto_merge_enabled` 与 `routine_merge_agent` 两个字段保留，合同要求所有仓库分别为 `false`、`null`（fail closed）。理由：PAT 轮换、bootstrap 工具与 Go PAT helper 按这个字段工作，属 K1 凭据托管（本批非目标）；字段恒空后它们的 routine 分支不可达，删除放 R16。
- **`vm_profile_policy` 收窄为 `vm_runtime: {runtime_user}`**，删除 `mac_host.vm_profile_tool`、项目 `vm_profile` 段、`profiles.py`、`project-profile-migration.sh` 与 profile CLI。`ANALYSIS_PROVIDER`/`IMPLEMENT_PROVIDER` 概念随之退出。
- **CLI 只留会话工具**：`change-name`、`resolve-documents`、`resolve-required-documents`、`check-change-documents`、`backfill-pr-url`、`publish-spec`、`publish-plan`、`claim-worktree`、`scan-worktrees`，以及任务书点名保留的 `get-issue`、`list-issues`、`apply-analysis`（事实 3：当前无调用方，按任务书保留，去留交 R11 的 `aisoft` 入口统一决定）。
- **兼容 adapter 技能**（`gitea-analyze-change`、`gitea-development-loop`、`gitea-implement-change`）保留名字，只删 Loop/provider/routine 措辞，指向交互会话流程；去留归 R10b/R14。
- **发布包升 1.3.0**；若 R10b 或 R10c 先合并并占用 1.3.0，本批以 merge commit 集成 `main` 后发下一版本。

## Acceptance criteria

- [ ] AC1 迁出说明 `archive/automation-engine-exit-261020.md` 按 `archive/reference-implementations-exit-261019.md` 的格式列出全部删除路径、最后所在 commit 与去向，注明 provider adapter 的形状可按 ADR 0002 D3 在 Mac 重建；`git grep` 对 `provider-poll`、`loop-controller`、`IMPLEMENT_PROVIDER`、`vm.profile`、`merge.routine` 只命中 `docs/changes/`、`archive/`、`docs/adr/` 与 `06` 踩坑表。
- [ ] AC2 Loop 代码退出：上列 5 个模块、`analysis.py` 的 render 支、10 个 Loop 脚本、`codex/systemd/`、`codex/install-vm.sh`、`templates/agent/`、只测 Loop 的测试删除；`cli.py` 只剩上述子命令；保留测试中的 `redact`、import hygiene 等断言迁到仍存在的对象上。
- [ ] AC3 broker 操作 39 → 34：五个操作在两份 manifest、合同、分派、runner、CLI 计数、shell 与 Python 测试中同步退役；`validate` 输出 `operation_count` 34 且不再有 merge 操作；`install-host-access-broker.sh` 把 `project-profile-migration` 列入退役清单，漂移检查把它放进 absent。
- [ ] AC4 manifest：LocalWMS `routine_merge_agent` 置 `null`；真实与夹具 manifest 删除 `vm_profile` 段、`routine_merge_agent_policy`、夹具 pilot，`vm_profile_policy` 改为 `vm_runtime`；`aisoft_host_access.cli validate` 与 `aisoft_gitea_governance.cli validate` 对真实与夹具 manifest 都 PASS；改源码 runtime 跑 `host.access.audit` 对七个项目 PASS（候选 manifest，免重装）。
- [ ] AC5 installer 集合为 6：`check-installed-drift --source-only` PASS；`test-installer-source-guard.sh`、漂移夹具测试、README、`06` §1.0 安装面表同步。
- [ ] AC6 文档最小改动：`04` 压成「候选状态与迁出说明」一页；`08` §4、§6 压缩；`03` §2.1 改为「routine 已退出」并清理 §7/§9 的 routine 条目；README 原则 6/7/9、架构图与时序图去掉 Analyzer/Loop 泳道与 routine 分支；`GLOSSARY.md`、`06` 安装面与凭据表、`usage/CONTRACT.md` §2、`templates/project/AGENTS.md`、`templates/docs/agents/*`、`docs/agents/*`、技能与 references 中的 Loop/provider/routine 现行表述改为交互会话流程；被删测试钉住的技能短语若仍有意义，迁到保留测试。路线图 R10a 行改状态。
- [ ] AC7 治理文件受控步骤：`AGENTS.md`（Development Loop、Controller、`IMPLEMENT_PROVIDER=none`、routine auto 四处）与 `codex/global-AGENTS.md` 单独 commit，提交后停下重读，再改 runtime。
- [ ] AC8 `bash codex/tests/smoke.sh` 全绿；泄漏基线只降不升；`usage-bundle.sh --release 1.3.0`（或集成后的下一版本）后 `--verify` 通过；改 shell 后 `bash -n` 与 ShellCheck 通过。
- [ ] AC9 Codex `codex exec -s read-only` 对候选 head 只读交叉审查 PASS，结论写项目库 `codex-review-391.md` 与 verification；合并前 `apply-classification-labels.sh --verify 391` 读回 `projected`。
- [ ] AC10 合并后（负责人执行，会话给完整命令并读回）：两台重装 broker 与技能；VM coder 家目录删除 `agent-poll.*` 单元、`aisoft-agent@*` 单元（如有）、`~/.config/aisoft/projects/*.env`、`~/.local/state/aisoft-loop/`、`~/.local/lib/aisoft-loop/`；`orbstack.vm.units.read` 读回无 aisoft/agent-poll 定时器与单元（systemd 自带的 `systemd-tmpfiles-clean.timer` 不在范围）；删除 `localwms-routine-merger` 账号、Mac canonical store 与 VM 下的凭据文件后 `host.access.audit` 对七个项目 PASS；`check-installed-drift` 读回无 `install-vm` 面、无残留 `profiles.py`。

## 接口、数据与兼容性影响

- broker 操作减为 34，旧调用方（只有 Loop 与 profile 工具）随本批一起删除。已安装 runtime 在重装前仍认识旧操作，行为不变。
- manifest schema 变化：顶层 `vm_profile_policy` → `vm_runtime`，删除 `routine_merge_agent_policy`，项目删除 `vm_profile` 键。两侧 manifest 合同同步修改，只改一侧 broker 全部 fail closed（由 validate 与 smoke 拦截）。
- 项目使用层：发布包 1.3.0 去掉 provider 字段与 routine-auto 表述；已 pin 1.2.0 的项目不受影响，升级由项目自己的 Issue 决定。
- VM：`install-vm` 面退出后平台不再向 VM 安装 Loop runtime；VM 上 broker 由 `install-host-access-broker.sh` 安装，不受影响。

## 风险与回滚约束

- 删错会话工具依赖：AC2 的保留清单按 `git grep` 调用方核对，smoke 覆盖 `codex/tools/*` 的测试。
- 两侧 manifest 不一致：validate、smoke、合并后先 VM 再 Mac 重装并读回。
- 回滚：revert 本 PR 后两台重装即恢复代码与操作；VM 单元与 `localwms-routine-merger` 账号删除后不能由 revert 恢复，因此排在合并、重装、audit 读回 PASS 之后，且两者本来就处于停用状态。

## 非目标

- 不改 K1 凭据托管（PAT 轮换、bootstrap、Go PAT helper）、`git.push.change`、`aisoft_main_integration.py`；不改 Matt vendor。
- 不做文档全面现行态重写（R14），不实现路由卡（R10b），不做漂移棘轮与 `applies_to`（R16）。
- 不删除兼容 adapter 技能本身。

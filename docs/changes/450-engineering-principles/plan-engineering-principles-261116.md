---
issue: 450
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/450
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - agent-governance
  - platform-governance
depends_on: []
branch: change/450-engineering-principles
created: 2026-11-16
updated: 2026-11-16
---

# Plan：共享工程原则的收敛改进

## 全局约束与接口

- 唯一执行合同为本 plan 的 Txx；负责人指定 Claude Code 实施，显式 provider 为 claude，R3：frontier/max、spec-plan、full+reverse-proof、cross-provider、confirm: 2，具体 skills 为 to-spec, to-tickets, executing-plans, verification-before-completion。
- exact worktree、owner、change_base、全部 git_scope 和冻结候选见 spec。Claude 先按交接说明以自己的真实 session 接管已交回的 worktree；一次只有接手会话一个写者，按依赖 frontier 执行，不 reset、重写历史或操作其他会话。
- 本轮只补合同，T01 / T02 都保持 pending。负责人同意已记录，不按文档、ticket、普通测试或合法本地 commit 重复询问；真正合同冲突或扩范围按既有规则升级。
- T01 治理提交后 STOP；T02 必须由 fresh run 重新读取批准合同、治理 diff、当前规则、owner / branch / HEAD 后恢复。同一线程普通工具调用或压缩不算 fresh run，旧运行不得自行宣布已满足。
- 最终独立审核由未参与实现的 Codex 只读会话承担，通过 Herdr 官方 CLI 使用可见独立会话，记录实际型号、推理强度、BASE / HEAD 与完成状态；审核者不得写入 worktree。不得把之前的 Claude 方案审核或 Claude 自审当作本轮 cross-provider 证据。用户处理登录、信任和权限提示。
- Claude 使用 superpowers 的 executing-plans，Txx 仍是唯一合同；prepare-ticket 产生的 Task N 只作派生视图，不另写人工计划。不把 Matt implement 的逐票双轴义务外推给此 SP 路径；最终整批 cross-provider 要求保留。
- 隔离构建仅写本票在临时目录创建的导出产物；不修改真实 HOME、安装或 adopt，不创建第二套验证系统，不新写镜像原则文字的单元测试。
- required CI 以已核对 governance manifest 的 `CI / verify (pull_request)` 为准；本地 smoke 不代表远端 CI 已通过。

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 将冻结原则文案和同字节使用包登记形成可回退的治理候选，受控提交后停止 | - | pending |
| T02 | fresh run 完成候选验证、隔离分发、独立审核及证据，形成最终 PR 候选 | T01 | pending |

## T01：受控应用原则文案与发布登记

- **交付/范围**：只应用本票冻结 patch 到 engineering-principles.md，以现有工具追加 usage/bundle.json release；记录准备证据，不改模板、适配器、runtime 或真实安装面。
- **blocked_by**：无。
- **AC**：AC-1、AC-2、AC-3、AC-4、AC-5 的源码与发布登记部分、AC-6 的受控治理步骤。
- **接口/约束**：遵守全局约束；开始前用 `bash codex/tools/aisoft prepare-ticket 450 T01 --provider claude` 记录 ticket_base / 初始状态，按返回的派生视图调用 executing-plans。先核实批准合同、owner 和基线原则摘要；冻结 patch 无法干净应用时停止分析，不能模糊套用。
- **验证**：
  1. `git apply --check --unidiff-zero docs/changes/450-engineering-principles/proposals/engineering-principles.patch`，通过后才应用。
  2. 应用后的原则全文 SHA-256 等于 spec 固定值；`git apply --reverse --check --unidiff-zero docs/changes/450-engineering-principles/proposals/engineering-principles.patch` 成功。
  3. `bash codex/tools/usage-bundle.sh --release 1.24.2 --today <实施日> --compatibility patch --notes '细化共享工程原则的结果验证、证据来源与重复问题改进，不新增流程硬门（#450）'`。版本占用时只按 spec 顺延。
  4. `bash codex/tools/usage-bundle.sh --verify --baseline-ref c14a86d4ad0d1fd5938ab31343f8d72acd486a71`；比较 bundle members 集合和既有 releases 前缀保持不变。
  5. `git diff --check`；`bash codex/tools/aisoft check-change-documents --porcelain`；逐项审议 spec 场景与反例，检查无未授权路径。
- **Expected**：冻结文案精确应用，反向可匹配；已有版本不可变且新增包摘要匹配源码；指导没有转成全任务硬门。此处不证明实际 Agent 效果、真实安装、项目采用或远端 CI。
- **停止条件**：同范围治理文件应用后独立本地 commit，记录 exact HEAD、验证结果和未完成核验，立即 STOP。T01 的候选完整性与实际完成判定由 fresh run 补齐；不为 SP 增加 Matt 逐票双轴审核。证据不齐时不把 T01 写成 complete，也不提前启动 T02。范围、合同或冻结文字须实质改变时先升级。

## T02：fresh run 核验与最终候选

- **交付/范围**：fresh run 接回同一 claimed worktree，先完成 T01 待完成的候选核验与真实完成判定；依赖满足后执行 T02。只补本票证据 / 状态及 review-evidence-index 本票行，完成最终候选，不接续 runtime 实施。
- **blocked_by**：T01。
- **AC**：AC-1、AC-2、AC-3、AC-4、AC-5、AC-6。
- **接口/约束**：先按全局约束复核治理 handoff，以 `prepare-ticket 450 T01 --provider claude --resume` 恢复并核对语义身份；固定其实际 HEAD，核对 ticket_base 到 HEAD 的内容、staged / unstaged / untracked 遗漏与真实结果。T01 证据完整后再 `prepare-ticket 450 T02 --provider claude`。复用真正覆盖同一范围的既有验证，不因技能名再叠加轮次。
- **验证**：
  1. `AISOFT_USAGE_BASELINE_REF=c14a86d4ad0d1fd5938ab31343f8d72acd486a71 LC_ALL=C bash codex/tests/smoke.sh`。
  2. `bash codex/tools/usage-bundle.sh --build <本票新建的隔离目录>`；逐个比较 `project/{.agents,.claude,.cursor}/skills/aisoft-platform/references/engineering-principles.md` 与当前源码字节相同。保存实际目录和比较结果，不把它称为安装。
  3. 重查 patch 反向匹配、实际候选全文摘要和 spec 反例。完整 smoke 已含 bundle 未发版、成员漂移和已发布历史不可变等负向夹具；确认这些既有检查确实执行。不额外重复已通过的定向测试，也不伪称文本审议是模型行为测试。
  4. 记录全部必要本地结果后形成固定 candidate_head，确认 `change_base..HEAD` 全批仅含 git_scope，检查 staged / unstaged / untracked 遗漏。Herdr 中未参与实现的独立 Codex 审核整个固定范围；修复后追加 commit、重验并审新 HEAD。治理返修仍独立提交、STOP / fresh run。
  5. 本票 verification 交叉审查表与 review-evidence-index 记录实际 BASE / HEAD、提供者、型号 / 强度、结论及 findings。仅证据提交改变 HEAD 时审实际证据 diff 并记录新的范围覆盖，不冒用旧 PASS。
  6. `bash codex/tools/aisoft classify --apply 450` 后单独 `bash codex/tools/aisoft classify --verify 450`，读回 projected；`check-change-documents --porcelain`、`git diff --check c14a86d4ad0d1fd5938ab31343f8d72acd486a71..HEAD` 和范围核对通过。
- **Expected**：现有本地必需回归通过；三端导出等字节；独立审核覆盖全部实际变更及 AC，风险表述无新增硬门；分类与路由读回一致，未执行的 CI / 安装 / 采用明确标注。证据不能证明长期缺陷率或人的处理成本已有改善。
- **停止条件**：形成 AWAITING_PR_CONFIRMATION 候选后停下，等待既有确认点 2。提交后 required CI、人工 merge 及合并后收尾按原合同处理。本计划没有授权实际安装、项目采用或部署。

## Expected touch points

- T01：`skills/aisoft-platform/references/engineering-principles.md`、`usage/bundle.json`，以及本目录已有证据区；冻结 patch 不因方便应用而静默改写。
- T02：本目录 plan 执行证据 / 状态与 verification、必要 summary 状态、`docs/governance/review-evidence-index.md` 本票一行。任何修改不得扩出 spec 的八个 exact 路径。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | 冻结 patch、全文 SHA-256、反向 apply check 与来源审议 |
| AC-2 | diff 和 spec 场景 / 反例，确认不改 route / 模板 / execution-adapter |
| AC-3 | 独立运行 / 转述 / 静态 / NOT RUN 的文本例子与实际报告抽查 |
| AC-4 | 归因维度、结构改进边界及效果声明的反例审议 |
| AC-5 | bundle verify、历史前缀和 members 比较、隔离 build 三端字节比对 |
| AC-6 | 文档 / scope 检查、完整 smoke 与既有负向夹具、STOP / fresh run、实际候选 cross-provider 与 classify 读回 |

## 执行证据

<!-- execution-evidence:start -->
2026-11-16：仅完成合同准备。T01 / T02 未开始，ticket_base、治理 candidate_head、完整 smoke、隔离 build 与实际补丁交叉审查均 NOT RUN。已有方案审核及准备阶段检查见映射 verification；不拿方案审核代替实施审核。
2026-11-16：负责人指定后续开发交给 Claude Code；在任何 prepare-ticket / 实施之前同步 provider、技能映射及独立审查方。尚无旧执行回执需要 resume，不得冒用原 Codex writer；接手回执由新会话记录。
2026-11-16：Claude Code 会话 `f2cce2e4-3bb8-4160-87a4-9b9a1a5ee664` 以 `claim-worktree --takeover` 接管（result=taken-over），`prepare-ticket 450 T01 --provider claude` 回执 status=prepared、ticket_base `4d4321dee233dc55116539f77799817595108167`、初始 staged / unstaged / untracked 均空。冻结 patch 精确应用、bundle 追加 1.24.2；治理提交 `9358cdf5aff69c12dccb3acb140dc49d0cbedff1` 只含原则与 bundle 两个文件，随后 STOP。T01 状态保持 pending：真实完成判定由 fresh run 以 `--resume` 恢复后补齐；T02 未开始。
<!-- execution-evidence:end -->

## 部署与回滚

无部署、全局安装或项目采用。本地候选和发布后回退按 spec，已发布 bundle 历史只追加。最终 PR 由人确认提交并人工合并。

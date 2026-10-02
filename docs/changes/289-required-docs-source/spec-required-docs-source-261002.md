---
issue: 289
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/289
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
confidence: high
risk_flags:
  - shared-core
  - platform-governance
depends_on: []
status: approved
branch: change/289-required-docs-source
created: 2026-10-02
updated: 2026-10-02
---

# #289 文档声明与事实一致性合同

## 目标与原因

声明一份 verification 必须承担交付真实文件的义务。读回的角色、实际文件与终态判断共享同一份校验后结果，文件缺失时不得 PASS 或写 completed。本合同修复既有治理承诺，因共享核心/平台治理强制 complex、唯一最终 PR 使用 manual。

复现已确认，精确根因与原 Issue 的推测不同：当前 development route 已保留 verification，load_contract 能拒绝缺文件；resolve-documents 忽略缺映射文件，audit 只调用该 resolver，terminal 再用 awk 读取另一份声明，因此仍有假绿。本 spec 以真实复现约束行为。

## 统一事实源

1. summary front matter 的 `required_docs` 是声明角色的唯一事实源；`documents` 是新格式角色到安全 basename 的唯一事实源。通过同一个受限 Python 解析器，拒绝空/未知/重复/混合角色与 legacy 文件名；summary 必须首项，不另建 awk YAML 解析规则。
2. `route.required_docs` 是 change_control/复杂度导出的**最低合同要求**，不能删除声明角色、不能替代声明本身；load_contract 保留原路由判级，校验每个最低要求被声明满足。development 无强制 spec/plan，production complex 仍须 spec/plan。低风险路由也不得让已声明 verification 消失；不新增部署推断。
3. 新格式 `documents` 每个显式映射文件均须存在、是当前 Issue 目录内可读取普通文件，并通过既有角色/slug/日期/front matter 校验；包括 required_docs 之外的显式附加映射。缺失诊断必须携带 Issue/change、role 与 basename。跨目录/符号链接不能替代实际文档。
4. required_docs 中每一项必须映射到实际文件。新增只读 `resolve-required-documents N --repo ...` 输出规范化语义角色列表和对应 basename（JSON）；公共 resolve-documents 保持既有 role→basename JSON 形状，但变为严格存在性检查。load_contract、audit 和 terminal 使用同一解析/校验结果，terminal 删除对原文的 awk 二次解析。
5. legacy 固定映射是历史推断，未声明的可选 spec/plan/verification 不要求凭空生成；已声明的 required_docs（语义角色或历史 basename）必须真实存在，并规范化为相同语义角色。保持 evidence-derived legacy compatibility，不新增 legacy 开关，不重命名/批改历史文件。已有缺 required_docs 的目录如出现，报明确 GAP，不猜测。
6. 文档草稿准备与交付校验分开：受限 publish-spec/publish-plan 可以解析合法声明并首次创建自己映射的目标；内部声明解析只由这个受限 writer 调用，不暴露给 audit/Loop/terminal 的 public strict 路径。沿用 open Issue、exact branch、单一 tuple、安全路径、front matter、日期与 Ticket graph 校验；多份文档逐份首次写入可行，但最后所有 strict 闸门必须拒绝尚未齐全的声明。不得用通用 skip-existence CLI 或全局 flag 逃过交付闸门。
7. completed 工具 dry-run 遇无效/缺文件合同仅产生 skip（可搜索 reason 与诊断），apply 对该 Issue 零 broker 写；JSON 解析失败或 resolver 失败同样 fail closed。这里证明的是文件存在与合同解析，不声称验证记录内容或现场动作已执行。
8. deployment_lifecycle 仍是仓库属性独立事实源：有效合同声明 verification 时，none→completed，selective→completed（未来真实部署可改 deployed），every-merge→等待已定义部署链写 deployed；不含 verification 的既有行为保持。本 Issue 不更改 manifest、不创建部署、不推断 verification=部署。

## 用户故事

- 作为文档作者，我希望漏写映射文件时立即获得具体文件诊断。
- 作为 development 项目维护者，我希望必需 verification 被保留，且不被强制添加 spec/plan。
- 作为 production 项目维护者，我希望复杂变更的 spec/plan 最低要求保持。
- 作为终态操作人员，我希望检查器与 mark-completed 对同一声明得出一致文件要求，错误合同没有写入。
- 作为历史项目维护者，我希望未声明的 legacy 可选文件不产生额外迁移义务。
- 作为合同作者，我希望 publish-spec/publish-plan 首次创建正常，但未完成合同无法进入验收或终态。

## Acceptance criteria

- [ ] AC-1 真实 SFM #142 历史 summary 原样 fixture 且 verification 缺失：resolve-documents、resolve-required-documents、check-change-documents 均非零；诊断包含 `142-architecture-lock-declaration`、verification 和真实 basename；development load_contract 同样拒绝。
- [ ] AC-2 route 之外的显式映射缺文件、required_docs 缺映射/文件、未知/空/重复/混合项、符号链接逃逸均拒绝；合法额外声明不可被 route 丢弃；production/development 最低要求原语义不回退。
- [ ] AC-3 同一合同让 checker 与 mark-completed 使用同一规范化声明；对缺失/非法合同运行 mark-completed --apply 的 mock broker 调用数为零。不得通过 fallback 原文读取制造成功。
- [ ] AC-4 合法 verification 在 none/selective/every-merge 三档的既有 completed/等待部署行为保持；legacy required_docs 中 `03-verification.md` 规范化为 verification；未声明 legacy 可选文件可缺，不生成额外文件。
- [ ] AC-5 初次 publish-spec 与 publish-plan 可按原顺序完成，保留分支/open Issue/路径/日期/graph 硬门；写完前 strict reader 红，文件齐全后绿，reader 不接受 writer 旁路参数。
- [ ] AC-6 平台 checkout audit PASS；SFM 当前 checkout 的合法新格式目录 PASS，既有历史 front matter GAP 逐项与基线相同且不回退。真实历史假绿 fixture 转红，回填后的 142 转绿。遇新无关 GAP 输出详情并升级，不批量修他人合同、不删声明求绿。
- [ ] AC-7 targeted tests、全量 runtime tests、mark-completed mock 集成测试、bash -n、ShellCheck（可用时）与 bash codex/tests/smoke.sh 真实通过；README/03 明确唯一声明源、route 最低要求、严格 resolver 和独立部署语义。

## 接口、数据与兼容性影响

既有 resolve-documents 成功 JSON 形状不变，新增失败覆盖不存在的显式映射。新增只读 resolve-required-documents 的角色/文件 JSON 为 terminal 共用事实读回；其具体字段固定为 `required_docs`（规范化角色数组）与 `documents`（角色映射）。不接受外部 URL/owner/repo/credential 参数，不改变 broker operation schema、CI context、labels taxonomy 或 dependencies schema。

## 治理文件的明确授权与 fresh run

批准本 spec 后，T01 独立**只修改治理合同说明**：README.md、03-Issue-Spec-Plan与单闸门开发流程.md 及本 Issue 文档。T01 完成后停止，本次运行不接着改 runtime；后续 fresh run 重新读取 AGENTS.md、README、03 和本 spec，才能执行 T02/T03。不修改 AGENTS.md、Agent provider、controller 的执行策略或运行期间治理指令。runtime / shell touch points 的明确授权范围见映射 plan。

## 风险与回滚约束

严格 reader 会提前暴露虚假声明，必须按真实错误处理。首次 writer 需要内部声明解析，不可误把 relaxed writer 用作交付检查。与 #286 并行更改 contract.py，各自只写拥有的 worktree；进入实现前只读确认另一 owner；合并后由本会话 fresh fetch/rebase 本 Issue 并重跑 gate。

未合并的本地变更可由本会话在 exact worktree 撤回；已合并代码通过新的人工审核 revert PR 回滚，禁止降低 required CI 或直接改 main。无 schema/数据迁移，无 installed/live apply、credential、服务或应用部署步骤。

## 非目标

不实现 #286 的依赖模型、#287/#288 其它合同缺口；不替 SFM 回填文档（#150 已另行交付）；不检查 verification 中每个断言真假；不重命名历史目录；不创建子 Issue、不跨仓写文件、不安装全局 skills/runtime、不合并或部署。

## 未决问题

无。用户在本聊天明确回复“确认”，批准前一轮提交的完整 spec/plan 与合同/启动请求；审批绑定 Issue #289、change/289-required-docs-source 与 manual policy。批准记录见 evidence/contract-approval.json；不包含最终 PR 提交、合并或部署。AC-1～AC-7 保持不变。

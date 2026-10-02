---
issue: 308
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/308
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - platform-governance
  - cross-module
  - ci-change
depends_on: []
reason: 新增覆盖八个安装面的只读功能，涉及平台治理、跨模块与 smoke CI 集成，强制 complex。
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-installed-drift-check-261002.md
  spec: spec-installed-drift-check-261002.md
  plan: plan-installed-drift-check-261002.md
  verification: verification-installed-drift-check-261002.md
override_reason: ''
pr_url:
status: approved
branch: change/308-installed-drift-check
created: 2026-10-02
updated: 2026-10-02
---

## 问题/需求总结

#304/#298 说明新增拒绝条件未安装时可能静默放行。8 个 installer 的 source guard 只在安装时执行，现有 Codex/Claude drift 与 readiness 工具没有覆盖全部安装面。

本会话真实 session `01a0fc7b-d0b3-7802-af08-555307d048a6`；fresh authoritative main 为 `5c2cd726c9aeaee9d17541d8feb049e33881bbac`。独立 worktree `/private/tmp/issue-308-installed-drift-check` 已 claim；共享 main 未写入。首次读取本 Issue 时评论为空，无批准或最终 PR；现已发布 triage brief #11977，用户随后明确回复“批准”，确认本 spec/plan 启动。用户启动批准已允许当前 spec/plan 的 Development Loop；PR 提交、合并和安装仍未授权。

## 影响范围

只读 checker、隔离 fixture 测试、smoke 静态接入、README/06 运维说明及本 Issue 语义文档。8 个 installer 原样作为映射事实源；真实安装目录只读。具体范围和验收见映射 spec/plan。

## 初步方案与建议

新增一条无凭据、无临时文件、无 sudo 的命令，逐 installer 输出 PASS/GAP、原有可读量、缺失/字节差异的 exact target；计数相等不能覆盖文件差异。先独立应用治理说明，fresh run 实现；smoke 接入再独立应用并停止，由后续 fresh run 验证。

## 风险

2026-10-02 Mac 基线已出现真实 GAP，原 AC-2「Mac 全 PASS」当前不成立：install-vm 初始映射 14 个目标不符，broker 3 个不符，architecture/release/sync 默认目标缺失。不能把这些改成 PASS、N/A 或视为已交付。checker 功能可用与所有组件已安装必须分别验证。

保留原 AC-2，作为待独立安装处置/人工裁决的验收缺口；本合同不为满足 AC 自动重装，也不申请 sudo。详细处置见 spec。反向证明仅在临时 fixture 安装面构造。未完成 AC-2 时不宣称全部验收完成、不归档。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
reason: 新增覆盖八个安装面的只读功能，涉及平台治理、跨模块与 smoke CI 集成，强制 complex。
risk_flags:
  - platform-governance
  - cross-module
  - ci-change
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
```

### 判级证据

- 逐读全部 8 个 installer、source guard、现有两个 skills drift 工具和 readiness 工具；缺少统一安装面覆盖。
- `06` 踩坑 20 给出 8 组可读量；踩坑 30 要求对缺失源码模块和拒绝条件做反向证明。
- `.out-of-scope/`、CONTEXT.md、docs/adr/ 当前不存在，没有发现已拒绝记录。
- 新增功能与平台/CI 风险使 small 路线不适用；manual 固定。

### 缺失的 acceptance criteria 或决策

合同已完整，用户于 2026-10-02 明确回复“批准”；授权绑定 exact #308/branch/spec/plan，收据见 evidence/contract-start-authorization.json。原 AC-2 保留为实际安装验收 GAP，不能在本只读合同内修复；用户可以先批准功能开发，安装处置仍独立授权。平台判级已真实读回 projected，生命周期 spec-drafting。现有 installed broker 缺少 canonical Matt triage 标签独立 typed 投影入口，未绕过；不以 ready-for-agent 推导 approved。

## T01 治理步骤完成

2026-10-02 用户启动批准已持久化，真实 approved 合同与 initial frontier T01 已校验。T01 仅补充 README/06 的八安装面只读合同，不改变当前 AGENTS、skills、installer、checker 或 smoke。映射 plan 已将 T01 标记 completed；下一 frontier 是 T02，但本轮遵守治理应用后停止边界，不实现 runtime。

后续 fresh run 重读 AGENTS/README/03/04/06 与本 Issue 合同，沿用既有启动授权执行 T02；不得重复请求启动确认。原 AC-2 仍为真实安装 GAP，PR 提交仍未授权。

## T02 实现完成

fresh run 已实现八面只读 checker。22 项针对性 fixture 全通过，bash -n/ShellCheck/diff-check 通过，source-only 八项 SOURCE PASS。code-review 两轴发现已修复并只读复审关闭。现有完整 smoke 默认 host 环境在 registry-preflight fixture FAIL，`LC_ALL=C` 重跑 PASS（978 runtime tests）；新 checker 尚未接入 smoke，阶段范围如实保留。

下一 frontier T03 仅应用 smoke 静态/fixture hook，然后停止；T04 fresh run 才完成集成与两台真实安装回读。原 AC-2 GAP 保留，没有 push、PR、merge、真实安装、sudo 或部署。

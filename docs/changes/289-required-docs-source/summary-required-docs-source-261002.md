---
issue: 289
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/289
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
reason: 修复共享 Loop 文档与终态治理闸门的假绿，属于平台治理和共享核心，强制 complex/manual
risk_flags:
  - shared-core
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
documents:
  summary: summary-required-docs-source-261002.md
  spec: spec-required-docs-source-261002.md
  plan: plan-required-docs-source-261002.md
  verification: verification-required-docs-source-261002.md
status: approved
branch: change/289-required-docs-source
pr_url:
created: 2026-10-02
updated: 2026-10-02
---

## 问题/需求总结

SFM #142 的真实历史 summary 声明 verification，但文件缺失时 resolve-documents 与 check-change-documents 仍 PASS，mark-completed dry-run 仍计划 set-completed。最新 route 已包含 verification，load_contract 会拒绝缺文件；漏检路径是 resolver/audit/terminal，各消费者应共享经验证的声明。

## 影响范围

仅本 Issue 的共享文档 resolver、audit、Loop 合同加载、受限 spec/plan publisher 和 completed 工具及其测试。治理说明明确修改 README.md 与 03 分册；不修改 AGENTS.md、部署 manifest、依赖解析或其它 Issue runtime。

## 初步方案与建议

summary.required_docs 为声明事实源，documents 为路径事实源；所有消费者共用规范化与存在性校验；route 仅定义阶段/复杂度最低要求，不能抹掉声明。首次文档 publisher 单独保留受限声明解析，不给检查器或终态增加旁路。先应用 README/03 治理说明后停止，fresh run 重读再实现。

## 风险

- 严格 resolver 会影响 spec/plan 首次写入，须以受限 writer 与独立测试保留准备流程。
- legacy inferred 可选文件不能被误判为显式必需；声明的历史必需项仍须校验。
- SFM 基线已有历史 front matter GAP，按逐项不回退比较，不将它们包装成 PASS。
- 与 #286 共享 contract.py；各自只写自己的 worktree，#289 不修改 depends_on 或 controller dependency 语义。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
reason: 修复共享 Loop 文档与终态治理闸门的假绿，属于平台治理和共享核心，强制 complex/manual
risk_flags:
  - shared-core
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
```

### 判级证据

- authoritative origin/main 基线 5c2cd726c9aeaee9d17541d8feb049e33881bbac；broker host.onboarding.check PASS；main can_push=false/can_force_push=false；required CI=CI / verify (pull_request)。
- SFM 历史 commit 516d24a9ca9638b4ac8fcba041296547c75a8198；summary SHA256 bb03c58dda71fccd923af20b1a0c45675d7f49a57e01fc36320e643462d7e446；verification 缺失。
- 历史 summary 原样 fixture：resolve-documents exit=0；check-change-documents exit=0/pass=2/gap=0；mark-completed dry-run action=set-completed。
- 同一 fixture：classification.route(development).required_docs=(summary,verification)；load_contract 拒绝 missing required contract documents。Issue 正文关于 route 不包含 verification 的描述不适用于当前基线。
- platform 当前 audit PASS；SFM 当前 audit exit=1/已有历史数字文件 front matter GAP；可解析平台 144 个/SFM 43 个 change，均无显式 documents 缺失、均含 required_docs。
- manifest aisoft-platform deployment_lifecycle=none，change_control 缺省 production；SFMDigitalBoard=development/application-deploy-selective。
- 2026-09-11 评论要求 resolver 本身拒绝缺映射文件；2026-09-15 评论记录旧调度顺序 #286→#289→#287→#288；本次新调度已明确并行派发并要求隔离写入。

### 缺失的 acceptance criteria 或决策

- 无；如后续发现缺失则回到 awaiting-triage。

### 当前交接

用户已于本聊天确认合同/启动；批准范围与文档摘要见 evidence/contract-approval.json。T01/T02/T03 已完成；targeted 14、全量 runtime 992、terminal mock、bash -n/ShellCheck、受控 host 完整 smoke 均 PASS。两轴审查无未解决发现。用户已确认唯一最终 PR 提交，policy=manual；owner 已 rebase 到含 #320 的 main 并重跑 992 tests/完整 smoke PASS。提交前 snapshot 的 PR CI 为 NOT RUN，后续结果按最终 PR exact head broker 读回；installed/live/deployment NOT RUN。classification live 已 projected；lifecycle approved。Matt canonical triage 标签的 typed writer 能力 GAP 已记录于 verification，由调度另行核对，不扩 #289。

---
issue: 327
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/327
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - platform-governance
  - agent-governance
  - shared-core
  - cross-module
  - security
  - rollback
depends_on: []
branch: change/327-broker-ff-integration
created: 2026-10-02
updated: 2026-10-02
status: approved
reason: 改变受控发布与主线整合行为并覆盖历史治理合同，涉及共享 broker、Controller、安全与回滚
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-broker-ff-integration-261002.md
  spec: spec-broker-ff-integration-261002.md
  plan: plan-broker-ff-integration-261002.md
  verification: verification-broker-ff-integration-261002.md
override_reason: ''
pr_url: ''
---

# #327 保留历史的 main 整合与 FF 发布合同

## 审阅入口与当前授权

负责人于本聊天直接回复“确认”，批准 #327 / `change/327-broker-ff-integration` / manual 合同，并仅启动 T01 独立治理应用。批准记录时间为 2026-10-02T22:28:43+08:00；不虚构消息 ID。本提交仅应用 14 个映射治理文本和四份语义文档，验证并原子提交后 STOP。T02/T03 必须后续 fresh run 重读；本轮不实施 runtime，不 push、提交 PR、写 live 标签、安装或部署。

- [完整 spec](spec-broker-ff-integration-261002.md)：行为、风险、精确文件范围、自举与 AC。
- [plan](plan-broker-ff-integration-261002.md)：T01 独立治理应用并停止 → fresh run → T02/T03；外部人工发表和安装不由 provider ticket 执行。
- [verification](verification-broker-ff-integration-261002.md)：真实基线与未执行矩阵。
- 唯一 owner：`01a0fcec-eb78-7790-a36a-daea917f43d2`；worktree：`/private/tmp/issue-327-broker-ff-integration`。
- 总调度 `01a0fc77-cef9-7442-9bf9-7f6799268198` 只调度；本 owner 不操作其他 Issue/worktree。
- 授权来源：#289 人工消息 `01a0fce2-1dd6-7010-bb55-3e2c9f1485c0`；其“好的，请通知总调度会话”仅批准独立路线准备；本轮 T01 授权另来自本聊天的直接确认，不能据此给其他聊天发送消息。

## 问题/需求总结

现行 AGENTS 要求 Controller FF、禁止 force；broker 要求 fresh main 祖先且拒绝 merge commit，却内部使用 `--force-with-lease`。已发表分支落后时，rebase 会丢弃 original remote tip 的祖先关系；保留历史的 main merge 又遭拒绝。#319 已有实际非 FF 发布审计，#289 保全原远端与本地候选。

2026-10-02 fresh main=`65268ee5f1e622c486fd9e354dd35e20a2900f91`。Mac installed broker 与该 main 的 broker.py SHA256 同为 `2c1b05977437f16b461c8db0d41a2ad6947d9df5a929bcc3eaeadd332030da7f`，不是 Mac 该模块的安装漂移。VM 当前 bytes 未通过本次 typed surface 刷新，保留 GAP。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 改变受控发布与主线整合行为并覆盖历史治理合同，涉及共享 broker、Controller、安全与回滚
risk_flags:
  - platform-governance
  - agent-governance
  - shared-core
  - cross-module
  - security
  - rollback
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
```

### 判级证据

- production / platform 仓库；强制 complex，固定 manual；routine opt-in 不可启用。
- redundancy：检索 host-access broker、Loop Controller、单 writer、06 #136 和 #298 AC-5/6；未发现保留 remote 历史并经无 force FF 的受控路径。
- prior rejection：本基线没有 `.out-of-scope/`；不推断历史上从未否决过。
- claim verification：源码三项互锁、Mac installed 字节相同、#319 事件记录支持；本次没有复现 live 写入。
- category 建议 `triage/enhancement`；state 建议 `triage/ready-for-agent`，仅表示合同准备就绪，不等于 `approved`。
- 问题已由 Issue 与派单固定；无需重新 grill 已决定的 slug、manual、禁止 force 或原 owner 权限。具体技术方案在 spec 中已由负责人确认；当前只执行独立 T01。
- fresh Issue 只有 `triage/needs-triage`，没有 type/complexity/lifecycle。此次不写 live 标签、不发布评论；只读 `--verify 327` 返回 `projection-missing`，投影是 GAP，不能声称 projected。后续按合同批准后的受控投影与读回复核。

## 影响范围与风险

精确清单见 spec §治理映射与 §runtime 映射。只修共享发布/整合边界及对应治理，保留 main 保护、required CI、exact tuple、唯一最终 PR、单 writer、每次 SHA 锚。

最小路线：owner 本地原子提交 → Controller 在合同内构造无冲突 main 整合 → broker 独立验证 provenance/tree/range → ordinary FF push。泛化 merge、历史重写、冲突自动解决、身份 fallback 均拒绝。

旧 broker 首推亦带 force-with-lease，本 Issue 首次发表必须由负责人本人 Gitea UI 将已验证文件发布到 exact change branch，并只创建一个 manual PR。UI 入口存在；实际 tree 等价、文件 mode 与新 head CI 全部 NOT RUN。Agent 不代 UI 提交，也不调用 direct Git/API 绕 broker。

## 依赖、终态与确认点

`depends_on: []`：#289/#319 为问题来源，不是本变更的硬前置。本变更也不是所有人工 PR 更新的硬前置。若 fresh main 已包含 #319，重新验收；未包含时默认 UTF-8 smoke 的失败应真实报告，不跨 Issue 修复。

合同/启动确认绑定 #327、exact branch、manual。确认后只先执行 T01 独立治理步骤并停止；后续 fresh run 重读才能做 T02/T03。最终唯一 PR 提交另有确认。两机安装各需独立 exact 版本批准，#316 旧授权不继承。

源码合并不证明 installed/live；安装 AC 未闭合时本任务保持可用、不 cleanup/归档、不报 Issue 实际完成。`Closes #327` 自动关闭的处理见 spec §完成边界。

### 缺失的 acceptance criteria 或决策

无未写明的方向性决策；方案已确认，T01 本地应用后停止。所有真实安装、首次人工发表、回滚与新行为测试尚未运行。远端 #327 ref 是否存在的独立精确读回仍为 GAP，任何未来创建/发表前必须重新查重。

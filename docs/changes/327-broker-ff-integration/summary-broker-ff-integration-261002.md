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

原 FF/自举合同已由本聊天“确认”批准，独立 T01 于 `061b0f3ec59869fe379d70b7d2f0455df4b8708a` 应用并 STOP。后续 fresh run 发现独立来源/批准证据缺口，完成只读核对与本地隔离 fixture，T02 尚未实现。

负责人先直接“按建议继续”选择 A 路线；草案 commit `ac172e515a47357d24ff268473af6bbee5c13fe1` 准备完成。随后本聊天直接“确认”，批准审阅卡绑定的 #327 / exact branch / manual / draft commit / spec+plan SHA256 具体补充合同，并仅启动 T04 独立治理应用。本提交只应用原14个映射治理文本及四角色，验证/本地原子提交后 STOP；无 runtime/config/service 或 live 权限实施。路线选择、原 T01 或其他聊天台账不替代此次直接确认。

批准版本和原始 spec/plan SHA256 已固定于外部 `t04-application-approval.json`；本次状态/证据更新不扩合同范围。T04 应用并停止后，后续 fresh run 才是 T02。后续唯一 PR、I01 安装与 I02 注册/启用各遵具体闸门。

- [完整 spec](spec-broker-ff-integration-261002.md)：行为、风险、精确文件范围、自举与 AC。
- [plan](plan-broker-ff-integration-261002.md)：T01/T04 已完成并分别停止 → 后续 fresh run → T02/T03；外部人工发表和安装不由 provider ticket 执行。
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
- 问题已由 Issue 与派单固定；无需重新 grill 已决定的 slug、manual、禁止 force 或原 owner 权限。原 FF 技术方向已由负责人确认；原 T01 已完成；本份新增可信根合同已由本聊天直接确认，T04 只应用治理后停止。
- fresh Issue 只有 `triage/needs-triage`，没有 type/complexity/lifecycle。此次不写 live 标签、不发布评论；只读 `--verify 327` 返回 `projection-missing`，投影是 GAP，不能声称 projected。后续按合同批准后的受控投影与读回复核。

## 影响范围与风险

精确清单见 spec §治理映射与 §runtime 映射。只修共享发布/整合边界及对应治理，保留 main 保护、required CI、exact tuple、唯一最终 PR、单 writer、每次 SHA 锚。

最小路线：owner 本地原子提交 → Controller 在合同内构造无冲突 main 整合 → broker 独立验证 provenance/tree/range → ordinary FF push。泛化 merge、历史重写、冲突自动解决、身份 fallback 均拒绝。

旧 broker 首推亦带 force-with-lease，本 Issue 首次发表必须由负责人本人 Gitea UI 将已验证文件发布到 exact change branch，并只创建一个 manual PR。UI 入口存在；实际 tree 等价、文件 mode 与新 head CI 全部 NOT RUN。Agent 不代 UI 提交，也不调用 direct Git/API 绕 broker。

## 依赖、终态与确认点

`depends_on: []`：#289/#319 为问题来源，不是本变更的硬前置。本变更也不是所有人工 PR 更新的硬前置。若 fresh main 已包含 #319，重新验收；未包含时默认 UTF-8 smoke 的失败应真实报告，不跨 Issue 修复。

合同/启动确认绑定 #327、exact branch、manual。T01 已独立完成；新增具体合同已确认，本次仅执行 T04 治理应用并停止，后续 fresh run 重读才能 T02/T03。最终唯一 PR 提交另有确认。两机安装各需独立 exact 版本批准，#316 旧授权不继承。

源码合并不证明 installed/live；安装 AC 未闭合时本任务保持可用、不 cleanup/归档、不报 Issue 实际完成。`Closes #327` 自动关闭的处理见 spec §完成边界。

## 可信根补充的具体审阅范围

- default-disabled 的 root verification authority；root 只运行 trusted-critical 代码，provider/verifier 以登记非 root 身份及真实 OS 隔离运行。
- protected grant 与记录绑定批准内容、scope/目的、graph、R0、每次 head/objects/verifier；broker 独立重算。OS peer 只证明 UID，不证明程序或人；caller PASS 永不登记。
- 仅新增 `git.change.begin(branch,ticket)`、`git.change.verify(branch,ticket,sha)`，没有 public merge/approve；`git.push.change(branch)` 不变。
- source 精确扩展见 spec 新表；新 config 默认关闭/空绑定，service 描述 inert，installer 不 provision/enable。
- I02 每主机 exact 注册/启动/权限/真实验收/rollback 是合并后的独立授权，非本次路线准备许可；新增 AC-9，不继承 T01/#316/泛安装许可。

### 缺失的 acceptance criteria 或决策

原方向及可信根补充具体合同均已直接确认；本地 approved 仅表示该 source 合同已批准，不能当作 live 投影或 protected grant。T04 只在本地应用治理；后续 fresh run 才能 T02。所有真实安装、首次人工发表、回滚与新行为测试尚未运行。远端 #327 ref 是否存在的独立精确读回仍为 GAP，任何未来创建/发表前必须重新查重。

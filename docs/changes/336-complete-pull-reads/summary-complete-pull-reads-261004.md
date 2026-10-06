---
issue: 336
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/336
change_type: security
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 新增完整读取证明并改变共享 broker/CLI 协议，涉及外部契约、安全与平台治理。
risk_flags:
  - external-contract
  - security
  - shared-core
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-complete-pull-reads-261004.md
  spec: spec-complete-pull-reads-261004.md
  plan: plan-complete-pull-reads-261004.md
  verification: verification-complete-pull-reads-261004.md
confidence: high
override_reason: ''
depends_on: []
status: approved
branch: change/336-complete-pull-reads
pr_url:
created: 2026-10-04
updated: 2026-10-06
---

# #336 完整读取合同

## 问题/需求总结

#333 的下一步源交付需要完整历史 PR 集合及精确 change namespace 的公开证明。当前单页读取不足以证明不存在重复源 PR；远端读取失败也不能证明分支不存在。改动涉及共享 broker、CLI 输出协议与安全闸门，独立归属 #336，按 complex/manual 处理。

2026-10-04 的“独立立案和四角色合同准备”是历史准备授权。2026-10-05 用户在总调度直接回复“按你的建议执行”，接受最小方案、独立派发及本票既有三路径合同启动与后续本地 Development Loop；本接收会话的派发指令明确本轮只完成 T01 治理固定并 STOP，T02 在后续 fresh turn 重新读取已固定合同后启动，无需重复合同/启动确认。唯一最终 PR 仍需另一次 exact #336 / branch / manual 确认；push、PR、merge、安装和现场动作均未授权。

批准来源：总调度 `01a0fc77-cef9-7442-9bf9-7f6799268198` 的直接用户决定与本会话派发指令；最小方案和派发卡保存在其 `issue-333-followup-diagnosis-261005/`。本次只投影 #336 的 `type/security`、`complexity/complex` 与 lifecycle `approved`，保留其他标签；实际读回记录在 verification。`triage/needs-triage` 的历史入口标签不替代合同批准。

## 影响范围

| 对象 | 本合同的范围 |
|---|---|
| Repository / Issue | `admin/aisoft-platform` / #336 |
| Branch | `change/336-complete-pull-reads` |
| Worktree | `/private/tmp/issue-336-complete-pull-reads` |
| 单写者 | session `01a10c82-7f6b-7093-80d5-d389a18198c0`；原 owner 实际交回后，既有 `claim-worktree --takeover` 已成功；原 claim 与接管前后证据保全，last_push=null |
| 草案基线 | `e2edb3e08194624a6647212571c6cc866298575b`，创建 worktree 时 `main` 与 `origin/main` 一致 |
| 当前实际改动 | T01 四角色治理固定；T02 已完成下列三路径实现及本地原子 commit；T03 本地验证与结果投影已推进，发布门保留 |
| T02 源实现 | `codex/runtime/aisoft_host_access/broker.py`、`codex/runtime/aisoft_host_access/cli.py`、新增 `codex/runtime/tests/test_host_access_complete_reads.py` |
| 归属边界 | #327 负责保留历史的整合/FF 发布路径；#333 保留调用方治理与现场验收 |
| Merge policy | `manual`；本平台 `routine` 固定 disabled；`IMPLEMENT_PROVIDER=none` |

## 初步方案与建议

按 [spec](spec-complete-pull-reads-261004.md) 固定读取协议、两个完整扫描、严格公开 receipt、所有大小/时间边界与失败拒绝规则。保留 typed operation 名称及调用参数；只改变明确声明的读结果语义。

现有审阅补丁 `reader-capability-source.patch` 的 SHA256 为 `11ab13f03770725e74d75fafc2de4572b484ef3480e7f6b8bae57f441f5cd2a2`。原包保留在 `/private/tmp/issue-333-pat-rotation-acceptance/T14-readiness-proposal-261004/`。T02 已核 hash/base/三路径范围后采用该补丁作为参考起点，再补严格 JSON、期限、传输/子进程有界读取及 CLI 证明校验；最终 delta 的 SHA256 为 `d98ad88dcbebd34ceacddc6f883fa42eb934a4b238b53e17600785a27b6994c0`，与旧补丁不同。其独立读取原型 217 tests 与读取/调用方组合原型 330 tests 的 PASS 均属于历史私人副本，不能替代 #336 新候选、默认 smoke、PR CI 或 installed 验收。

T01 已于独立 turn 固定治理并 STOP。2026-10-06 fresh T02 已重读合同、owner、基线与真实 Issue/main protection；runtime commit 为 `4cf6af48463238a7f019f94da56a9e5b663aa666`。本轮专项/受影响回归 237 项、全量 runtime 1156 项、固定 runtime HEAD 上的完整默认 smoke 与最终三路径恢复均 PASS；结果及调用失败日志见 verification。T03 的发布审阅卡仍为 GAP：观察到的 main 不是当前候选祖先，且未证明远端完整 branch/PR 唯一性；本票不借用 #327 未合并代码。唯一最终 PR 仍须绑定 exact Issue、branch 与 `manual` policy 单独确认。验证及未完成项见 [verification](verification-complete-pull-reads-261004.md)。

## 风险

- 两次相等的完整扫描证明观测期间稳定，不提供服务端原子 snapshot；后续 publication/merge 门必须重新读取。
- 新成功 stderr receipt 是共享 CLI 协议变更，消费方必须验证其 schema、scope、时间与 stdout hash；#333 调用方适配由其独立治理增量负责。
- 旧 source38/installed36 与缺 `credential_rotation_policy` 证据保留为历史。2026-10-05 本次公共观察为 Mac source38/installed38，manifest、broker.py、cli.py、contract.py 与当前 main source 公共 bytes 相同，字段存在；#336 原基线 manifest 与当前 main/installed bytes 不同。此项只证明所查公共字节一致，完整 provenance、权限、所有文件、VM 与现场仍未验收；不能据此宣称整包 installed PASS，也不随本票启用 rotation/dependency 权限。
- #327 技术发布能力仍须以真实交付为准。本票不写其工作区、不借用未合并代码、不使用 force/lease-force 或未合并 runtime 自举。
- 完整度或边界条件无法证明时 fail closed；超限、transport error 和契约漂移均保留失败，不通过 fallback 制造 PASS。

## AI 判级

```yaml
change_type: security
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 新增完整读取证明并改变共享 broker/CLI 协议，涉及外部契约、安全与平台治理。
risk_flags:
  - external-contract
  - security
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

- 新增完整分页、namespace 证明与公开 receipt，改变外部消费契约和共享 CLI 成功/错误输出语义。
- 涉及安全相关 fail-closed 判断与平台 broker 共享核心，符合强制 complex 规则；不是仅恢复单页输出的局部 small 修复。
- `verification` 用于保留改动前缺口、实际读取/失败拒绝与回滚证据；声明它不授予安装或部署权限。

### 缺失的 acceptance criteria 或决策

AC 与三个 runtime 路径已经固定，合同/启动批准已取得，无待重复确认的设计选择。T01 已独立 STOP；T02 已在 fresh turn 实现并作本地提交，T03 保留最终发布/CI 门。最终代码若因 fresh main 或 #327 已正式交付的等价 namespace 能力而改变，必须重新固定实际 diff 与证据；仅 main/能力事实变化不新增跨票产品依赖。本地三路径垂直切片可继续准备，真正 FF/发布/安装门各自独立，不增加或删除其他 Issue 的 live dependency。

## 2026-10-06 Mac 前置与范围投影更新

#327 / PR #346 已合并；当前 Mac 已对固定 merge `1a86a0037ee76f462eac52dc7dc08d3d3fbd2ed4` 完成完整安装、真实恢复、再安装和幂等复验，回执 `PASS_MAC_FF_INSTALL_ACCEPTANCE`，旧 installed FF qualification 缺口已解除。上述旧 source38/installed38 观察仅保留历史含义；#336 新协议仍未安装、未发布。

当前 Controller 要求 committed approved spec 声明 `git_scope`，本轮仅补充原三代码路径与四映射文档的精确机器投影，并本地提交后独立 STOP。隔离兼容预演仍为 `MERGE_CONFLICT`，实际 source/main 整合尚未执行；T03 继续 in-progress，最终候选、完整唯一性、发布确认与 PR CI 仍未完成，不声明 PR ready。

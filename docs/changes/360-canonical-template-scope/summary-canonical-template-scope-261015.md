---
issue: 360
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/360
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 修正共享Git范围授权判据并绑定canonical资源与holder，涉及安全和Controller治理
risk_flags:
  - security
  - shared-core
  - cross-module
  - agent-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-canonical-template-scope-261015.md
  spec: spec-canonical-template-scope-261015.md
  plan: plan-canonical-template-scope-261015.md
  verification: verification-canonical-template-scope-261015.md
confidence: high
override_reason: ''
depends_on: []
status: approved
branch: change/360-canonical-template-scope
pr_url:
created: 2026-10-15
updated: 2026-10-16
---

## 问题/需求总结

`admin/aisoft-platform#360` 修正共享 Git scope reader 对 canonical vendored 模板的误判。
已合并源码 `afd76bf2830ecc7ddc81dc07071ae4bbd8251fc8` 的
`GitRepository.scope()` 将所有不在本票目录内的 `docs/changes/` 路径视为另一 Issue；
`docs/changes/_template/{summary,spec,plan,verification}.md` 即使逐项列在获批 spec 的
`git_scope` 中也会被拒绝。Controller 和 broker 共用这个 reader。

用户已直接批准`ed03008a6cfbbfbf1826501ec6a482929f2d557e`的D-SCOPE360-1最小整包，
绑定本branch，并要求先完成T02后停止、fresh run重读后继续。
T02已独立治理应用并STOP；本轮fresh重读后按同一批准手动完成T03–T05，不启动自动provider/Loop。
本轮初始live Issue fresh读回为`open / needs-analysis`，后续分类与候选状态以真实回执记录。

## 影响范围

- exact tuple：`change/360-canonical-template-scope`、本目录、
  `/private/tmp/issue-360-canonical-template-scope`。
- 唯一 writer：`01a13b2a-e69a-78e2-9c6f-a00284afda90`，已正式 claim。
- fresh manifest main / 文档起点：`afd76bf2830ecc7ddc81dc07071ae4bbd8251fc8`。
- reader、Controller、broker及真实Git fixtures的精确路径见mapped spec；分发/drift复用既有机制。
- T02实际delta仅03、project-align及四文档；本轮T03–T05只增加获批的四runtime/三测试文件和本票证据。

## 初步方案与建议

D-SCOPE360-1已收敛为**精确资源授权的最小流程修复整包**：只有manifest绑定项目是合法holder、
已提交的同票映射 summary/spec 生命周期及绑定合法、精确 scope 明列目标路径时，
才允许四个 canonical 文件中相应的文件。未获批文件没有隐含授权。
holder 复用已解析的 canonical access/governance 绑定，四模板身份收在现有 shared reader 内，
不能取目标候选中的 manifest 或环境变量替身。
逐提交 delta、历史锚点、R0/R/M/H 祖先、两 parent tree、普通 FF 与 guard 全部保留。

按用户已确认的收敛边界，全历史模板内容锁延期，不再提供扩大方案选项。
该整包的实施及所列本地验证已获直接批准；T02停止已完成，本轮fresh重读后推进T03–T05。
该资源判据不证明人类批准不可伪造；仍是#327的cooperative checks。

## 2026-10-15 必要性与最小范围复核

用户要求：“aisoft平台项目是流程的管理，不会具体到某个项目的部署。”
结论：**#360 有必要修复，范围仅为平台流程判据缺陷**。现有通用对齐合同要求四份
vendored 模板，而平台自身 reader 对它们无差别拒绝；即使消费者的批准与 exact scope 完整也失败。
只补解释文档不能改变该判定，绕 guard、伪造路径或省略真实 delta 都不可取。

最小实施包为现有 shared reader 的精确资源例外、复用现有 holder/批准投影、
Controller/broker 必要接线及正负 fixtures；不创建新 policy 框架、typed operation 或授权系统。
现有两个 installer 与 drift mapping 已覆盖这些模块及 access/governance manifests，
因此本方案**移除 installer、漂移脚本及其测试源码的候选修改**；既有分发只需验证，不需另建
sync manifest 安装链。详细逐项必要性和收缩后的 exact scope 见 D-SCOPE360-1。

平台工具的后续版本分发属于共享能力交付，仍需独立安装授权；HSDB 的 PM2、数据库、服务、
环境配置和 UAT 不在本票。#358/#360 不构成 HSDB 全部业务开发的统一前置，
只约束实际依赖该能力的流程步骤；本票不替 HSDB 调度暂停其他已获批工作。

## 风险与依赖

- 平台模板原件在 `templates/docs/changes/_template/`，下游副本在 `docs/changes/_template/`；
  两者不互换，`vendors_change_templates=false` 不得凭路径获得下游例外。
- `git_history_paths` 同样必须核对 canonical 例外，不能用于漂白另一 Issue 或 add/revert 的中间 delta。
- 原main基线不含holder/policy检查；本票source候选与fixture结果不能替代CI、两机installed或HSDB adoption。
- 无启动依赖。`admin/aisoft-platform#358` 独立；`admin/HSDB#15` 是受影响消费者，
  不是本票启动前置。本票不向 `depends_on` 填外仓裸编号，不修改 #358 或 #15。
- HSDB #15 原 owner、worktree、固定 OID `82a5aba9e46a002b78e3aca9896ef9a26e4aa5cd`
  均保留；本轮未操作或 fresh 验证它们。公司试运行继续 PAUSED。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 修正共享Git范围授权判据并绑定canonical资源与holder，涉及安全和Controller治理
risk_flags:
  - security
  - shared-core
  - cross-module
  - agent-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
```

### 判级证据

Issue 标题虽为 fix，但变更涉及共享安全判据、Controller 和 broker，强制 complex；
`contract_effect=change` 描述范围判定的可观察变化，不按纯文档或局部 bugfix 降级。
manifest 将平台仓定义为 public-platform、production 默认、routine disabled，policy 固定 manual。
Matt triage 文档判定为 `bug / ready-for-human`，尚未投影 live triage 标签。
verification 是独立保留现场/归属/安装证据的义务，不代表本次部署。

### 授权与下一步

直接批准来源：HSDB 调度 2026-10-15 用户“批准调度创建两个分析会话”；仅授权独立 WT/claim、
合同分析文档、完整方案、文档检查及线性本地文档提交。批准记录和 fresh 证据位置见 verification。

用户在本会话直接批准：“批准 #360 按 ed03008a6cfbbfbf1826501ec6a482929f2d557e 的
D-SCOPE360-1 最小整包卡实施及执行所列本地验证，绑定 change/360-canonical-template-scope。
先完成 T02 并停止，fresh run 重读后继续；不含 push/PR、merge、真实安装或项目部署。”

T02已完成治理应用/文档检查/线性本地提交并STOP。本轮fresh run已重读本branch的
AGENTS、03、project-align及四份mapped docs，复核原批准、owner/HEAD与source事实，
继续T03–T05，不再重复索取整包启动批准。live分类/lifecycle投影按正式入口另作真实读回，
不得以本地approved冒充live已投影或直接启动自动provider。
最终PR仍需第二确认；merge、真实安装、HSDB采用/部署仍在各自独立边界。

本轮source及合成fixtures已实施；两轴只读审阅发现的两项合同缺口均已修复并复查。
上一收尾快照的分类投影阻断及自动审批拒绝记录保留在verification。
2026-10-16用户已直接批准仅补齐两个分类标签；正式projector执行成功，独立
`--verify 360`读回`projected`：`type/platform`、`complexity/complex`。
完整Issue读回仍为open，`needs-analysis`未变；没有其他live写入或provider启动。
T05候选准备完成，本会话停在唯一manual最终PR提交确认，等待第二确认；
不以本次分类授权推导push/PR、merge、真实安装或部署。

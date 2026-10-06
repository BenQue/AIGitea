---
issue: 344
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/344
change_type: security
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
reason: 新增固定身份CURRENT PAT清单治理合同涉及认证与安全输出边界
risk_flags:
  - external-contract
  - authentication
  - security
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-hsdb-pat-inventory-261006.md
  spec: spec-hsdb-pat-inventory-261006.md
  plan: plan-hsdb-pat-inventory-261006.md
  verification: verification-hsdb-pat-inventory-261006.md
confidence: high
override_reason: ''
depends_on:
  - 337
  - 339
status: contract-drafting
branch: change/344-hsdb-pat-inventory
pr_url:
created: 2026-10-06
updated: 2026-10-06
---

# #344 · 共享平台 CURRENT PAT 清单治理合同（HSDB T02C用例）

## 问题/需求总结

人类确认旧 manager-mutation/hsdb-agent PAT 创建、发布历史“没有记录或不确定”。#342 同UID5有界启用失败后已恢复原 flag=true，三项访问仍 HTTP_401；#343 R1 只能准备无记录恢复 proposal。需要一个目的限定的 CURRENT metadata 清单能力，取得固定两账号的当前实例后再由独立安全恢复合同决定保留/处置。

本票最终交付是**治理合同**。不以工具可执行、取得清单或HSDB恢复访问作为本票完成条件；这些分别有后继源实现、安装、read-window及恢复合同。未来 CURRENT_INVENTORY_PASS 不等于 canonical ownership 或 HSDB ACCESS_PASS。

## 唯一归属与当前授权

- Issue：#344；manual，routine disabled；owner/session `01a10ebe-7d29-73d0-9151-51fd09f71b49`。
- tuple：`change/344-hsdb-pat-inventory` / `docs/changes/344-hsdb-pat-inventory/` / `/private/tmp/issue-344-hsdb-pat-inventory`。
- fresh source main/base：`96ba8a17baad8e9854d4e8d0397d4162b8067b09`；shared primary仍为 `c9b5ef4e74592cbc68d6bdc6219568a1d51b6853`，未在其写合同。
- 本轮授权来自总调度派发的人类顺序授权，只包含只读查重、唯一立案/claim、四角色合同/证据、本地文档提交与审阅卡。完成T01立即STOP；未设置approved、未运行Loop。
- 未来G1需人批准exact治理delta并独立应用/STOP；fresh run重新读取后才可准备/执行后继runtime合同。本草稿不能自行新增运行权限。

## 影响范围与查重

fresh open Issues为#327/#333/#336/#340/#342/#343；其正文与评论均已读，无同能力owner。#333的marker读取只限smoke-test，#336尚未发布/安装且namespace只覆盖#333，#327仍open。各owner/worktree/批准均未接管。证据见[查重](evidence/deduplication.json)、[installed catalog](evidence/installed-catalog.json)。

fixed Gitea 1.26.4，UID3/aisoft-platform-manager 和 UID5/hsdb-agent，每次一个target/exact request；仅安全人类身份通道GET清单，严格metadata allowlist；不读canonical token内容/hash。Mac-only、用户路径、无sudo；输入终止、源码回退、安装恢复和现场read窗口分开。

## 前置与避免循环

`depends_on=[337,339]`，fresh均closed/completed。#342的忠实失败结果候选与#343 exact R1卡仅为证据输入；不要求它们closed或HSDB访问PASS才取得清单。#343已有`[337,339,342]`保持原样。

#342的AC-4原目标未达成，若要发表最终失败结果，须其原owner取得人对独立合同处置的决定，再走manual交付；本票不能改其AC/标签/终态。解除#342文档发表缺口与完成CURRENT清单能力是不同前置。

后续发布如受#327普通FF/首次发表策略、#336完整唯一性证明阻塞，交回原owner并保持GAP；#336的#333-only namespace不能当作本票证明。无push/PR授权，当前不进入发布路径。

## AI 判级

```yaml
change_type: security
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
reason: 新增固定身份CURRENT PAT清单治理合同涉及认证与安全输出边界
risk_flags:
  - external-contract
  - authentication
  - security
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
```

强制复杂证据：新增人类身份读取例外、外部API/分页/安全输出合同与平台治理；verification还负责记录不可重放的fresh tracker/catalog观测。实际分类投影/读回另见verification，不把判断当作已安装能力。

## 当前GAP与最小审阅决定

本次四角色合同可审。最小下一决定仅为批准本票G1的六个治理路径及T02独立应用/本地提交/STOP，或指出具体修订；不包含runtime、Git发布、安装/输入授权/read-window或凭据恢复。

非Secret现场operator UID/login、安全transport、后继Issue编号、tool source/installed pin、窗口均为null/GAP。治理规则已给出拒绝行为，不用猜值补齐。source/安装/read要各自补齐精确合同后另审；安全HTTP→TLS/身份通道若缺失，单列前置，不自行改服务或创建通道。

## 2026-10-06 人类补充的仓库归属边界

人类直接补充：“当前项目具体部署的问题，不要在 aisoft 平台创建。具体项目的推进在本项目里处理。”本票据此仅保留真实**共享平台能力**：共享manager与固定受管agent的CURRENT清单工具、版本/身份/分页/Secret剔除协议及平台治理例外；工具源规范/代码和共享用户安装合同属于`admin/aisoft-platform`。首个受控用例为UID3/UID5，允许范围仍固定两者，不借“共享”扩大为任意账户读取。

HSDB是该能力消费方。HSDB一次性现场read请求、hsdb-agent凭据/flag恢复与adoption、项目本地部署、环境/配置、迁移/备份/恢复、应用健康检查、业务修复、UAT和公司试运行均由`admin/HSDB`的对应既有聊天及独立项目合同追踪；不在AISoftPlatform新建或承接，不以平台completed取代HSDB验收。共享manager-mutation影响所有平台消费者的恢复另用平台security合同，不能与HSDB agent恢复合票。

本轮保留#344/owner/claim及原授权，既有#342/#343仅exact证据输入，不自行迁移/关闭/接管。未来若仅剩HSDB一次性现场处置而没有共享工具/协议/治理delta，停止该混入范围并交根拆分，不用平台票容纳项目推进。后继项目票号/owner/窗口均null；本轮不创建项目票，不使用未验收跨仓broker能力来投影项目状态。

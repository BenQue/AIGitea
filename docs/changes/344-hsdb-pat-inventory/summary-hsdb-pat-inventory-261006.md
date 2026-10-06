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
status: pr-open
branch: change/344-hsdb-pat-inventory
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/350
created: 2026-10-06
updated: 2026-10-06
---

# #344 · 共享平台 CURRENT PAT 清单治理合同（HSDB T02C用例）

## 问题/需求总结

人类确认旧 manager-mutation/hsdb-agent PAT 创建、发布历史“没有记录或不确定”。#342 同UID5有界启用失败后已恢复原 flag=true，三项访问仍 HTTP_401；#343 R1 只能准备无记录恢复 proposal。需要一个目的限定的 CURRENT metadata 清单能力，取得固定两账号的当前实例后再由独立安全恢复合同决定保留/处置。

本票最终交付是**治理合同**。不以工具可执行、取得清单或HSDB恢复访问作为本票完成条件；这些分别有后继源实现、安装、read-window及恢复合同。未来 CURRENT_INVENTORY_PASS 不等于 canonical ownership 或 HSDB ACCESS_PASS。

## 唯一归属与当前授权

- Issue：#344；manual，routine disabled；current owner/session `01a10ecc-1a09-78b0-8e41-2b15de72df43`。原T01 owner `01a10ebe-7d29-73d0-9151-51fd09f71b49` 已HANDOFF_STOP，正式takeover和原聊天归档已在仓外HANDOFF_ACCEPTED实证；保留原准备证据。
- tuple：`change/344-hsdb-pat-inventory` / `docs/changes/344-hsdb-pat-inventory/` / `/private/tmp/issue-344-hsdb-pat-inventory`。
- T01历史fresh source main/base：`96ba8a17baad8e9854d4e8d0397d4162b8067b09`；当时shared primary为 `c9b5ef4e74592cbc68d6bdc6219568a1d51b6853`，未在其写合同；该值仅T01历史。T03 fresh main=`11628709e659dac48f5cb66bade81f1617974546`。
- 原T01授权只包含只读查重、唯一立案/claim、四角色合同/证据、本地文档提交与审阅卡，已完成并STOP。G1已获人类exact六路径确认，实际应用、校验及原子commit `dc66b448e231edc7f8a3438fbba20152547ea101` 完成后独立STOP。T03在fresh接续中仅整理交付事实、校验唯一manual候选和已批准路径范围；不运行provider或runtime。
- G1批准绑定patch SHA256=`aceaf2622156ea30060c482f7020f187bb40b519c21f9bdb0b4586e76e8ff24b`，仓外执行回执为事实源。local `approved`仅投影已批准治理合同；live Issue仍open/spec-drafting，未改标签。后继源合同/安装/read各自另审，不因本票状态产生运行权限。

## 影响范围与查重

T01当时fresh open Issues为#327/#333/#336/#340/#342/#343；其正文与评论均已读，无同能力owner。#333的marker读取只限smoke-test，#336尚未发布/安装且namespace只覆盖#333，#327仍open。各owner/worktree/批准均未接管。证据见[查重](evidence/deduplication.json)、[installed catalog](evidence/installed-catalog.json)。

fixed Gitea 1.26.4，UID3/aisoft-platform-manager 和 UID5/hsdb-agent，每次一个target/exact request；仅安全人类身份通道GET清单，严格metadata allowlist；不读canonical token内容/hash。Mac-only、用户路径、无sudo；输入终止、源码回退、安装恢复和现场read窗口分开。

## 前置与避免循环

`depends_on=[337,339]`，fresh均closed/completed。#342的忠实失败结果候选与#343 exact R1卡仅为证据输入；不要求它们closed或HSDB访问PASS才取得清单。#343已有`[337,339,342]`保持原样。

#342的AC-4原目标未达成，若要发表最终失败结果，须其原owner取得人对独立合同处置的决定，再走manual交付；本票不能改其AC/标签/终态。解除#342文档发表缺口与完成CURRENT清单能力是不同前置。

T03实际installed read：两次全状态PR collection均165项、各内含两次完整扫描/终空页5/server total和stdout hash核验PASS，结果一致，未发现本票PR。ordinary `git.fetch.change`以#327 generic分支逻辑检查`change/344`与`change/344-*`，两次返回remote_known=true/head=null；未借#336的#333-only namespace证明。当前7项dispatch/FF source-installed bytes及wrapper qualification PASS，可使用qualified Controller本地无冲突[C,M]整合。push/PR仍待唯一最终确认，不写remote。

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

G1已完成，无需重复批准。T03校验通过后最小下一决定为绑定#344/branch/manual policy的唯一最终PR提交确认；候选卡记录实际最终HEAD/main/范围/验证。remote发表前重新fresh-read；runtime、安装、read-window与凭据恢复各自后继，不含在此确认内。

非Secret现场operator UID/login、安全transport、后继Issue编号、tool source/installed pin、窗口均为null/GAP。治理规则已给出拒绝行为，不用猜值补齐。source/安装/read要各自补齐精确合同后另审；安全HTTP→TLS/身份通道若缺失，单列前置，不自行改服务或创建通道。

## 2026-10-06 人类补充的仓库归属边界

人类直接补充：“当前项目具体部署的问题，不要在 aisoft 平台创建。具体项目的推进在本项目里处理。”本票据此仅保留真实**共享平台能力**：共享manager与固定受管agent的CURRENT清单工具、版本/身份/分页/Secret剔除协议及平台治理例外；工具源规范/代码和共享用户安装合同属于`admin/aisoft-platform`。首个受控用例为UID3/UID5，允许范围仍固定两者，不借“共享”扩大为任意账户读取。

HSDB是该能力消费方。HSDB一次性现场read请求、hsdb-agent凭据/flag恢复与adoption、项目本地部署、环境/配置、迁移/备份/恢复、应用健康检查、业务修复、UAT和公司试运行均由`admin/HSDB`的对应既有聊天及独立项目合同追踪；不在AISoftPlatform新建或承接，不以平台completed取代HSDB验收。共享manager-mutation影响所有平台消费者的恢复另用平台security合同，不能与HSDB agent恢复合票。

本轮保留#344/owner/claim及原授权，既有#342/#343仅exact证据输入，不自行迁移/关闭/接管。未来若仅剩HSDB一次性现场处置而没有共享工具/协议/治理delta，停止该混入范围并交根拆分，不用平台票容纳项目推进。后继项目票号/owner/窗口均null；本轮不创建项目票，不使用未验收跨仓broker能力来投影项目状态。

## G1/T02 六路径候选与启动边界

本次具体候选把已定义的固定UID3/UID5、GET/human auth、TLS、输出allowlist、分页与资源硬门、三类恢复及仓库归属规则写入[共享reference](../../../skill-for-codex/references/hsdb-current-pat-inventory.md)，并在`codex/skills/gitea-platform-ops/SKILL.md`增加仅该规范的读取指针。四角色只同步正式接续owner、当前筹备状态、exact路径、应用/验证/恢复/STOP计划；不改变原6AC、security/complex/add/manual或deps[337,339]。

G1启动决定只绑定spec列出的六个路径和仓外审阅卡的exact patch SHA256；不得只按方向自动扩范围。确认后独立受控步骤执行本地应用、文档/范围校验、一个原子commit并STOP。Git发布仍待唯一最终PR确认，源工具/安装/现场读取及恢复仍按各自具体合同执行，本次不新建立案或派发。

人类批准、实际应用和commit结果以仓外`G1-EXECUTED-STOP-344.json/.md`为准。T03将四角色local status投影为`approved`、补充spec exact 11路径`git_scope`，仅覆盖原T01九路径与G1六路径的并集；不新增治理行为或工具文件。`pr_url`仍空，Issue正文/状态/labels均未修改，未运行结果不预填。安全origin/operator UID/tool pin/read window继续null/GAP，12组未来runtime设计仍NOT RUN；这些不是G1文档准备的前置。既有evidence JSON继续作为原T01快照，G1不改写其历史。

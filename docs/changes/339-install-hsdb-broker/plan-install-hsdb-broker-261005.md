---
issue: 339
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/339
change_type: security
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - security
  - shared-core
  - deployment
  - rollback
  - platform-governance
depends_on:
  - 337
status: contract-drafting
branch: change/339-install-hsdb-broker
created: 2026-10-05
updated: 2026-10-05
---

# #339 安装与恢复 Plan（未 approved）

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 实际Issue合同、exact四角色映射、owner与可审执行卡 | - | done |
| T02 | 获批后两端完整安装、同pin重复执行及HSDB注册readback | T01 | pending |
| T03 | 获批真实snapshot restore、同pin再安装最终七仓与下游门交接 | T02 | pending |

本表是草案依赖图，不授权T02/T03执行。T01完成仅指准备；合同本身仍draft。下一frontier先取得实际#339/pin/scope的安装批准。
T03不注入共享runtime/账号/PAT/service故障，也不冒充事故或接管#333；restore/reinstall授权或排他/窗口不足即STOP并保留NOT RUN。

## Expected touch points

- T01：仅本目录summary/spec/plan/verification、Issue #339正文和本聊天artifact；本地branch/writer marker。
- T02：source primary clean main FF（明确获批后），Mac/gitea-ci root 25固定目标+receipt及其previous链。exact清单在spec，不操作其他installer/profile/service。
- T03：批准的window快照、固定snapshot restore、八个允许清除目标的ownership/absence清单、相同c9b5ef4e pin的已合并installer再安装与最终七仓readback。本票source代码零修改，root操作本轮未执行。

## 测试与验收映射

| AC | Ticket | 验证方式 |
|---|---|---|
| AC-1 | T01/T02 | Issue #339正文、四角色resolver/checker、owner marker；人类明确确认scope及执行方式/窗口，未签署不得替代 |
| AC-2 | T02 | installed typed git.fetch.main；HEAD=origin/main=pin、clean main；两端root过程guard/provenance |
| AC-3 | T02 | 25目标SHA256/mode/root uid-gid、receipt四摘要/source_sha/merged_main/helper null |
| AC-4 | T02 | source集合/原六仓/seal/三VM profile比较；同pin两次installer及独立readback |
| AC-5 | T02 | installed typed hsdb repo/access/onboarding，保存精确错误而不修Secret；检查无账号/profile/timer/部署动作 |
| AC-6 | T03 | window snapshots→真实restore核原六仓/HSDB unknown及原字节/mode/owner/absence/previous链→同pin再安装→最终七仓/38及26目标/receipt/识别，无故障注入 |
| AC-7 | T03 | 机读handoff将source/installed/account/restore层分开，总调度fresh确认后单独激活T02 |

## 数据库迁移

无；不访问或修改HSDB/Gitea数据库、附件或业务数据。

## 安装、失败与恢复

顺序：批准确认→fresh owner/source/helper/receipt核验→已授权source FF→即时独立snapshots→VM→Mac安装→同pin再跑→全目标/receipt/识别读回→真实window snapshot restore→原六仓/unknown/previous/absence读回→同pin再安装→最终七仓/26目标读回→交接。
主机操作只在后续fresh run和明确scope内进行；guard失效、helper/receipt变化、并发owner、pin变化即STOP。
窗口建议确认后45分钟；planned restore/reinstall/readback须在45分钟内完成，演练前保留至少30分钟，不足不开始。额外≤15分钟仅用于意外baseline恢复与读回，不授权过期再安装。不能要求人工签署者冒充执行owner，也不把sudo身份当人类授权。

没有应用部署、服务迁移或生产环境操作。两次installer、真实snapshot restore和同pin再安装闭环在verification分phase记录；目前均NOT RUN。
source回退、fixture和artifact解包不替代真实installed恢复。snapshot恢复是待明确批准的方法，previous installed source SHA继续NOT VERIFIED。

## 发布与边界

T01本地文档原子commit可复核；本轮不push/PR、不修改main。最终唯一manual文档PR另按平台确认和CI门。
已有merged installer消费无需推断新增文档先merge门；一旦main确实变化则重新审pin，不能从change/339或本artifact导出源安装。

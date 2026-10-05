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
status: approved
branch: change/339-install-hsdb-broker
created: 2026-10-05
updated: 2026-10-05
---

# #339 安装与恢复 Plan · 完整技术闭环完成

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 原及Revision2合同授权、完整差异、owner、窗口/快照准备 | - | done |
| T02 | 两端同pin首次/第二次安装、26目标/receipt/policy/HSDB非unknown核验 | T01 | done |
| T03 | 新window真实snapshot restore→baseline验收→同pin再安装→最终七仓及handoff | T02 | done |

唯一source pin c9b5ef4e74592cbc68d6bdc6219568a1d51b6853，owner/tuple不变。完整动作发生于2026-10-05T22:44:23+09:00起的新45分钟窗口；planned restore22:55:17，余量34分05.9秒，最终installed/registration读取22:55:38完成；未延长窗口。

## 已执行seam及验证

fresh owner/source/root能力/baseline/helper→独立新snapshot→VM→Mac安装→独立26目标/policy/receipt→同pinsecond no-op→独立metadata/previous/bytes不变→installed识别（HTTP401真实GAP）→Mac→VM真实snapshot tar恢复及八本候选新增目标清除→原六仓36/bytes/mode/root owner/previous/absence/unknown验收→VM→Mac同pin再安装→最终七仓38/26目标/receipt/HSDB非unknown→机读handoff。
精确命令/exitcode与before/after均在window-2证据，完整AC及冻结命令卡在spec，结果在verification。没有代码/工具变更、数据库/账号/Secret/服务/应用部署或故障注入。

## 下一frontier及边界

剩余仅最终文档/正文一致性、本地文档提交和总调度fresh T01门。HSDB HTTP401 credential/account/access GAP交T02在独立adoption合同中诊断，安装批准不代替Secret/账号或canary批准；不自行激活T02。
最终唯一manual文档PR仍未push/提交/CI，按平台既定门禁；source #337已closed，不重开或把本票installed证明冒充CI/main workflow/UAT。provider=none，#333等owner/暂停monitor不变。

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
status: awaiting-triage
branch: change/339-install-hsdb-broker
created: 2026-10-05
updated: 2026-10-05
---

# #339 安装与恢复 Plan · STOP后的下一窗口候选

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 原合同授权、执行记录、完整installed差异和修正版审阅卡 | - | done |
| T02 | 增量/新窗口获批后两端同pin首次和第二次安装、全目标/策略/识别验收 | T01 | pending |
| T03 | 新窗口真实snapshot restore→baseline验收→同pin再安装→最终七仓交接 | T02 | pending |

当前frontier：仅准备及发布Revision 2供总调度审阅；T02/T03未获新scope/窗口批准，不能重启原窗口。

## 本窗口已执行/停止

primary exact FF至c9b5ef4e74592cbc68d6bdc6219568a1d51b6853；VM/Mac首次installer exit0。独立策略核验发现sfm-digital-board/dependency_read_targets absent→[aisoft-platform]，与旧卡“原六仓声明保持”不符；停止第二次installer/识别/再安装。
Mac→VM按即时snapshots真实恢复，原字节/mode/owner/previous/absence/六仓36及HSDB unknown独立读回PASS。本窗口STOP终态，不消费剩余时间再安装；planned AC-6/最终七仓未完成。

## 下一完整窗口候选

先由总调度审阅完整逐字段差异和源字段影响，再向用户询问具体增量与新45分钟窗口。确认后fresh owner/root capability/source/pin/baseline；重新备份两端非Secret安装面并核摘要；VM→Mac安装→独立26目标/完整policy核验→同pin第二次→识别读回→余量≥30分钟时Mac→VM真实snapshot restore→原六仓36/原字节/metadata/previous/absence/unknown核验→VM→Mac同pin再安装→最终七仓38/26目标/receipt/识别→总调度fresh核T01门。
planned restore/reinstall/readback均在新45分钟内完成；≤15分钟延长只允许意外baseline恢复/读回，不授权过期再安装。能力、owner、helper/receipt/pin/baseline漂移均STOP，不能修改工具绕过或静默使用更宽身份。

## Touch points与验证

T01只四份文档、#339正文和本聊天artifact；T02只版本化root installer25目标+receipt；T03只批准的新window快照/八目标恢复清除/同pin再安装。完整目标和命令在spec/Revision2卡。
验证覆盖AC-1/2授权及pin/root guard；AC-3/4固定26目标/receipt/policy/幂等；AC-5HSDB解析与真实access GAP；AC-6全闭环；AC-7fresh交接。没有schema/数据库/账号/Secret/应用部署动作，不注入runtime/PAT/服务故障，不接管#333。

## 发布

本地可review的文档commit，仅本票branch；未push/PR。总调度读取结果，本聊天不消息回发。文档最终唯一manual PR按既有门禁，治理/runtime源码仍零改动。

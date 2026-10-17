---
issue: 362
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/362
change_type: platform
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
  - 360
status: approved
branch: change/362-mac-broker-install-acceptance
created: 2026-10-17
updated: 2026-10-17
---

# #362 运维执行计划

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | fresh正式Issue/合同/唯一claim/固定source和baseline | - | completed locally |
| T02 | P0–P6：snapshot→安装→资格→no-op→完整restore/负例→再安装/最终drift | T01 | completed: actual P0–P6 + independent acceptance PASS |
| T03 | F1/F2封闭fixture与资源清理 | T01 | completed |
| T04 | actual evidence/local candidate/最终manual提交卡 | T02, T03 | local candidate ready; awaiting manual PR submission confirmation |

## Expected touch points

本票仅 `docs/changes/362-mac-broker-install-acceptance/` 四语义文档和本票 runbook；证据在本会话artifact。
既有installer只消费source pin；target允许清单与副作用见spec/原卡。没有源码修改或新分发框架。

## 数据库迁移

无。

## 测试与验收映射

| AC | 具体验证 |
|---|---|
| AC1 | formal typed readback、claim、full SHA/hash、fresh baseline、root/窗口/interpreter |
| AC2 | 每次安装后独立27字节/owner/mode/type/link及公开metadata |
| AC3 | 本session `template_scope_context(None, "hsdb")` + canonical repo/holder + `context.verify()` |
| AC4 | 同pin installer输出no-op，安装前后完整target/previous/absence独立比较 |
| AC5 | native tar explicit manifest/headers/hash、restore逐项比对、旧资格负例、同pin再装 |
| AC6 | 原卡两个exact unittest；独占TMPDIR，清理本次证明资源 |
| AC7 | mapped verification，真实结果与NOT RUN分开；最终HEAD/claim/clean读回 |

## 部署与回滚

仅本机Mac共享工具安装，不涉及业务应用部署。本人接续步骤见 [runbook](runbook-mac-broker-install-acceptance-261017.md)。
P0先协调窗口并fresh核全部输入→native snapshot→P1安装→P2资格→P3no-op→P4完整恢复/旧资格负例→P5再装/P1P2→P6focused drift。
任何步骤失败依既有完整snapshot恢复，漂移/恢复失败STOP；snapshot不删除。
历史准备阶段：首次Agent root不可用；随后本人私密终端root核验通过，协调前主动退出3；之后全员ACK/ARMED和首次实际安装/恢复已完成。后续同会话从P0 fresh核验恢复，不需要重新批准整包。

## 当前恢复接续

首次实际snapshot/P1完成，P2辅助holder预期错误触发完整恢复PASS；只修本票辅助验收和文档。原snapshot/path/hash复用，受限 --resume-restored 重做fresh P0后完成原P1–P6。根调度明确同窗口HOLD持续；真实重试和最终新版验收尚未运行。

## 最终执行结果

本人终端修正后复用原snapshot完成P0–P6全部PASS，原owner独立当前installed/no-op/restore/资格回执比对PASS。终端阶段结束2026-10-17 05:03:13.251131 UTC；原snapshot保留，初次失败证据不覆盖。共享窗口RELEASE请求已交根调度，等待实际回执后核最终文档/分类并准备唯一manual PR候选；此前执行计划段落保留作为阶段记录。

全员RELEASE/ACK已于2026-10-17 05:08:37 UTC完成；RELEASE后完成formal pin/Issue/protection/classification只读核验。唯一剩余人类动作是manual最终文档PR发表确认，PR后required CI及人类merge另核；不再进行系统安装。

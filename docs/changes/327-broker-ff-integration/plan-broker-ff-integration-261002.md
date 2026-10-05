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
updated: 2026-10-05
status: approved
---

# #327 最小 Git 实施计划

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 历史：独立原治理应用/commit/STOP | - | completed |
| T04 | 历史：可信根合同治理应用；相关能力现已明确延期，不表示验收 | T01 | completed |
| T05 | 历史：资源/工具链合同治理应用；能力延期，旧失败保留 | T04 | completed |
| T06 | 历史：canonical main 治理同步，随后 R01 checkpoint 保留 | T05 | completed |
| T07 | 历史：固定 Python3.9 兼容治理与后续已提交四行保持 | T06 | completed |
| T08 | 历史：Mac observer/签名治理；能力延期未验收 | T07 | completed |
| T09 | 历史：Mac interpreter 绑定治理；能力延期未验收 | T08 | completed |
| T10 | 历史：七文档治理 commit f8750441 后 STOP；旧 M 未整合 | T09 | completed |
| T02 | 本轮仅收缩治理/保全/校验/commit/STOP；下一 fresh 读取、本人首次 main 整合、复用 WIP 做最小 FF/DAG/并发修复与真实回归 | T10 | in-progress |
| T03 | exact source candidate、固定 guard、首次本人普通 FF 与唯一 PR 第二确认、required CI/manual merge/可恢复收尾 | T02 | pending |

## 本轮与最短后续

本轮 exact 18 文档由 spec 列出；不混源码/config/installer/CI。verification 原 WIP 历史证据纳入文档，32 源码 WIP bytes/mode/uid/gid 保持。文档 resolver/semantic/graph、链接/范围/历史保全、staged tree/单 parent 与恢复校验真实通过后本地原子 commit 并 STOP；不新增 T11 或再问同一收缩批准。

1. 本人按 `human-first-main-integration.md` 在原 worktree 校验治理 G 与 fresh M，临时 park 32 WIP，保存不可变 stash SHA/bundle，标准 `--no-ff --no-commit` main merge；无冲突后仅本人 commit `[G,M]`。冲突 abort/保留恢复证据，不 pop/drop/reset/自动解决。无需 R02/authority/OS 能力，无远端写。
2. 下一 fresh T02 重读实际治理与新批准/Issue/source/installed，按 stash SHA 恢复和复用最小 Git 相关 WIP。main #337 的既有 config/test 变化保留；延期代码/测试以精确保全映射 park，不删除/skip 原 required 门。source 与旧 unsigned/mock/root/OS 证据分层，不用 clean checkpoint 充当修复。
3. 完成 spec 精确最小 runtime/测试/安装映射；运行真实 bare remote 正反向/两窗口竞态、owner/Controller/Git 回归、全 runtime discover、默认 smoke；shell 改动须 bash-n/ShellCheck。source guard 失败或 runtime 未到达如实写，不制造 PASS。
4. T03 形成一次可执行的本人首次发表命令，绑定 exact R0/R/M/H、fixed guard hash/argv、blob/mode/tree/恢复与唯一 PR；完成最小代码后才进入最终第二确认。本轮未批准 push/PR。确认后本人用现有 manifest-bound helper、固定 guard、exact SHA 单 ref ordinary FF；AI 只 broker 读回/准备，不代绕行。新 head/base required CI `CI / verify (pull_request)` 全绿后本人 manual merge。
5. 当前 source 范围完成后 deterministic 文档/终态/可恢复收尾；延期与 installed GAP 留档，不因 AC-9～11 等延期再建立 source-first 闭环，不抛弃保全 WIP。安装必须 source merge 后另获授权。

## AC 与验证

| AC | 阶段/检查 |
|---|---|
| AC-1 | 本轮文档/授权/owner/保全；future fresh 重读 |
| AC-2～4 | T02 实际临时 bare remote、main integration DAG/tree、ordinary FF、exact R races 与全部负向/provider deny |
| AC-5 | T02 全 runtime discover/default smoke/static，truthful marker/readback/main-advanced/no-op |
| AC-6、AC-8 | T03 本人首次 Git 发表/唯一 PR、新 head/base required CI/本人 merge/恢复；main/身份/owner 不变 |
| AC-7、AC-9～11 | DEFERRED / GAP / NOT RUN；原安装/root/closure/scratch/observer失败原样保留，不纳入当前 source PR 前置或宣称通过 |

无 schema/数据迁移、root/Secret/账号/全局安装/服务/部署或 provider 启用。source helper 映射不等于 installed；read-only transport 与 push ACL 不等于真实新 broker FF。缺实际能力给出一项标准 Git 人工操作或具体 GAP，不建设另一层执行系统。

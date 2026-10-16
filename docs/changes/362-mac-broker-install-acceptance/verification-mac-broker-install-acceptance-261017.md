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

# #362 当前执行证据（未安装）

## 基线与范围

- 安装source/full cached origin/main：`06afadfca2a950ad6ebee4b90a22e9d950bc72fa`，clean。
- 文档WT：`/private/tmp/issue-362-mac-broker-install-acceptance`；branch `change/362-mac-broker-install-acceptance`。
- 唯一session：`01a1457e-699f-7372-8b6a-7a21d613d407`；claim last_push_head=null。
- 本轮证据：`/Users/benque/.codex/visualizations/2026/10/16/01a1457e-699f-7372-8b6a-7a21d613d407/issue-362`，时间按2026-10-17 Asia/Shanghai解释，JSON at用UTC。
- 只读原卡12项receipt hash均相等；27 source与pin一致；不把原卡历史结果冒充本轮实测。

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| typed repo.read / issue.read362 / pull.read361 | PASS，正式正文hash相等，open/needs-analysis；PR361 merged/base pin | initial-fresh-typed.json；最终标签另见classification-readback.json |
| formal classification apply→独立verify / lifecycle approved→独立readback | PASS，projected，approved/type/platform/complexity/complex | classification-readback.json |
| new worktree + claim-worktree | PASS，owner为本session | claim.json（本会话artifact） |
| local-read-checks.py | PASS source/完整目标baseline无漂移；27中25同2异 | local-preflight.json |
| source guard单独只读调用 | exit0，06afadf level with origin/main，operations38 | source-guard.txt |
| sudo -n /usr/bin/id -u，sandbox | operation not permitted | root-preflight.json |
| 同一sudo命令通过原生host执行 | exit1，sudo: a password is required | root-preflight.json；并非自动审批拒绝 |
| F1/F2两个exact unittest | exit0，Ran 2 tests / OK | fixtures.json |
| fixture清理 | PASS，unittest临时Git资源自动删除；exact xcrun_db缓存metadata/hash留证后删除，独占根已rmdir | fixtures.json |
| existing focused broker drift | GAP，两个bytes-differ与rotation-source-binding；source身份PASS | focused-drift.json |
| 四角色resolver / check-change-documents | PASS，165 Changes / 2 PASS / 0 GAP | document-validation.json |
| runbook六个bash块 / helper Python语法与真实baseline | bash -n均exit0，ast.parse通过，baseline PASS；其他root分支NOT RUN | document-validation.json / manual-helper-baseline.json |
| shared工具写入窗口 | NOT OPENED；不能以本地marker声称排他 | 未进行写入 |
| snapshot / P1首次安装 / P2实际资格 | NOT RUN | root阻塞在任何系统写入前 |
| P3真实no-op / P4完整restore+旧资格负例 | NOT RUN | 同上 |
| P5再装 / P6最终安装验收 | NOT RUN | 同上 |

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC1 | PARTIAL，Issue/owner/source/baseline已核；root/窗口/root interpreter未通过 | fresh typed/local/claim/root |
| AC2 | NOT RUN | 安装未执行 |
| AC3 | NOT RUN | P2未执行，无真实资格PASS |
| AC4 | NOT RUN | 无真实重复安装/no-op |
| AC5 | NOT RUN | 无snapshot/restore/reinstall |
| AC6 | fixture PASS；外部GAP保留 | fixtures.json |
| AC7 | 当前记录PASS；完整交付仍未完成 | 本文/回执 |

## 本机工具安装与恢复责任

直接批准已覆盖整个工具运维包；原生root认证是执行条件。接续runbook绑定固定source/原installer，包含完整snapshot、no-op、restore、再装与资格；目前仅准备，不能作为已执行证据。
本人必须在执行命令的同一私密Mac终端认证和协调写入窗口。另一终端sudo -v不保证Codex -n可用，不向聊天提供密码。
本session继续负责claim、正式投影、证据独立审查和文档；本人如执行root命令，需按runbook回传非敏感receipt，实际操作者明确标注human。

## 遗留风险与未完成项

唯一已实测外部阻塞是sudo非交互认证缺口。43文件/13absence/10目录再次fresh比较为零差异，结合installer/snapshot均未运行，证明本轮未改变受管工具闭包；不宣称OS级排他或不可伪造授权。
Mac user Loop沿用原卡GAP（本轮未重读）；VM installed NOT READ，当前路径NOT REQUIRED；architecture/lock GAP未处理。
HSDB采用、live/UAT、VM、公司部署均NOT RUN；#15资源未访问，公司#32/T06 PAUSED。CI/push/PR/merge NOT RUN。
恢复root条件后先fresh source/remote/baseline/窗口核验再进入P0；若source已前进或target漂移即STOP，不改latest/reset。
最终PR候选尚未就绪，本轮不请求发表确认。

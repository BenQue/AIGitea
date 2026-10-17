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

## 初始准备与exit3历史执行结果

下表保留当时快照；最新真实安装/恢复见末节。

| Command / check | Result | Evidence |
|---|---|---|
| typed repo.read / issue.read362 / pull.read361 | PASS，正式正文hash相等，open/needs-analysis；PR361 merged/base pin | initial-fresh-typed.json；最终标签另见classification-readback.json |
| formal classification apply→独立verify / lifecycle approved→独立readback | PASS，projected，approved/type/platform/complexity/complex | classification-readback.json |
| new worktree + claim-worktree | PASS，owner为本session | claim.json（本会话artifact） |
| local-read-checks.py | PASS source/完整目标baseline无漂移；27中25同2异 | local-preflight.json |
| source guard单独只读调用 | exit0，06afadf level with origin/main，operations38 | source-guard.txt |
| sudo -n /usr/bin/id -u，sandbox | operation not permitted | root-preflight.json |
| 同一sudo命令通过原生host执行 | exit1，sudo: a password is required | root-preflight.json；并非自动审批拒绝 |
| 本人私密终端P0 root uid/interpreter/import | PASS，uid0 / Python3.14.4 / approved import paths | personal-terminal-prewrite-readback.json，原回执按hash保全 |
| 本人入口协调停点 | exit3，shared tool window not coordinated，install_attempted=false | manual-execution-receipt.json，原副本目录见上项 |
| 受限resume-prewrite入口 | 4项模拟guard校验PASS，拒绝已安装/snapshot/其他失败状态；系统命令0 | resume-prewrite-validation.json |
| F1/F2两个exact unittest | exit0，Ran 2 tests / OK | fixtures.json |
| fixture清理 | PASS，unittest临时Git资源自动删除；exact xcrun_db缓存metadata/hash留证后删除，独占根已rmdir | fixtures.json |
| existing focused broker drift | GAP，两个bytes-differ与rotation-source-binding；source身份PASS | focused-drift.json |
| 四角色resolver / check-change-documents | PASS，165 Changes / 2 PASS / 0 GAP | document-validation.json |
| runbook六个bash块 / helper Python语法与真实baseline | bash -n均exit0，ast.parse通过，baseline PASS；其他root分支NOT RUN | document-validation.json / manual-helper-baseline.json |
| shared工具写入窗口 | NOT OPENED；不能以本地marker声称排他 | 未进行写入 |
| snapshot / P1首次安装 / P2实际资格 | NOT RUN | 共享工具窗口尚未协调，未发生系统写入 |
| P3真实no-op / P4完整restore+旧资格负例 | NOT RUN | 同上 |
| P5再装 / P6最终安装验收 | NOT RUN | 同上 |

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC1 | PARTIAL，Issue/owner/source/baseline已核；本人终端root/interpreter已通过，窗口已ARMED/HOLD、首次snapshot/安装/失败恢复已执行；修正后重试待执行，Agent认证未重探测 | fresh typed/local/claim/root |
| AC2 | 首次安装后PASS；随后已恢复旧baseline，最终新版仍NOT RUN | actual manual-p1-installed.json |
| AC3 | 首次P2辅助holder断言FAIL；辅助回归GREEN，真实重试NOT RUN | p2-assertion-diagnosis.json / p2-predicate-regression.json |
| AC4 | NOT RUN | 无真实重复安装/no-op |
| AC5 | snapshot/失败完整restore/旧负例PASS；计划内no-op与同pin再装未完成 | actual snapshot / p4 / independent-restored-baseline.json |
| AC6 | fixture PASS；外部GAP保留 | fixtures.json |
| AC7 | 当前记录PASS；完整交付仍未完成 | 本文/回执 |

## 本机工具安装与恢复责任

直接批准已覆盖整个工具运维包；原生root认证是执行条件。接续runbook绑定固定source/原installer，包含完整snapshot、no-op、restore、再装与资格；修正后的接续入口尚未真实执行；首版实际安装/失败恢复见末节。
本人必须在执行命令的同一私密Mac终端认证和协调写入窗口。runbook恢复块可在失败shell已退出后独立重建所有exact变量，并从本窗口路径/归档hash回执核验后恢复。另一终端sudo -v不保证Codex -n可用，不向聊天提供密码。
本session继续负责claim、正式投影、证据独立审查和文档；本人如执行root命令，需按runbook回传非敏感receipt，实际操作者明确标注human。

## 遗留风险与未完成项

首次Agent sudo非交互认证缺口保留为历史；本人实际终端已完成root及首次snapshot/安装/完整恢复。当前停点为辅助holder错误已修、等待同snapshot受限重试；窗口全员HOLD保持。43文件/13absence/10目录owner-mode-type的独立恢复比较PASS；授权snapshot目录保留，原始失败证据完整保全。不宣称OS级排他或不可伪造授权。
Mac user Loop沿用原卡GAP（本轮未重读）；VM installed NOT READ，当前路径NOT REQUIRED；architecture/lock GAP未处理。
HSDB采用、live/UAT、VM、公司部署均NOT RUN；#15资源未访问，公司#32/T06 PAUSED。CI/push/PR/merge NOT RUN。
协调完成后在本人实际终端用受限 --resume-prewrite 保留旧回执并重做全部P0，随后先fresh source/remote/baseline/窗口核验再进入P0；若source已前进或target漂移即STOP，不改latest/reset。
最终PR候选尚未就绪，本轮不请求发表确认。

## 2026-10-17 首次真实安装、辅助验收失败和完整恢复

该节更新此前NOT RUN快照；原始历史记录不删改。真实执行者human:benque，同一私密Mac终端。
协调保持开始01:13:11 UTC；实际snapshot/工具写入开始01:39:41 UTC；两者分开。当前HOLD持续，实际整个窗口结束时间仍null。

| 本次实际步骤 | 结果 | 证据 |
|---|---|---|
| P0 snapshot native tar / root读取43成员header+bytes | PASS；保留exact archive | manual-snapshot-verified.json |
| 原既有installer | exit0，fixed pin；真实operations=39 | manual-p1-installer.txt |
| P1独立27文件+metadata/previous/owner/mode/type/link | PASS，实际JSON非空 | manual-p1-installed.json |
| P2 pure资格后的辅助断言 | FAIL，错误要求holder=False | manual-p2-qualified.json为空；用户终端trace；p2-assertion-diagnosis.json |
| 同窗口完整snapshot restore+原absent精确清理 | exit0 / PASS | manual-p4-restored.json / manual-execution-receipt.json |
| 恢复后旧资格负例 | PASS_EXPECTED_REJECTION / BROKER_SURFACE_GAP | manual-p4-old-qualified.json |
| 原owner有界独立恢复比较 | PASS，43文件/13absence/10目录owner-mode-type与写前相同；snapshot目录保留副作用独立列明 | independent-restored-baseline.json 与写前JSON相等 |
| 辅助holder断言回归 | 原exact谓词在canonical True时RED；修正后GREEN，错误holder/URL仍拒绝 | p2-predicate-regression.json / validate-restored-entry.py |
| 受限restore-resume guard / 失败恢复控制流 | 4项mock PASS，所有系统命令0，fixture根已清理 | resume-restored-validation.json |
| 新真实P1–P6重试 | NOT RUN | 等待本人新hash入口 |

固定pin的contract.py明确DEFAULT_VENDORS_CHANGE_TEMPLATES=True，HSDB未显式覆盖，因此本票辅助False预期错误。只修辅助脚本/document，不删除holder核验，不接受任意bool，不改installer/runtime/manifest/权限政策。
此前单独sourceguard调用人工传入operations38，只证明当时guard的staleness输出，不证明manifest计数；fixed source公开manifest和真实installer输出均为39。该历史输出保留并纠正解释，不能伪造成新的38计数。

Snapshot：`/usr/local/share/aisoft/backups/tools-362-20261017T013941Z/baseline.tar.gz`，SHA256 `00ea2f364a7778e49984791dce5ca5f7784a7434a705e4ab6dc6d7830abefd35`。
原始失败总回执SHA256 `ee55a851b3041b7709f9aacc238d4da377e0d22600021e796cd84a923393d66b`；全部已保存于artifact `attempt-20261017T013941Z-failed-p2/`，包括旧辅助脚本/入口/runbook及分阶段JSON。总回执P1/P2分组失败把p1记为NOT RUN，但P1实际独立JSON PASS；本节区分，原回执字节不改。

当前old-baseline；真实发生过安装和restore，不能再报系统写入0或整包完成。根调度已明确同窗口继续HOLD，不自动RELEASE。接续仅复用该snapshot，核source/owner/当前baseline/归档hash及协调状态，重做root/P0并完成原P1–P6。

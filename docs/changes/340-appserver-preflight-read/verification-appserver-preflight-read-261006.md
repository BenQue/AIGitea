---
issue: 340
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/340
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - external-contract
  - security
  - shared-core
  - platform-governance
depends_on: []
status: pending
branch: change/340-appserver-preflight-read
created: 2026-10-06
updated: 2026-10-06
---

# #340 T01 治理证据与未执行事实

## 基线与范围

- 日期：2026-10-06（Asia/Tokyo）。准备阶段曾为 AWAITING_START_CONFIRMATION；
  实际本人确认后，本轮执行止于 T01_GOVERNANCE_STOP。
- T01 前 HEAD / fresh origin/main：c9b5ef4e74592cbc68d6bdc6219568a1d51b6853。
- owner：01a10e8e-9128-7fa2-97a8-6493ee84be08，local。
- worktree：/private/tmp/issue-340-appserver-preflight-read。
- branch：change/340-appserver-preflight-read。
- 本轮仅 06、本 Issue 四份 semantic docs 及自身证据；T01 本地治理提交后 STOP，
  尚无 runtime/fixture implementation commit。
- 本记录保存 AC1–AC6 的 source/installed/live层级；不是部署报告。

## 合同准备阶段执行结果（批准前记录）

| Command / check | Result | Evidence |
|---|---|---|
| installed gitea.issue.read --number 340（sandbox） | BLOCKED | TRANSPORT_ERROR，执行路径不可达，不能推断Issue不存在 |
| 同请求 host retry + comments.read | PASS（只读） | OPEN；comments=0/[]；content_version=0；triage/needs-triage；Issue正文AC1–6 |
| installed git.fetch.main（sandbox→host同请求） | PASS（host只读） | remote=origin/project=aisoft-platform；随后origin/main完整SHA读回 |
| fresh gitea.protection.read（同请求host） | PASS（读回） | main push/force禁用；admin-only merge；CI / verify (pull_request) |
| installed gitea.pulls.read --state all | GAP（完整性） | 返回50条最新PR，#341至#245；本页无#340；不是完整namespace/full pagination证明 |
| installed git.fetch.change --branch change/340-appserver-preflight-read | BLOCKED | sandbox TRANSPORT_ERROR；host HOST_COMMAND_FAILED；不能解释为branch absent |
| 本地refs/history/docs/worktree/claim/调度台账 | PASS（本地归属） | 本地创建前无#340 tuple；root台账仅本session；创建后exactbranch与ownermarker一致 |
| git worktree add + claim-worktree | PASS（本地准备） | .git只读sandbox被阻断后，原命令host成功；未takeover；last_push_head=null |
| source/installed manifest只读投影 | PASS（限定观测） | 两者均SHA256 509bdffb34494cbf82ef016d96e519c6bc3a17034a68ea052a516121aca4a8b9；38 operations；fixed gitea-ci；无preflight |
| source/installed技能与private-access比较 | GAP（局部文档漂移） | installed issue-session-flow/private reference缺source #286 dependency说明；aisoft-platform SKILL.md一致；未安装/修改skills |
| Context7 OrbStack resolve + query / 官方docs / local CLI --help | PASS（文档读取） | /websites/orbstack_dev；https://docs.orbstack.dev/machines/commands；run/exec aliases；help未列no-start，不是现场no-autostart证明 |
| target no-autostart primitive可靠性 | GAP | 尚无可证明实现；spec强制无法证明则zero target execution/BLOCKED |
| resolve-documents / resolve-required-documents 340 | PASS（文档） | 四角色明确映射到真实 appserver-preflight-read-261006 basename；required_docs=[summary,spec,plan,verification] |
| check-change-documents --repo 本worktree | PASS（文档） | changes=157；change-documents与change-pr-url两项PASS，gap=0；不证明新接口实现 |
| Classification.from_yaml / front matter / Ticket graph 静态核对 | PASS（文档） | 两处判级一致，platform/complex/add；production四角色；五票据，first frontier=T01，均pending |
| 新文档 whitespace / scope核对 | PASS（修正后） | 初次no-index --check发现末尾多空行FAIL，已修正；四文件重验无diagnostics；tracked source diff=[] |
| source feature/runtime tests / full smoke | NOT RUN | 准备阶段未获启动批准；批准后仍留给 fresh run，本轮 T01 只验证文档 |
| final-head required CI / PR / push | NOT RUN | 无 push/唯一最终PR授权 |
| 正式Mac/gitea-ci broker/AppServer helper安装及真实restore | NOT RUN | 无独立安装授权；manifest同hash不等于整个installed面验收 |
| operator创建/组/权限/SSH/sudo/Docker socket/PG授权 | NOT RUN | 固定候选aisoft-preflight可用性未知；零grant/provision |
| AppServer内部预检/live fresh task | NOT RUN | 未调用目标；2026-10-05 running/questing/arm64仅来源交接历史，未在本轮重验 |
| target/保留对象完整before/after / #333消费现场回执 | NOT RUN | 没有本轮liveinventory，历史清理不能代替 |
| deploy/VM lifecycle/Secret/DB/service/container mutation/UAT | NOT RUN | 不在本轮批准内 |

自身证据存放本 Issue evidence/；完整开发启动卡存放本会话visualization目录。
其它owner的worktree/台账/heartbeat均只读，本轮未恢复总调度。

准备阶段新文档尚未git add；普通git diff --check不包含untracked文件。
当时对四个新文档分别执行git diff --no-index --check /dev/null <exact-file>，
以没有whitespace diagnostics为依据；no-index对新增差异本身可返回1，不能误报失败。

## T01 治理应用与本地验证（本人确认后）

批准原文、批准前四文件/确认卡 SHA256 与 exact owner/tuple 绑定见
[approval receipt](evidence/t01-approval-readback.json)；原卡保持原字节。
本轮 fresh Issue/comments/main 读回见 [fresh readback](evidence/t01-fresh-readback.json)。
Issue 仍 OPEN/content_version=0/comments=0，live 仍只有 triage/needs-triage；
本轮只记录本地 approved，没有投影 live 标签或运行 Controller。

| Command / check | Result | Evidence |
|---|---|---|
| 本人确认与批准前 hash/owner/branch/HEAD 核对 | PASS | 直接本人确认 #340/exact branch/manual；四文件与原卡 hash 全匹配；owner 与 last_push_head=null；T01 前 HEAD/origin/main 均为 c9b5ef4e74592cbc68d6bdc6219568a1d51b6853 |
| installed Issue/comments/main 同请求 sandbox→host 读回 | PASS（host只读） | sandbox TRANSPORT_ERROR 后，同 typed 请求 host 成功；Issue/comments 无漂移，main 未前进 |
| 06 新增固定应用目标只读预检治理合同 | PASS（文档应用） | 仅新增 #340 小节：接口/目标/身份/字段/限额、no-autostart fail closed、Secret/零写边界、分层证据与独立安装授权；未修改 runtime/manifest/helper |
| resolve-documents / resolve-required-documents 340 | PASS | 四角色 basename/目录/branch 对齐；required_docs=[summary,spec,plan,verification] |
| check-change-documents --repo 本worktree | PASS | changes=157、pass=2、gap=0；change-documents 与 change-pr-url 均通过；只证明文档合同 |
| Classification.from_yaml / parse_front_matter / Ticket graph | PASS | 四文件判级一致、platform/complex/add；summary/spec/plan 本地 approved，verification pending；T01 completed，其余 pending，first frontier=T02 |
| JSON evidence、tracked/untracked scope 与 whitespace | PASS | 仅 06 与本 Issue 文档/证据；git diff --check 与逐文件 no-index --check 无 diagnostics；新增差异 rc=1 不当作测试失败 |
| staged scope/whitespace、原子本地 commit 和最终 clean readback | 提交后回执记录 | 提交前再次核对 staged allowlist；完整 SHA 与最终 staged check/clean 状态记录在本会话 visualization 的 T01 提交后 STOP 回执，避免自引用 |
| runtime/fixture/full smoke、CI、push/PR、正式安装、live、权限或部署 | NOT RUN | T01 治理隔离；本轮本地 commit 后 STOP，后续源码必须 fresh run，现场层与唯一最终 PR 仍需另确认 |

静态核对脚本首次因 PyYAML 不存在报 ModuleNotFoundError，随后改用仓库现有
parse_front_matter 并通过；未安装依赖。范围脚本首次将 Git 的中文路径 quoting 当成差异，
改用 -z 分隔后通过；未修改 Git 配置。两次脚本失败均未作为 PASS 或 feature 证据。
最终文档验证命令与输出见 [T01 document checks](evidence/t01-document-checks.json)。

本轮治理回滚仅通过本 owner 的追加 revert commit；没有向 AppServer/gitea-ci 内部执行 helper，
无目标写入或主机回滚。STOP 后不得在本 implementation run 接着执行 T02。

## Fresh T02 源码切片

fresh 起点仍为原 T01 commit；owner/branch/worktree、实际 Issue/comments 与 main 漂移见
[fresh T02 readback](evidence/fresh-t02-start-readback.json)。main 仅新增 #339 文档，没有 runtime
冲突；本会话未重写 T01 历史，也未静默变更批准前 pin。

- source operation/manifest 新增固定 localwms/localwms-local-test→AppServer；原项目、身份、ACL、
  credential route 与旧操作参数不变；旧 38-operation manifest 仍可读。
- 新 CLI 严格拒绝重复/外来 flags，拒绝不回显 caller values；broker 在任何 control/credential
  访问之前拒绝未知 target、跨项目及缺/增参数。typed runner 限额读 stdout 并验证固定拒绝回执。
- control 只允许 orb list --format json，按 bytes/rows 限额解析；没有任何 target executor。
  running、running→stopped 竞态仍返回 TARGET_EXECUTION_NO_START_UNPROVEN/BLOCKED、execution=0。
- 专用测试 12 项 PASS；既有 test_host_access.py 194 项 PASS；test-host-access-broker.sh PASS，
  其 installer 只使用临时 fake root；bash -n 与 ShellCheck PASS。
- 完整 smoke 的 sandbox 首次在 fixture 127.0.0.1 bind 被拒，FAIL（执行权限）；
  相同命令 host 路径复验在进行，尚无最终 PASS。最终 T05 必须冻结源码后重跑并绑定 tested bytes。
- live classification 写入被 automatic approval review 拒绝；原因：原批准仅 source/local，
  未含 live 标签。该写入未执行、未绕路重试，lifecycle approved/Controller 为 NOT RUN。
  source/local 工作仍按原直接本人批准完成；最终 PR readiness 为 BLOCKED。

T02 完成的是安全拒绝与 source fixture 切片，不是 no-autostart primitive/目标执行可用性证明。
正式安装、权限与 live 层均 NOT RUN，无法据此解除消费者 #333 的现场前置。

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC1 | NOT RUN（实现） | 输入/namespace/typed合同已草拟；尚未实施、未有source正反测试 |
| AC2 | NOT RUN（实现/live） | 停机/竞态/no-start/只读命令限制已写合同；primitive证明GAP |
| AC3 | NOT RUN（实现） | fields/limits/Secret/trust/旧操作回归已映射fixture，尚未测试 |
| AC4 | NOT RUN（正式安装） | 必须单独merged SHA安装卡；现有manifest读取不能替代新feature安装 |
| AC5 | NOT RUN（live） | 未获installed/operator/no-autostart条件，不向AppServer发helper调用 |
| AC6 | NOT RUN（现场交接） | 准备卡可评审；现场zero-write/完整保留对象证明未取得 |

## 遗留风险与未完成项

1. 完整远端#340命名空间证据GAP：无已发现冲突；不得将HOST_COMMAND_FAILED当不存在。
   runtime实施/提交前重新核对；发现actual既有tuple/owner即STOP，不能第二写者/换slug。
2. 现有orb help无no-start参数：running前读不能证明竞态后不自启。
   默认BLOCKED，不能把fixture正向模拟替代真实execution primitive证明。
3. operator/helper可用性、Docker/PG获准访问是live条件；未经精确权限卡不provision或fallback。
   PG角色/旧归档/未知datadir不能从固定路径猜测完整性。
4. 实际本人已批准启动并授权本轮 T01 本地治理提交；本地 approved 不等于 live
   type/complexity/approved 投影，live 标签仍未修改。后续源码须 fresh run，不同轮绕过治理 STOP。
5. source PR/CI后仍须将AC4–AC6未执行事实保留，source合并不等于通道installed/live ready。
   后续唯一PR确认卡必须明确source与现场边界，不能宣称六条AC整体PASS或消费者已解阻塞。

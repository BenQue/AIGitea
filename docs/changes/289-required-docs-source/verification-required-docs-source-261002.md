---
issue: 289
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/289
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
confidence: high
risk_flags:
  - shared-core
  - platform-governance
depends_on: []
status: approved
branch: change/289-required-docs-source
created: 2026-10-02
updated: 2026-10-02
---

# #289 证据与验证记录

## 当前阶段

基线阶段（2026-10-02）：triage 与完整合同草稿准备完成，当时尚未 approved、尚未实现。基线观察的 PASS 不表示修复后验收；最终修复后 AC-1～AC-7 的执行结果见下表与 T03 收口记录。T01/T02/T03 已完成，用户已确认最终 PR 提交；提交前 snapshot 尚未 push/PR。

## 可核对基线

- 平台 authoritative main：5c2cd726c9aeaee9d17541d8feb049e33881bbac；broker git.fetch.main 返回 PASS。
- #289 Issue open；初始入口 needs-analysis，完成草稿后已投影 type/platform、complexity/complex、spec-drafting；classification --verify 289 返回 result=projected。评论无已有启动批准；gitea.pulls.read open 返回 []。
- host.onboarding.check PASS：project-agent write；protected main can_push=false、can_force_push=false；required CI=CI / verify (pull_request)；routine disabled。
- exact tuple：change/289-required-docs-source；issue-289-required-docs-source；docs/changes/289-required-docs-source；本聊天 session=01a0fc7b-dfb2-77b3-a089-2d0f73ac8554，claim-worktree created。
- manifest：aisoft-platform deployment_lifecycle=none；缺 change_control → production。SFM development/selective，与 verification 义务独立。

## 原始历史复现

真实来源：SFM 本地 Git 历史 516d24a9ca9638b4ac8fcba041296547c75a8198（来源 Issue 已指出 merge，当前只读提取）；原样 summary 在 evidence/sfm-142-summary-516d24a.txt；SHA256=bb03c58dda71fccd923af20b1a0c45675d7f49a57e01fc36320e643462d7e446。git cat-file -e <sha>:docs/changes/142-architecture-lock-declaration/verification-architecture-lock-declaration-260910.md 非零，证明历史对象内缺失。

构造仅包含原样 summary 的 /private/tmp/aisoft-289-evidence/sfm-142-missing/docs/changes/142-architecture-lock-declaration/，不改 SFM 当前 checkout；结果保存在 evidence/baseline.json。

| 真实执行 | 当前结果 | 意义 |
|---|---|---|
| PYTHONPATH=codex/runtime python3 -m aisoft_loop.cli resolve-documents 142 --repo /private/tmp/aisoft-289-evidence/sfm-142-missing | exit=0；返回含 verification 的完整映射 | 证实缺文件不报错 |
| PYTHONPATH=codex/runtime python3 -m aisoft_loop.cli check-change-documents --repo /private/tmp/aisoft-289-evidence/sfm-142-missing | exit=0；PASS 两项、gap=0 | 证实假绿 |
| 同一 summary Classification.route(change_control=development) | (summary, verification) | 纠正原 Issue 对 route 的推测 |
| 同一 fixture load_contract；合成 open/approved、type/platform、complexity/complex Issue | ContractError: missing required contract documents: verification-architecture-lock-declaration-260910.md | 当前 Loop readiness 已拒绝；audit 漏检仍真实 |
| bash codex/tools/mark-completed-issues.sh --repo /private/tmp/aisoft-289-evidence/sfm-142-missing --project sfm-digital-board 142，固定本仓 governance/access manifests | exit=0；action=set-completed；reason=deployment-not-guaranteed；applied=false | terminal dry-run 仍接受虚假声明，零 live 写入 |

fixture 的 git remote 只写本地 metadata 供项目绑定校验，没有访问远端，也没有 --apply。

## 当前 checkout 基线

- platform audit：exit=0，change-documents PASS / change-pr-url PASS。
- SFM 当前 db3c80af5ccb46b363dafe37848df15761b9b5d5：exit=1，change-documents GAP（已有历史数字目录 front matter），change-pr-url PASS；原始清单 evidence/sfm-audit-baseline.txt。该共享工作树有既有未跟踪 docs，保持未动。此结果仅该 checkout 当前状态，不冒充 authoritative remote 或全仓 PASS。
- 可解析平台 144 个/SFM 43 个 change：无显式 documents 缺文件，required_docs 均存在；历史不可解析目录按原 audit GAP 保留。不修其它 Issue 文档。

## 修复后验收

| 项目 | 状态 |
|---|---|
| AC-1～AC-7 修复后 | PASS：见 T03 收口映射 |
| targeted / 全量 runtime | PASS：14 / 992；完整 smoke 中另运行 992 项 |
| bash -n / ShellCheck / smoke | PASS：受影响三脚本；完整 smoke 以 LC_ALL=C 在受控 host 执行 |
| PR CI | NOT RUN：本提交前 snapshot；创建 PR 后按最终 exact head 另行 broker 读回 |
| installed / live runtime / deployment | NOT RUN；本次无授权 |
| 用户合同启动确认 | PASS：本聊天明确回复“确认”；摘要记录见 evidence/contract-approval.json |
| 最终 PR 提交确认 | PASS：用户“确认提交”，exact #289/branch/manual；evidence/pr-submission-confirmation.json |
| 人工 merge | NOT RUN |

## 治理执行顺序

先获得本 spec/plan 的明确确认；T01 仅治理 README/03 说明应用后停止；fresh run 重读后再实现 T02/T03。没有运行的验证不能填通过；终态工具只证明声明文件和仓库生命周期，不证明 verification 文本每项已执行。

## 投影与能力 GAP

真实执行 apply-classification-labels --apply 289 → updated；--verify 289 → projected（type=platform, complexity=complex）。lifecycle spec-drafting → PASS；未设置 approved。

Matt 类别/ready 标签未投影：尝试 gitea.issue.labels.extension.set 的 triage/bug 与 triage/ready-for-agent 均被 broker 拒绝（REQUEST_DENIED: label is canonical or retired and cannot use the project-extension writer）。源代码确认 extension writer 不接受 canonical triage，现有 lifecycle writer 只支持 delivery lifecycle，classify writer 只支持 type/complexity。本次停止这些写入，没有绕过 broker，也不以安装/扩权解决。triage 判断在本 Issue 评论与合同中保存，canonical 标签 GAP 交调度核对独立治理范围；不是 #289 代码修复内容。

## T01 独立治理步骤（2026-10-02）

用户已确认本 Issue 精确 spec/plan 与启动开发，未确认最终 PR 提交。原批准文档 SHA256 和 exact branch/manual/session 绑定见 evidence/contract-approval.json。

真实执行：

- broker gitea.issue.labels.set --number 289 --lifecycle approved → PASS，after=[approved,complexity/complex,type/platform]。
- broker live gitea.issue.read + 本地 load_contract → PASS，issue=289、branch=change/289-required-docs-source、effective_complexity=complex、acceptance_criteria_count=7。
- git diff --check → exit=0。
- check-change-documents --repo . --porcelain → change-documents PASS、change-pr-url PASS。
- 人工模型 diff review：README/03 的全部新增约束与已批准 spec 一致；声明来源、route 最低要求、严格 reader、首次 publisher、legacy 兼容、非法合同零写入、独立 deployment_lifecycle 均已覆盖。文档明确 runtime 待 T02/T03，未把新增 CLI 写成已实现。
- 本步骤未修改 runtime、shell、AGENTS.md、manifest、template、CI 或其它 Issue 文件。因此 runtime tests / bash -n / ShellCheck / smoke 仍 NOT RUN，留 T02/T03 执行。

T01 完成本地 commit 后按治理规定停止；fresh run 重新读取更新后的 AGENTS.md、README、03、spec/plan，再执行 T02。无需重复请求合同启动确认；唯一最终 PR 提交确认仍保留。

### T01 证据展示修复

首次未暂存 git diff --check 通过，但它不覆盖未跟踪的基线证据；首次 cached 检查识别 platform/sfm TSV 空诊断列的末尾 TAB，提交仍执行，故补追加修复 commit。两份 .txt 展示副本仅去掉行尾空白，原始 stdout（包含尾 TAB）及 SHA256 原样保存到 evidence/audit-baselines.json；历史 summary 原样 hash 未改。scope 检查改为 git -c core.quotepath=false 读取，避免中文文件名转义造成假失败。修复后重新执行 staged diff --check 与文档检查，不修改验证判断或 runtime。

## T02 fresh run 实现记录

本轮重新读取 AGENTS.md、README、03、spec/plan，确认 exact owner；broker fresh git.fetch.main PASS，base 仍 5c2cd726c9aeaee9d17541d8feb049e33881bbac。#286 的 owner/session 已只读核对，未写入其它 worktree。集成优先级 4 不新增 depends_on。

实现：严格公共 resolver 校验全部显式 mapping 文件与 required 声明；新增 resolve-required-documents 返回规范化角色；load_contract 使用声明结果并校验路由最低要求；development 验收来源保持 Issue；bounded publisher 首次写入内部声明 seam，不给 reader 旁路；terminal 移除 awk/find 原文重读，失败 skip 且 zero broker write。

- TDD 基线：新增 12 项测试在旧实现上得到 16 个 subtest failures（包含真实历史 summary），修复后 targeted 转绿；另补 small verification 保留回归，共 13 项。
- test_contract.py 27、test_documents.py 20、test_change_audit.py 9、test_change_control.py 14 均 PASS。
- 首次全量 runtime 990 项 PASS（90.109s）；新增最后 1 项 small verification 初跑因 fixture 字符串替换误改 requested_complexity key 而失败，已收窄到精确字段值替换；修复后的 targeted 与最终全量由 T03 记录。
- mark-completed mock tests PASS：三档生命周期中缺文档 --apply 均 skip/applied=false/zero write；合法 legacy verification 正确归一；非法 JSON/空角色 receipt 零写入。
- bash -n、ShellCheck 对三个受影响 shell 文件 PASS。首次 smoke 在 probe JSON 字面值写法触发 SC2089/SC2090 后退出，已按数组修复；重跑进行中，尚不宣称 smoke PASS。
- 真实历史 fixture：resolve-documents exit=2；resolve-required-documents exit=2；audit exit=1；terminal dry-run skip/applied=false。诊断包含 change/role/basename。
- platform audit exit=0；SFM 当前 audit exit=1；两者 stdout 与 T01 原始基线逐字相同。回填后当前 SFM #142 strict resolver exit=0。完整读回见 evidence/post-fix.json。

实际改动包括 test-project-check.sh 的 synthetic summary 增加 required_docs 字段，使旧 project-check 测试 fixture 满足真实合同；未削弱任何断言、不修改项目/模板或 CI 硬门。CLI 回归位于 test_required_documents.py（仓库不存在 test_cli.py）。

## T03 审查修复与全量验证

Standards 双轴审查硬标准 0 项；重复解析是非阻断建议，保留现有结构。Spec 初审发现 P2：documents 的 mapping/list 类型切换可静默丢弃缺文件映射。已先补回归（修复前 14 项中 2 failures），再明确拒绝 documents 列表项和非空容器重置。修复后公共 resolver、required JSON、audit/CLI，以及 terminal 三档非法合同 --apply 零写入均 PASS。两位 reviewer 增量复核均 PASS，未解决发现 0。见 evidence/review.json。

最终 runtime 全量 992 tests PASS（89.939s）；targeted 14 PASS；terminal mock PASS；三个受影响脚本 bash -n / ShellCheck PASS。classification --verify 289 实际读回 platform/complex、projected；fresh broker fetch 的 main 仍为 5c2cd726c9aeaee9d17541d8feb049e33881bbac；当前无 #289 active PR。收据见 evidence/local-validation.json。

smoke 执行记录：第一次 ShellCheck probe 写法失败已修复；第二次运行期间 HEAD 被本地提交推进，source identity gate 拒绝，不能计 PASS；第三次固定 be9664e60617abb4139db5b5ff4b34ab4342082b，通过 source identity gate 后被 sandbox 的 localhost bind PermissionError 中断。下一次保持候选固定，以同一命令在受控 host 重跑；尚不计 smoke PASS。PR CI、installed/live、部署均 NOT RUN。

## T03 收口与最终候选

固定代码提交 c4d1da1629ac518a594f8e1788e859c4ebcb50df，执行 `LC_ALL=C PYTHONDONTWRITEBYTECODE=1 bash codex/tests/smoke.sh` → exit=0，992 tests PASS（84.605s），Codex platform static smoke checks passed。完整机器收据、日志 hash、失败尝试与环境边界见 evidence/local-validation.json。

前一次受控 host smoke 在未修改的 registry 测试失败。诊断仅在 /private/tmp 副本回显本地 fixture 输出：macOS Bash 3.2.57 在 C.UTF-8 下把 `$REGISTRY（` 的中文括号解析进变量名；registry-preflight.sh 与其测试逐字等同 main 基线。使用 C locale 后原健康→停服红→恢复绿及 5xx/非法元数据/缺包体/缺配置断言均通过，再执行完整 smoke 通过。未改 registry 脚本/测试、未弱化硬门、未操作真实 registry。此前失败均保留，不算 PASS。

| AC | 最终真实结果 |
|---|---|
| AC-1 | PASS：原样历史 fixture 三 CLI 非零且诊断含 change/role/basename；缺 verification 的 load_contract 拒绝 |
| AC-2 | PASS：额外 mapping/必需映射/文件缺失、非法声明、符号链接、documents 容器覆盖旁路均拒绝；production/development/small 声明保留 |
| AC-3 | PASS：单一 required JSON；三档 invalid --apply mock 零 broker 写入；坏 JSON 无原文 fallback |
| AC-4 | PASS：none/selective/every-merge 的合法 verification 行为保持；legacy normalize/optional 兼容 |
| AC-5 | PASS：首次 spec 后 plan 正常；partial strict 红、complete 绿；保留既有 writer 硬门和无公共 skip |
| AC-6 | PASS：最终解析器重跑 platform audit exit=0；SFM exit=1 的既有 GAP stdout 与基线逐字相同；原始 142 红、当前回填 142 绿 |
| AC-7 | PASS：14 targeted、992 全量、terminal mock、三脚本 bash -n/ShellCheck、完整 smoke；README/03 合同审查 PASS |

最后提交仅更新本 Issue 的 summary/plan/verification 与证据，未修改已通过的 runtime、shell、fixture 或治理合同。最终 candidate SHA 与代码/测试相等性检查保存在本会话私有 `/private/tmp/aisoft-289-state/issues/289.json`；该文件是交互会话本地交接状态，不声称执行过 installed/VM Controller。最终文档与 diff 闸门在该提交后另行读回。

最终 PR 提交仍待绑定 Issue #289、change/289-required-docs-source、manual 的用户确认。确认后才由 canonical broker push 并创建唯一 PR，required CI 对最终 head 执行；CI 全绿后停 READY_FOR_REVIEW 等待人工合并。无 merge、安装或部署授权。canonical triage 标签 GAP 保持独立治理范围，未扩 #289。

## 最终提交授权与 owner rebase

用户明确回复“确认提交”，授权绑定 Issue #289、change/289-required-docs-source、manual；允许合同内 PR CI 修复，未授权合并、安装或部署。持久化本会话 confirm-pr → CONFIRMED，证据见 evidence/pr-submission-confirmation.json。

fresh canonical broker fetch 发现 main 已合入 #320，推进到 11c0410d3878d5449fa61796f174ba3d2dd5e59c。仅本 owner 对自己的 worktree rebase，无冲突，range-diff 六条 commit 全部相等；重新读取更新治理规则后，固定 9b89f0e617645fa6607b885b4ef9ecf88e1e81b3 完整 smoke → exit=0，992 tests PASS（98.165s），static checks PASS。onboarding PASS，main direct/force push 禁止，required context 精确为 CI / verify (pull_request)，classification projected。见 evidence/rebase-validation.json。

本追加提交仅记录上述授权/验证并更新本 Issue 文档；首次 broker push 前 fresh 核对 owner、branch、clean tree、diff 与文档审计、已测试代码树相等，再登记本次 exact SHA 并比对 pushed_head。PR 创建后严格执行 summary-only pr_url/status backfill，再验证并使用其 fresh SHA 核对第二次 push；最终 required CI 绑定 PR 最终 head，绿后停 READY_FOR_REVIEW。

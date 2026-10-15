---
issue: 360
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/360
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - security
  - shared-core
  - cross-module
  - agent-governance
depends_on: []
status: pending
branch: change/360-canonical-template-scope
created: 2026-10-15
updated: 2026-10-15
---

# #360 分析证据与未执行验收

## 基线、授权与归属

- 日期：2026-10-15，Asia/Shanghai。
- repository：`admin/aisoft-platform`；Issue #360。
- 文档起点/fresh manifest main：`afd76bf2830ecc7ddc81dc07071ae4bbd8251fc8`。
- branch：`change/360-canonical-template-scope`；WT：`/private/tmp/issue-360-canonical-template-scope`。
- owner session/thread：`01a13b2a-e69a-78e2-9c6f-a00284afda90`。
- 正式 marker：主仓 `.git/worktrees/issue-360-canonical-template-scope/aisoft-owner.json`；
  `claim-worktree` 返回 created / issue360 / exact branch/session/worktree / last_push_head=null。
- 直接批准记录：
  `/Users/benque/.codex/visualizations/2026/10/04/01a1071e-d973-71a1-99a8-da35d447d1cd/hsdb-readiness/15-platform-dependencies-analysis-handoff-261014/两票分析会话创建直接批准-261015.json`。
  用户原话“批准调度创建两个分析会话”。允许文档WT/claim、分析方案、文档检查/线性本地文档commit；
  明确排除产品/治理源码实施或产品测试、安装、目标/身份/凭据访问、push/PR/merge/deploy。
- 本轮 evidence root：
  `/Users/benque/.codex/visualizations/2026/10/14/01a13b2a-e69a-78e2-9c6f-a00284afda90/scope360/evidence/`。
  final local HEAD 与提交后检查单独写此 root 的 final-local.json，避免自引用HEAD写进自己的commit。
  该文件保留首次分析commit的收据；本次必要性补充的提交后收据另存necessity-final-local.json。

读取的治理入口：实际 `AGENTS.md`、`README.md`、03、04、`codex/global-AGENTS.md`、
`docs/agents/{issue-tracker,triage-labels,domain}.md`，实际已安装
`/Users/benque/.agents/skills/{issue-session-flow,aisoft-platform}/SKILL.md` 及 private-gitea-access/project-align。
本仓未发现独立命名 constitution/宪法 文件；不将别仓规则替换这些现行入口。

## Fresh 检查和来源边界

| Command / check | Result | Evidence / 限制 |
|---|---|---|
| typed `gitea.issue.read --number 360` | PASS | open；唯一needs-analysis；title与目标一致；evidence/issue360.json；不等于实施批准 |
| typed `gitea.issue.comments.read --number 360` | PASS | `[]`；comments360.json；没有后续评论覆盖正文 |
| typed `gitea.pulls.read --state all` | PASS | 170条返回记录；匹配 #360 head/引用/标题为0；pulls-all.json；只声明该次读回范围，不臆造未交付的分页完整性闭包 |
| typed `git.fetch.change --branch change/360-canonical-template-scope` | PASS | manifest origin；remote_known=true、remote_head=null；fetch360.json；该调用检查本票命名选择，未报告冲突 |
| typed `git.fetch.main` + local `rev-parse origin/main` | PASS | fresh main 为上述 afd76bf…；没有移动主仓 HEAD |
| 本机会话/WT/owner marker只读检查 | PASS for #360 | 50会话列表仅本会话匹配 #360；创建前无本票branch、WT、marker；#358独立writer已存在，不触碰 |
| `scan-worktrees --repo ... --porcelain` | GAP（全仓历史），本票无冲突 | #308/333/342/343/344/349旧WT缺失/不可读；#358 unpushed；不清理、不重写他票。不得写成全仓PASS |
| 创建exact WT + `claim-worktree` | PASS | 标记owner为本会话；沙箱.git只读先拒绝，随后同动作经宿主权限成功；没有takeover |
| source只读追踪 | PASS（静态分析） | scope:235–291、verify_history:195–233、Controller:1063–1119、broker:3650–3777；详见spec |
| HSDB #15原失败/历史整合 | 报告证据，未重放 | fresh Issue正文陈述；不是本轮产品测试；未访问原WT/ref/claim/业务目标 |

初始 broker 命令缺 `--operation` 返回用法错误，已按实际CLI修正；随后沙箱内同一合法只读调用
返回 `TRANSPORT_ERROR / BLOCKED_EXTERNAL`，经宿主边界重试同一 typed broker 成功。
这两类失败不是Issue/分支不存在证据，也未切换身份或直接API。
`git.fetch.change` 不等于fresh main，已另执行 `git.fetch.main` 并核对实际OID。

## 文档验证与本地提交

本节只记录文档门，不能替代产品AC。实际命令输出保存到上述 evidence root。

| Command / check | Result | Evidence |
|---|---|---|
| `resolve-documents 360 --repo <WT>` | PASS | exit0；四角色与本票真实basename完全一致；resolve-documents.json |
| `resolve-required-documents 360 --repo <WT>` | PASS | exit0；required_docs恰为summary/spec/plan/verification；resolve-required-documents.json |
| `check-change-documents --repo <WT>` | PASS | exit0；changes=164 pass=2 gap=0；check-change-documents.json |
| exact tuple/front matter / 四文档范围 / `git diff --check` | PASS（工作区检查） | exit0；scope目录与四角色一致；新增文件还需staged检查，见final-local.json |
| 线性本地文档commit、claim/head/clean复核 | 见提交后独立收据 | 仅允许四文档；本文件不自引用自己的commit；final-local.json记录实际exact HEAD/parents/clean/claim/check结果 |

首次文档检查因手写 `risk_flags` 使用了受限解析器不支持的 inline list 而失败
（`unsafe YAML scalar at line 10`）；已改为既有 block-list 语法后重跑上述三门通过。
这是文档格式修正，没有修改解析器、runtime或测试。

## 2026-10-15 调度复核补充：实施必要性与最小包

反馈直接引用用户：“请检查 #358、#360 的合同分析是否有真正实施的必要？记住aisoft平台项目是流程的管理，
不会具体到某个项目的部署。”本会话只复核#360，不代写或实施#358。
用户没有批准A/B或产品实施；当前补充继续适用原四文档范围和线性本地文档commit授权。

在本WT fresh确认原分析HEAD为`87fa88a8fde98155ae2b7eccbb27d93632883b04`、工作树clean、
branch/claim/session一致后，只读重查以下源码，没有调用产品函数或运行产品测试：

| 事实 | 结论与边界 |
|---|---|
| `GitRepository.scope:235–291`仍在paths()无差别拒绝非own的docs/changes路径 | 存在平台通用流程误分类；修复必要性成立，不依赖HSDB具体部署或新profile |
| governance parser已有`vendors_change_templates`且可解析缺省 | 可复用holder，不需新manifest schema/项目授权表 |
| CLI已有access/governance project绑定；LocalGit尚无holder上下文；broker已持有自己的contract | 必要工作是有限接线和shared reader一致性，不需新controller/policy系统 |
| 两个installer已有shared模块、runtime包和access/governance复制；drift checker已有对应mapping | A无需新增sync manifest分发；六个先前候选installer/drift相关源码路径从future scope移除 |
| sync manifest用于既有四模板版本/digest合同 | 本轮仅对照；不变成runtime放行authority，B全历史内容锁建议延期 |

源代码基线仍为已核对的`afd76bf2830ecc7ddc81dc07071ae4bbd8251fc8`；本段记录的是本地
source静态复核，不把旧远端Issue/PR读回冒充本次重新联网核验。
修订后的D-SCOPE360-1明确最小包、必要/非必要项、source/工具安装/项目部署分门；
没有执行产品/治理源码、产品测试、真实安装/目标动作、push/PR/merge/deploy。
本次实际文档检查与第二个线性文档commit以necessity-final-local.json为准，首轮证据不覆盖。

本次补充已执行`resolve-documents`、`resolve-required-documents`、`check-change-documents`及
`git diff --check`，均exit0；全仓文档结果仍为`changes=164 pass=2 gap=0`。
十个已记录source输入的SHA256与首次分析收据一致，branch/claim仍属于本会话。
检查原始输出独立保存在`evidence/necessity-261015/`；产品测试和真实安装继续NOT RUN。

## 最小整包卡收尾

用户现已同意收敛边界：“#358暂不实施当前大包，只评估通用声明与校验的最小适配；
#360整理最小流程修复方案，供我一次审阅。继续推进T05和#50，现有数据保留，公司部署继续暂停。”
本会话只整理#360；不向T05/#50或其他会话发送消息，不操作其资源。

既有卡已覆盖13条exact scope、四资源/holder/committed approved scope复用、必要接线和正负fixture计划；
本次补齐必要本地工具/独占合成fixture资源与停止保全边界，并移除仍残留的A/B待选项，
给出唯一整包批准措辞。全历史内容锁已延期、六个installer/drift源码修改继续排除。
这属于实质审阅缺项补齐，不新增第二张卡、Issue、会话、产品源码或确认性测试。

开始时HEAD为`2c0c6d72321e8bf5f4d04a44b78695282e14babb`且clean，claim仍为本会话。
本次文档检查/提交后exact HEAD与source不变证明另存`evidence/review-package-final-local.json`，
保留首轮及必要性复核收据。当前产品实施/测试/安装/发表均NOT RUN；状态为整包卡就绪，仅待实施批准。

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1–AC-5（reader/安全/历史/Controller/FF/分发fixtures） | NOT RUN | 仅静态分析和计划，未写产品实现、未执行产品或Gitfixture测试 |
| AC-6（全runtime/default smoke/shell/required CI） | NOT RUN | 本轮只可文档检查；不能拿文档PASS代替产品PASS |
| AC-7（单票/source与installed边界） | 分析归属已核对，其余NOT RUN | 单WT/正式claim；尚无PR/source merge/installed/adoption |

## 遗留风险与未完成项

- D-SCOPE360-1最小整包卡就绪，仅实施批准待审；全历史内容锁延期且不再设A/B选择。
  summary为analyzed、spec/plan为contract-drafting，
  未投影live标签，未置产品approved，未启动provider/Controller Loop。
- 产品source、unit/integration/Gitfixtures、全runtime/smoke、PR/CI、source merge：NOT RUN。
- Mac/VM installed入口现场盘点、安装/故意失败/快照恢复、用户身份/凭据、服务/真实库/迁移、
  HSDB采用/本机运行/部署/UAT：NOT RUN。本轮不得运行其余目标检查便利地获取证明。
- scope projection与owner marker不能证明不可伪造授权；#327延期能力继续GAP/NOT RUN。
- 不修改 #358、HSDB #15原资源与固定OID，不恢复已归档平台调度，不发消息给其他会话。
- 收尾状态：ANALYSIS_COMPLETE / NEEDS_HUMAN_DECISION（整包卡就绪，仅待实施批准）；边界同意不等于启动授权。

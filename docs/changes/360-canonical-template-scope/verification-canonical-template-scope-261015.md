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

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1–AC-5（reader/安全/历史/Controller/FF/分发fixtures） | NOT RUN | 仅静态分析和计划，未写产品实现、未执行产品或Gitfixture测试 |
| AC-6（全runtime/default smoke/shell/required CI） | NOT RUN | 本轮只可文档检查；不能拿文档PASS代替产品PASS |
| AC-7（单票/source与installed边界） | 分析归属已核对，其余NOT RUN | 单WT/正式claim；尚无PR/source merge/installed/adoption |

## 遗留风险与未完成项

- D-SCOPE360-1 A/B安全语义与实施批准待人裁定；summary为analyzed、spec/plan为contract-drafting，
  未投影live标签，未置产品approved，未启动provider/Controller Loop。
- 产品source、unit/integration/Gitfixtures、全runtime/smoke、PR/CI、source merge：NOT RUN。
- Mac/VM installed入口现场盘点、安装/故意失败/快照恢复、用户身份/凭据、服务/真实库/迁移、
  HSDB采用/本机运行/部署/UAT：NOT RUN。本轮不得运行其余目标检查便利地获取证明。
- scope projection与owner marker不能证明不可伪造授权；#327延期能力继续GAP/NOT RUN。
- 不修改 #358、HSDB #15原资源与固定OID，不恢复已归档平台调度，不发消息给其他会话。
- 收尾状态：ANALYSIS_COMPLETE / NEEDS_HUMAN_DECISION；需要用户一次审阅卡片、裁定并批准实施。

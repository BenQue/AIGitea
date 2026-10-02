---
issue: 317
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/317
change_type: bugfix
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - data-migration
  - external-contract
  - shared-core
  - rollback
  - security
  - platform-governance
depends_on: []
status: pending
branch: change/317-migration-rollback-guard
created: 2026-10-02
updated: 2026-10-02
---

# 当前验证与证据边界

## 基线与范围

- authoritative origin/main：`5c2cd726c9aeaee9d17541d8feb049e33881bbac`；2026-10-02 经 project=aisoft-platform broker fetch。
- Session：`01a0fc7b-9d82-75e2-975f-d407cd23e34a`；exact worktree `/private/tmp/issue-317-migration-rollback-guard` 已 claim。
- 当前合同已批准，T01 治理文档已应用；runtime 尚未实施。下节保存批准前的历史观测，不代表当前授权或标签状态。

## 批准前基线执行结果（历史）

| Command / check | Result | Evidence |
|---|---|---|
| broker gitea.issue.read #317 + comments.read | PASS | open、needs-analysis；正文记录批准1,2；评论=[] |
| broker host.onboarding.check | PASS | exact project-agent write；main 不可 push/force；admin-only merge；required CI=CI / verify (pull_request)；routine disabled |
| branch/history/docs/PR 去重 | PASS | 无 #317 既有 branch/docs/history；broker pulls.read all 的 #317 filter=[] |
| worktree add / claim | PASS | fresh authoritative main；branch tuple；真实 session owner |
| `PYTHONPATH=codex/runtime python3 docs/changes/317-migration-rollback-guard/evidence/reproduce-baseline.py` | BUG CONFIRMED | baseline-reproduction.json；3/3入口无依据旧镜像 up=1 |
| semantic analyzer normalization / document check | PASS | validate-analysis 成功；resolve-documents 精确四角色；check-change-documents changes=145 pass=2 gap=0 |
| classification plan | PASS | 从映射 summary 得到 bugfix/complex，仅计划 |
| live classification --apply | BLOCKED | 自动审批拒绝，未执行写入；理由为合同启动确认尚未取得 |
| live classification --verify | GAP | 两维 projection-missing；不伪造 projected |
| runtime 修复/新回归测试/完整 smoke | NOT RUN | 合同未批准，未修改 runtime |
| PR CI | NOT RUN | 未 push/PR |
| installed/live Docker/DB/公司现场 | NOT RUN | 未获得此范围授权 |

`reproduce-baseline.py` 只调用 repository FakeDocker 和临时 fixture，无真实 Docker subprocess。
其中 database_restore_calls=0 表示本 baseline adapter 没有 restore 调用；不代表真实 DB 验收。
该脚本绑定上列 baseline，在修复后运行当前 source 预期结论改变，不能重写本 baseline evidence。

## Acceptance criteria 结果

AC-01–10 均 NOT RUN（指修复后的合同验收）；baseline reproducer 只证明缺陷存在。正式结果将由后续批准后的 fresh runtime run 回填。

## 授权、遗留风险与未完成项

2026-09-21 平台先行方向保留；本票首次具体的 profile/evidence/state/security 合同已获2026-10-02 用户直接批准；授权证据见 evidence/contract-start-approval.json。
依赖：#317 depends_on=[]；NewEMaint #229 被本票阻塞。
需要 runtime/schema/test 实施、consumer review、最终 PR 提交确认和人工 merge；不能提供新的 merged SHA 或宣称解除 #229 前置。

## T01 独立治理合同步骤（2026-10-02）

- 用户本会话直接回复“批准”；绑定原 reviewed head `abc1adfffe6fcdc3b6053695050a5a83fd3e4830` 的 spec/plan 和 manual policy；无最终 PR、merge、install、deploy 权限。
- Fresh authoritative main 仍为 `5c2cd726c9aeaee9d17541d8feb049e33881bbac`；工作区 ownership/clean 读回正确，未修改共享 main。
- 已应用 Docker release README 与 versioned `docker-release/contracts/migration-rollback-v1.md`；README 明确当前 runtime 仍为基线，不虚报 guard 已生效。
- spec AC 表转换为现有 loader 可读的 checklist、plan 逐项 AC 映射展开，内容和验收范围保持。
- 本阶段只运行文档/纯合同检查；未启动 Controller，未实施 runtime/schema/test，也未运行 Docker/DB。

| Check | Result | Evidence |
|---|---|---|
| 合同启动授权 | PASS | direct user “批准”；contract-start-approval.json |
| 仅 #317 classification --apply | PASS | bugfix/complex updated |
| 独立 classification --verify | PASS | 两维 result=projected |
| approved lifecycle 投影 | PASS | before needs-analysis → after approved；保留 type/complexity |
| pure load_contract + frontier | PASS | CONTRACT_VALID；criteria_count=10；frontier=T01 |
| 文档与 pr_url 检查 | PASS | changes=145 pass=2 gap=0 |
| Matt triage/category 状态投影 | GAP | 当前 broker 无 triage typed write；extension 明确禁止 managed prefix，未绕过 |
| T01 Standards / Spec 独立 review | NOT RUN | 本地提交后执行并回填 |
| runtime、release suite、smoke、CI、installed/live | NOT RUN | T01 文档步骤，本阶段不宣称功能通过 |

T01 完成后停止。下一条 fresh run 重读当前 AGENTS/README、已批准 spec/plan、新治理合同和 claim，再沿用已有批准实施 T02/T03；不额外申请合同启动批准。

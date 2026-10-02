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
- 当前内容为合同草案及改动前证据；未批准/应用新的 release 治理合同，未实施 runtime。

## 执行结果

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

2026-09-21 平台先行方向保留；本票首次具体的 profile/evidence/state/security 合同待确认。
依赖：#317 depends_on=[]；NewEMaint #229 被本票阻塞。
需要 runtime/schema/test 实施、consumer review、classification 读回、最终 PR 提交确认和人工 merge；不能提供新的 merged SHA 或宣称解除 #229 前置。

---
issue: 237
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/237
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - platform-governance
  - ci-guard
depends_on:
  - 233
status: approved
branch: change/237-deproject-company-delivery
created: 2026-09-03
updated: 2026-09-03
---

# Implementation plan · 去项目化收尾

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 基线观测入 verification（grep 计数、smoke 基线、链接检查基线）+ `archive/company-delivery-pilot-历史-20260903.md` 与索引行（P-12/P-13，逐字收录待迁出段落） | - | pending |
| T02 | `company-delivery/` 通用文件去项目名（D-01、D-05、D-06～D-08 `$comment`）+ `test_company_delivery.py:2926` 字面量同步；`smoke.sh` 全绿 | T01 | pending |
| T03 | `07` §5.1 与 `company-delivery/` 引用句（P-01～P-06）、`README.md`（P-07～P-10）改写；链接检查 `broken=0` | T01 | pending |
| T04 | NewEmaint 仓承接 Issue（broker `gitea.issue.create`）；编号回填 archive 文件与 verification | T02, T03 | pending |
| T05 | `smoke.sh` 新增 `company-delivery/README.md`+`runbook.md` 项目名守卫 + 反向证明；verification 定稿；判级投影 | T04 | pending |

Ticket ID 固定为 `Txx`；依赖只引用本表中的 ID。每个 ticket 都应可由 `$implement #N Txx` 独立执行和验证。
T02 与 T03 互不依赖，可并行；T05 的守卫必须在 T02 把 Markdown 计数清零之后加入，否则守卫自身报红。

## Expected touch points

- T01：`archive/company-delivery-pilot-历史-20260903.md`（新建）、`archive/README.md`、
  `docs/changes/237-deproject-company-delivery/verification-*.md`（基线节）。
- T02：`company-delivery/README.md`、`company-delivery/runbook.md`、`company-delivery/schema/inventory-v{1,2,3}.schema.json`、
  `codex/runtime/tests/test_company_delivery.py`（第 2926 行附近一条字面量）。
- T03：`07-内网与生产平移路线.md`、`README.md`。
- T04：无平台文件改动之外的写操作——NewEmaint 仓 Issue（broker）；`archive/company-delivery-pilot-历史-20260903.md`
  与 verification 回填编号。
- T05：`codex/tests/smoke.sh`（新增守卫块，紧接 #233 G-01 references 守卫之后）、verification、summary 状态。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | `grep -n '新项目默认' 07-*.md`（空）；`grep -c '平台不设默认' 07-*.md` = 1；`git diff -U0 origin/main...HEAD -- 07-*.md` 显示 §5.1 bullets 无 diff |
| AC-2 | `find company-delivery -type f \| wc -l` = 19 与判定表逐行对照；`grep -rci NewEmaint company-delivery/`（README/runbook = 0，合计 9）；`for f in company-delivery/schema/inventory-v*.json; do jq -r '."$comment"' $f; done` 每个含「历史证据」 |
| AC-3 | broker `gitea.issue.read --project newemaint --number <N>` 读回标题与正文；`git diff --stat origin/main...HEAD` 只含平台仓路径；`grep -c '原路径' archive/company-delivery-pilot-历史-20260903.md` ≥ 1；`git diff origin/main...HEAD -- archive/README.md \| grep -c '^+|'` = 1 |
| AC-4 | 守卫反向证明（临时副本 + `ROOT=<临时目录>` 单独执行守卫块，rc=1；真实树 rc=0）；`bash codex/tests/smoke.sh` rc=0；`git diff --stat origin/main...HEAD -- codex/tests/test-company-delivery-real-release-harness.sh codex/tests/integration codex/runtime/aisoft_company_delivery` 为空；`git diff origin/main...HEAD -- codex/runtime/tests/test_company_delivery.py` 只含 `:2926` 字面量与 `CompanyDeliveryTopologyDocsTests` 一个方法；integration `--execute` NOT RUN |
| AC-5 | 链接检查脚本（沿用 #233 AC-3 的 `check-md-links.sh` 逻辑）对 `README.md 07-*.md 12-*.md 13-*.md company-delivery/*.md archive/README.md` 报 `broken=0`（install-time 3 条除外）；`grep -n 'NewEmaint 公司交付 runbook\|NewEmaint 两台公司 VM 人工' README.md 07-*.md` 为空 |
| AC-6 | `git diff --stat origin/main...HEAD -- docker-release/ architecture/ codex/runtime/aisoft_company_delivery codex/runtime/aisoft_loop codex/config codex/tools templates AGENTS.md skill-for-codex skill-for-claude codex/skills 12-*.md 13-*.md` 为空 |

## 部署与回滚

无部署影响。回滚 = revert 唯一 PR；承接 Issue / 衍生 Issue 作为普通 Issue 关闭。

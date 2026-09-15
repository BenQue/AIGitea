---
issue: 292
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/292
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - security
  - platform-governance
  - shared-core
depends_on: []
status: spec-drafting
branch: change/292-github-main-relay
created: 2026-09-11
updated: 2026-09-15
---

# 实施计划（已被原生 Push Mirror 取代）

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 独立合同步骤：本票四份映射文档与范围对齐，无runtime修改 | - | completed |
| T02 | typed main relay plan/reconcile/status、绑定与协商OID门、确定性测试 | T01 | stopped |
| T03 | 版本化安装与项目调度、脱敏receipt及失败关闭回归 | T02 | stopped |
| T04 | 完整回归与最终PR材料；提交/合并等待独立人工门 | T03 | stopped |
| T05 | exact merged install、必要用户认证、两次live执行及调度验收 | T04 | stopped |
| T06 | 收口：四份映射文档改写为原生 Push Mirror 路线，唯一最终 PR 人工合并后关闭 #292 | T01 | in-progress |

`stopped` 表示该 ticket 因 2026-09-12 用户裁决被取代，不再执行、不再作为任何后续工作的前置；
它不是 `completed`，其交付物不存在。

## 现行执行路径（T06）

1. 修订 summary/spec/plan/verification 四份文档：写明取代关系、现行 M-1 至 M-6 边界、旧 T02–T05 停止、
   镜像启用/同步与公司导入全部 NOT RUN。
2. 本地验证：`bash codex/tests/smoke.sh`、`check-change-documents`、`git diff --check`。
3. 判级投影读回：`codex/tools/apply-classification-labels.sh --verify 292`；已 projected 则不动。
4. 人确认后 broker `git.push.change` 与 `gitea.pull.create --issue 292`（policy manual，正文 `Closes #292`），
   `backfill-pr-url` 回填 summary。
5. 人合并后按收尾流程执行终态标签、文档自查、worktree 与本地分支清理。

## Expected touch points（现行）

T06 只触及 `docs/changes/292-github-main-relay/{summary,spec,plan,verification}-github-main-relay-260911.md`。
不修改 `sync/`、`codex/runtime/`、`codex/config/`、`codex/tools/`、installer、`AGENTS.md`、`README.md` 或 07。

镜像本身的配置（M-2）、首次同步读回（M-3）与后续自动同步（M-4）由用户在 Gitea 界面手工完成，
证据记录在 NewEMaint #80，不在本仓库任何文件中。

## 数据库迁移

无。

## 测试与验收映射（现行）

| 验收项 | Verification command or review |
|---|---|
| 四份文档如实反映取代关系 | PR diff review |
| 文档合同可解析、pr_url 规则满足 | `PYTHONPATH=codex/runtime python3 -m aisoft_loop.cli check-change-documents --repo <checkout>` |
| 仓库其它部分无变化 | `git diff --stat origin/main...HEAD` 只列四份文档；`bash codex/tests/smoke.sh` |
| M-2 至 M-5 | 不由本票验证；NOT RUN，归 NewEMaint #80 |

## 部署与回滚

本票不部署任何东西。回滚方式是 revert 本次文档 commit；镜像的停用（M-6）由用户在 Gitea 界面操作，
只停止未来同步，不回退任何 GitHub ref。

---

## 历史 touch points（T02–T05，已停止）

T02：codex/runtime/aisoft_host_access/{broker,contract,cli}.py，新增github_relay.py及固定pre-push验证入口，codex/config/host-access-broker.json，relay binding schema，codex/runtime/tests/test_host_access.py及新增test_github_relay.py。

T03：codex/install-host-access-broker.sh及其测试、versioned macOS launchd模板/installer与tests、source-guard inventory、README与06相关小节。

T04：范围内smoke/回归与文档验证修复。

T05：merged exact source实际安装与绑定/项目调度，凭据由人本地输入。

以上均未开始，分支上没有对应文件改动。

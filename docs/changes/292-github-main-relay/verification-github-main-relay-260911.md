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

# 验证记录（收口：被原生 Push Mirror 取代）

## 基线与范围

- Commit SHA：本次收口提交在分支 `change/292-github-main-relay` 上，父提交 f1f3d79（T01 最后一个合同 commit）。
- 基线：`origin/main` = a2f8854b69a3b6badeb11fee6fd95a3500083379（分支已位于其上，无需 rebase）。
- 环境：Mac 开发机本地 worktree `/private/tmp/issue-292-github-main-relay`。
- 本记录负责证明：四份映射文档如实反映取代关系；仓库其它部分无变化；镜像与公司侧各项如实记为 NOT RUN。

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| `command -v rg` | PASS | `/opt/homebrew/bin/rg`（真实 rg，无需 shim） |
| `bash codex/tests/smoke.sh` | PASS | 2026-09-15 本地执行：`Ran 890 tests in 65.394s` / `OK` / `Codex platform static smoke checks passed.` |
| `PYTHONPATH=codex/runtime python3 -m aisoft_loop.cli check-change-documents --repo /private/tmp/issue-292-github-main-relay` | PASS | `PASS: change-documents` / `PASS: change-pr-url` / `result: changes=133 pass=2 gap=0` |
| `git diff --check` | PASS | rc=0，无空白问题 |
| `git diff --stat origin/main...HEAD` 只含四份映射文档 | PASS | 暂存区 4 files changed，均在 `docs/changes/292-github-main-relay/` |
| `codex/tools/apply-classification-labels.sh --verify 292` | PASS | `result: projected`，`change_type: platform`，`complexity: complex`，未执行 `--apply` |

## 现行路线各项状态

| 项 | 结论 | 证据 |
|---|---|---|
| M-1 唯一源与目标核对 | 已确认 | 用户 2026-09-12 裁决，见 #292 正文与 NewEMaint #80 顶部「当前路线」 |
| M-2 手工配置原生 Push Mirror | NOT RUN | 由用户在 Gitea 界面完成，本票不执行 |
| M-3 首次同步与两端 main SHA 读回 | NOT RUN | 无读回证据 |
| M-4 后续自动同步读回 | NOT RUN | 无读回证据 |
| M-5 公司入站/PR/CI/部署 | NOT RUN | 归公司流程与 NewEMaint #80 |
| M-6 停用镜像边界 | 边界声明 | 未发生停用 |

## 历史路线（已停止）

- T01 三个合同 commit（6bf75cf、a18294a、f1f3d79）保留在分支历史。
- T02–T05：自研 relay 代码、测试、installer、scheduler 均未在本分支落盘；2026-09-12 记录的「保留未提交代码」
  所在原 worktree 目录已于 2026-09-15 前丢失，未提交的修订随之不可恢复，本次文档按 #292 与 #80 正文重写。
- 2026-09-11 观测「本机源比 GitHub 领先 237 提交、镜像未配置」是历史观测，不是本轮读回。

## 遗留风险与未完成项

- 镜像启用、同步读回与公司导入全部 NOT RUN；本票关闭不代表任何同步已发生。
- 若将来需要 fast-forward-only 出站语义，另开 Issue；本票分支合并后删除，不复用。
- 本仓库没有任何文件记录镜像凭据或私有端点。

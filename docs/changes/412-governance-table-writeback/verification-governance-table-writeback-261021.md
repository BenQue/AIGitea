---
issue: 412
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/412
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - agent-governance
  - platform-governance
depends_on: []
status: pending
branch: change/412-governance-table-writeback
created: 2026-10-21
updated: 2026-10-21
---

# 治理表回写验证记录

## 基线与范围

- Commit SHA: 待填写
- 基线：`origin/main` = `1db191ebf83f7393baa4001d9e85d40ad7f93b40`（broker `git.fetch.main` 后读回）
- 环境: Mac 平台检出，Claude 会话；各项目 checkout 只做 broker fetch 与临时 detached worktree，读完即删
- 本记录负责证明的 acceptance criteria: AC-1 至 AC-6

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| broker `gitea.pulls.read --state closed`（aisoft-platform） | PASS | PR 390 `0192a8e`、393 `149e469`、394 `08be6f4`、398 `43db3d0`、399 `86821cf`、400 `fb9d8c5`、401 `fdf93c1`、404 `b2a154d`、405 `38ddc92`、407 `cee4294`、410 `f169b12`、411 `1db191e`，均 `merged=true` |
| 各合并 commit 上 `usage/bundle.json` 的最后一个 release | PASS | 149e469 1.3.0、08be6f4 1.4.0、43db3d0 1.5.0、86821cf 1.6.0、fb9d8c5 1.7.0、38ddc92 1.8.0、f169b12 1.9.0、1db191e 1.10.0；0192a8e、fdf93c1、b2a154d、cee4294 不改 `usage/` |
| broker `gitea.pull.read`（newemaint 322、hsdb 71、sfm-digital-board 185 与 187、localwms 336） | PASS | NewEMaint 322 `dfe04df` 2026-10-21；HSDB 71 `673cadb`；SFM 185 `799bf12`、187 `3bb6b78`；LocalWMS 336 `6e143fe`；均 `merged=true` |
| 各项目 main 合并 SHA 的 detached worktree 里 `.aisoft/bin/aisoft bundle status` | PASS | HSDB `673cadb`、SFM `3bb6b78`、LocalWMS `6e143fe` 各四项 PASS：platform-pin、tool-provenance、pointer-sections、change-templates，均为 1.8.0 |
| 同上 `.aisoft/bin/aisoft check-change-documents` | 见证据 | HSDB `changes=33 gap=0`；LocalWMS `changes=161 gap=0`；SFM `changes=78 gap=1`，GAP 全部是旧编号目录与无 front matter 的旧四文档（R12 LEGACY 范围，本批不处理） |
| LocalWMS `grep -n uses: .gitea/workflows/*` | PASS | 无输出 |
| 反向证明：删 03 新标题后跑 smoke | NOT RUN | 待 T02 |
| `bash codex/tests/smoke.sh` | NOT RUN | 待 T02 |
| `wc -c AGENTS.md` | NOT RUN | 基线 4767 字节 |

NewEMaint PR 322 正文：AC-5 的隔离比对被无关容器的重启循环误判为 FAIL，负责人以回执判过并记录例外；生产恢复仍 NOT RUN。

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | 待填写 | 待填写 |
| AC-2 | 待填写 | 待填写 |
| AC-3 | 待填写 | 待填写 |
| AC-4 | 待填写 | 待填写 |
| AC-5 | 待填写 | 待填写 |
| AC-6 | 待填写 | 待填写 |

## 交叉审查

| 轮次 | 实现方 | 审查方 | exact head | 结论 | 发现与处置 |
|---|---|---|---|---|---|
| 1 | Claude | Codex | 待填写 | NOT RUN | 待填写 |

## 遗留风险与未完成项

- 规则落在文档，执行仍靠会话；收尾读回 `origin/main` 是唯一确定性核对。

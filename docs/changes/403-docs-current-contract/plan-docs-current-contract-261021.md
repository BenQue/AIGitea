---
issue: 403
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/403
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - platform-governance
  - ci-change
depends_on:
  - 391
  - 395
  - 396
status: approved
branch: change/403-docs-current-contract
created: 2026-10-21
updated: 2026-10-21
---

# R14 文档现行态实施计划

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 分册改写：01–08 体例（现行合同段、来历表），`03` 叙事清理到 ≤ 26 行引用，`08` 示例表外移，`06` 速查与合同分开，`01` §4.3 标注，README §1 改指向生成命令并加未实施清单，GLOSSARY 术语；站点值改引 manifest `site` 段 | - | pending |
| T02 | smoke 治理步骤：`require_heading` 辅助、01–08/README 正文钉子改标题钉子、`smoke-pin-baseline.json` 棘轮、README 日期版本守卫、`test_architecture_governance.py` 改钉标题、泄漏基线 `--write-baseline`；单独 commit 后停止，fresh 重读 | T01 | pending |
| T03 | `aisoft-platform-readiness.sh --render-readme` 与 `test-platform-readiness.sh` 覆盖 | T02 | pending |
| T04 | 反向证明、全量 smoke、路线图 R14 行、verification、Codex 只读交叉审查、判级投影 | T03 | pending |

按 superpowers `executing-plans` 依 Txx 顺序内联执行，同一时刻一个写者；每张 ticket 至少一个原子 commit，主题含 `#403 Txx`。

## Expected touch points

- T01：`01`–`08`、`README.md`、`GLOSSARY.md`、`12-Linux-GitHub-Gitea-双服务器自动部署方案.md`、`13-项目结果迁移与内网切换实施手册.md`、`architecture/README.md`
- T02：`codex/tests/smoke.sh`、`codex/tests/smoke-pin-baseline.json`、`codex/runtime/tests/test_architecture_governance.py`、`codex/config/project-leak-baseline.json`
- T03：`codex/tools/aisoft-platform-readiness.sh`、`codex/tests/test-platform-readiness.sh`
- T04：`docs/governance/remediation-roadmap.md`、`docs/changes/403-docs-current-contract/*`

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | `rg -c '#[0-9]{2,3}' 03-Issue-Spec-Plan与单闸门开发流程.md`；`rg -n '#[0-9]{2,3}'` 逐行核对都在来历表 |
| AC-2 | `rg -n '^## 来历'` 01–08；来历 SHA 逐个 `git cat-file -e`；`rg -n '尚未(实施|运行)'` 01–08 |
| AC-3 | `bash codex/tests/smoke.sh`；反向证明：README 注入日期后 smoke 红 |
| AC-4 | `bash codex/tests/test-platform-readiness.sh`；`bash codex/tools/aisoft-platform-readiness.sh --render-readme` |
| AC-5 | `grep -c 'grep -Fq' codex/tests/smoke.sh` 与基线比对；反向证明：加一行 `grep -Fq` 后 smoke 红 |
| AC-6 | review：`01` §4.3、GLOSSARY diff；链接解析脚本 |
| AC-7 | `python3 codex/tests/check-project-leak.py`；`git diff codex/config/project-leak-baseline.json` |
| AC-8 | `git diff --stat origin/main -- skills templates usage` 为空；`bash codex/tools/usage-bundle.sh --verify`；`bash codex/tests/smoke.sh`；`bash -n`、`shellcheck`；`codex exec -s read-only`；`codex/tools/apply-classification-labels.sh --verify 403` |

## 部署与回滚

无部署影响；整 PR revert 即回滚。

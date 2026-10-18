---
issue: 371
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/371
change_type: docs
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - agent-governance
  - cross-module
depends_on:
  - 368
status: approved
branch: change/371-docs-deproject
created: 2026-10-17
updated: 2026-10-17
git_scope:
  - docs/changes/371-docs-deproject/summary-docs-deproject-261017.md
  - docs/changes/371-docs-deproject/spec-docs-deproject-261017.md
  - docs/changes/371-docs-deproject/plan-docs-deproject-261017.md
  - 01-基础设施-VM-Gitea-Runner.md
  - 02-CI与自动部署流水线.md
  - 03-Issue-Spec-Plan与单闸门开发流程.md
  - 04-Agent编排与定时任务.md
  - 05-通知与多人协作.md
  - 07-内网与生产平移路线.md
  - 08-双工具共存与实施.md
  - 09-v3平台简化与Loop-Engineering文档改造规划.md
  - 12-Linux-GitHub-Gitea-双服务器自动部署方案.md
  - 12-Windows平台自动部署方案.md
  - 13-项目结果迁移与内网切换实施手册.md
  - README.md
  - archive/09-v3平台简化与Loop-Engineering文档改造规划.md
  - archive/02-legacy-pilot-as-built.md
  - skill-for-claude/issue-session-flow/SKILL.md
  - codex/skills/issue-session-flow/SKILL.md
  - skill-for-codex/references/private-gitea-access.md
  - templates/project/ci/registry-preflight.sh
  - codex/tools/rotate-gitea-service-account.md
  - codex/config/project-leak-baseline.json
  - codex/runtime/tests/test_architecture_governance.py
  - codex/tests/smoke.sh
  - docs/governance/remediation-roadmap.md
---

负责人于 2026-10-17 在项目线程“平台治理整改”确认本合同，批准锚为 `c47c37f`。

## 目标

按 ADR 0001 D2/D3/D5/D9 清理通用文档与技能里的项目化内容：分册只写平台通用事实和规则，项目差异指向 manifest，事故教训保留为通用表述。

## 改写规则

1. **项目事故**：保留教训本身，删掉项目名；需要追溯时写 Issue 编号或指向 `06` 的踩坑编号（`06` 允许具体对象）。
2. **按项目区分的事实**（治理集合名单、哪个项目用哪个 runtime、各项目耗时）：改为“以 `codex/config/` manifest 为准”，或用匿名统计（如“最慢项目的 p90”）。
3. **已退出项目（rsdesign-new）的 as-built**：从现行分册移出。`02` 的 §1–§6 整体是该试点的 legacy 证据，原样迁到 `archive/02-legacy-pilot-as-built.md`，`02` 留一行指针。
4. **参考文档**（`12` 两份、`13`）：项目名改为“示例项目”，结构与合同不变。
5. **单票状态**：README 中只描述某张 Issue 当前状态的段落（如 #352 源码候选）移出，按 ADR D9 留在该 Issue 的 `docs/changes/`。
6. **站点配置值**：`05` 中邮件 `FROM` 等站点值改为占位（`<站点名>`），并说明真实值在站点配置里。
7. **钉住短语的测试**：被改写的短语若被测试钉住，改钉结构或新措辞；不删除测试意图。

## 逐文件处置

| 文件 | 处置 |
|---|---|
| `01` | 治理集合名单、runner 耗时表、Node 22 消费方、Flutter 实测、PostgreSQL 库名等改为 manifest 指针或匿名表述；rsdesign 遗留行改为“旧试点 runtime 已删除” |
| `02` | §1–§6 迁 `archive/02-legacy-pilot-as-built.md`；§0 把 Docker-first 表述为参考实现（ADR D5）；其余去项目名 |
| `03` | 事故案例去项目名、改指 06 或 Issue；示例命令里的项目路径与 id 改占位；依赖边改为指向 manifest `dependency_read_targets` |
| `04`、`08` | provider 迁移与 pilot 证据去项目名，保留“曾有一个 pilot 证据，已退出治理”的事实 |
| `05` | 邮件配置示例改占位 |
| `07` | 公司内网 pilot 改为“示例项目”；rsdesign 试点段落改为指针 |
| `09` | `git mv` 到 `archive/`，README 与测试同步 |
| `12` 两份、`13` | 项目名改“示例项目” |
| `README.md` | §1 状态表去项目名单；§6/§7 中 rsdesign 行删除或改指针；#352 单票段移出 |
| 两份 `issue-session-flow`、`private-gitea-access.md` | 依赖边改为“以 manifest `dependency_read_targets` 为准” |
| `registry-preflight.sh`、`rotate-gitea-service-account.md` | 注释与说明去项目名 |
| 基线 | `check-project-leak.py --write-baseline` 收紧 |

## 验收标准

- AC1：上表文件在棘轮基线中的条目清零或只剩“示例项目”无法替代的必要引用（若有，在 PR 中逐条说明）。
- AC2：PR 正文给出删除/改写清单：文件、原内容摘要、去向。
- AC3：仍有效的规则与教训不丢失（diff review 对照）。
- AC4：macOS 本机 smoke 全绿，PR CI 绿。

## 边界

- `git_scope` 为全部范围；不改 runtime 产品代码、CI workflow 行为、installer、manifest。
- 不碰 `templates/docs/changes/_template/`（下游 vendored，留 R4）、`architecture/`、`docker-release/`、`company-delivery/`。

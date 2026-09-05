---
issue: 154
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/154
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - external-contract
  - shared-core
depends_on: []
status: pending
branch: change/154-catalog-fastify-kysely
created: 2026-09-05
updated: 2026-09-05
---

# Verification: catalog Fastify 与 Kysely，systemd 原生 profile 1.1.0

## 基线与范围

- Commit SHA: `change/154-catalog-fastify-kysely`，rebase 后 base 为 `87b3aa4`
- 基线：`origin/main` = `07084de`（建 worktree 时）→ rebase 到 `87b3aa4`（smoke staleness 闸门要求）
- 环境: macOS / Python 3，本机 `architecture/bin/aisoft-architecture`，无新增依赖，不改 broker
- 本记录负责证明的 acceptance criteria: AC-1 至 AC-8

### 改动前基线（合并后无法重放）

| 基线观测 | 结果 |
|---|---|
| `PYTHONPATH=codex/runtime python3 -m unittest discover -s codex/runtime/tests -p 'test_architecture_*.py' -t codex/runtime` | `Ran 39 tests ... OK` |
| 五个 `architecture/fixtures/valid/*.json` 逐个 `validate` | 全部 `"valid":true`，`catalog_revision` 均为 `2026.08.3` |
| `bash codex/tests/smoke.sh` | rc=0，`Ran 660 tests ... OK` |
| `architecture/catalog.json` 组件数 | 29，无任何 `framework.fastify.` 或 `orm.kysely.` 条目 |

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| `curl https://registry.npmjs.org/fastify` | PASS | `dist-tags.latest` = `5.12.3`，发布时间 `2026-09-04T08:21:57Z`；`four` = `4.29.1` |
| 读回 <https://fastify.dev/docs/latest/Reference/LTS/> | PASS | LTS 表：5.0.0 released 2024-09-17 / End of LTS `TBD`；4.0.0 released 2022-06-08 / End of LTS `2025-06-30` |
| `curl https://registry.npmjs.org/kysely` | PASS | `dist-tags.latest` = `0.29.5`，发布时间 `2026-08-10T00:41:31Z`，`engines.node` = `>=22.0.0`，另一个 dist-tag 是预发布 `next` = `0.30.0-beta.1` |
| `aisoft-architecture explain --component framework.fastify.5` | PASS | `{"component_id":"framework.fastify.5","state":"preferred","version":"5.12.3","support_end":null,"eol":null,...}` |
| `aisoft-architecture explain --component orm.kysely.0-29` | PASS | `{"component_id":"orm.kysely.0-29","state":"preferred","version":"0.29.5","support_end":null,"eol":null,...}` |
| 五个 valid fixture 逐个 `validate` | PASS | 全部 `"valid":true`，`catalog_revision` 均为 `2026.09.0`；systemd fixture 为 `{"catalog_revision":"2026.09.0","lock_sha256":"230513d08b5c9e8311e4be1d04cfecac6847991923f7ef89f2d8558c07a663bb","profile_id":"linux-node-systemd-postgres-v1","project_id":"fixture-linux-systemd","valid":true}` |
| 三份 reference `lock` 重新生成 | PASS | newemaint `8bde0d16e41bb7d4fffddbc0b4a7da87717008f69dbc418196ba8997b8d1219a`、windows `83f88581b51106ee7b4b7a3cec4bc4aacb4446b8f13789692a94b83e799dafd5`、sqlite `48b29470e31548bd066863e5e887f235c4cda8bc5274eb059b1865b9a7cdc5db` |
| 同三份 lock 第二次生成后 `cmp` | PASS | 三份都是 `BYTE_IDENTICAL` |
| LocalWMS 形状候选声明 `validate`（catalog 钉的版本） | PASS | `{"catalog_revision":"2026.09.0","lock_sha256":"98b1b7e52a19e34912d5ecd9d52a9e536f7a9d49b734ae43ba3d2cf3a20ac381","profile_id":"linux-node-systemd-postgres-v1","project_id":"localwms","valid":true}`，rc=0 |
| 同一形状但用 LocalWMS 当前实际版本 | PASS（预期失败） | `{"diagnostics":[{"code":"PROJECT_VERSION_DRIFT","message":"Project version 与 pinned Catalog 不一致。","path":"$.components[5].version"}],"valid":false}` |
| LocalWMS 已提交声明对新 catalog `validate` | PASS（预期失败） | `{"diagnostics":[{"code":"PROJECT_CATALOG_MISMATCH",...,"path":"$.catalog_revision"}],"valid":false}` |
| `git diff 87b3aa4 --unified=0` 于既有三 profile、四个 valid fixture、五个 invalid fixture | PASS | 全部 diff 合计只有 12 行 `-"catalog_revision": "2026.08.3",` 与 12 行 `+"catalog_revision": "2026.09.0",` |
| `unittest discover -p 'test_architecture_*.py'` | PASS | `Ran 39 tests ... OK` |
| `unittest discover -p 'test_*.py'`（全量 runtime） | PASS | `Ran 660 tests ... OK` |
| `bash codex/tests/smoke.sh` | PASS | rc=0，`Ran 668 tests ... OK`，`Codex platform static smoke checks passed.`（668 比基线的 660 多 8 条，来自 rebase 带进来的 #180/PR #244） |

`smoke.sh` 第一次跑报的是 `architecture/install.sh` 的 staleness 闸门（#171/#162），
原因是 worktree 落后 `origin/main`，不是本次 diff。broker `git.fetch.main` 后 rebase 到
`87b3aa4` 再跑即通过。

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | PASS | 两条 `explain` 输出；`provenance.evidence` 分别写明 Fastify LTS 表的 6+6 个月窗口与 End of LTS TBD，以及 Kysely 无支持窗口表因此 lifecycle 日期为 null |
| AC-2 | PASS | catalog `revision` = `2026.09.0`，`published_at` = `2026-09-05`，`review_by` = `2026-12-05`；任一 validate 输出的 `catalog_revision` 均回读为 `2026.09.0` |
| AC-3 | PASS | profile `version` = `1.1.0`，`required_components` 增加 `framework.fastify.5` 与 `orm.kysely.0-29`，第三条 `compatibility_rules` 已改写为「声明了 framework 与 query-builder slot，仍不声明 frontend/proxy/container slot」 |
| AC-4 | PASS | 上表的 12+12 行 diff 统计；`linux-systemd-project.json` 按 spec 修订后的 AC-4 跟随其 profile 升到 1.1.0 并补两个组件 |
| AC-5 | PASS | 三份 lock 重新生成的 sha256 与第二次生成的 `BYTE_IDENTICAL` 比较 |
| AC-6 | PASS | LocalWMS 形状候选声明 `"valid":true`，profile `linux-node-systemd-postgres-v1`，revision `2026.09.0`，components 含两个新组件 |
| AC-7 | PASS | `smoke.sh` rc=0 与 39/660 两轮单测 |
| AC-8 | PASS | 见下方「遗留风险与未完成项」的重装交接项 |

## 遗留风险与未完成项

- **合并后必须重装 `architecture/install.sh`**（显式交接项，AC-8）。它有 source staleness
  闸门（#171/#162）：已安装的 CLI 仍带旧 catalog 与旧 profile，安装一个落后的 checkout 会
  在成功输出里看不出区别。本 PR 不执行安装，合并后由人在最新 `main` 上重跑
  `architecture/install.sh`。
- **LocalWMS 必须在自己的仓开 Issue 重新声明**。上表已给出两条实测证据：现有声明对新
  catalog 报 `PROJECT_CATALOG_MISMATCH`；即使改成 1.1.0 形状，它当前实际安装的
  `fastify@5.12.1` 与 `kysely@0.28.17` 仍会报 `PROJECT_VERSION_DRIFT`。它需要同时
  升到 `catalog_revision` `2026.09.0`、`profile_version` `1.1.0`、`fastify@5.12.3`、
  `kysely@0.29.5`，并重新生成 `architecture.lock.json`。本变更只读了它的声明与
  `package.json`，没有写入该仓任何文件。
- **未执行**：不曾部署、不曾安装、不曾改 `codex/runtime/aisoft_architecture/` 下的 validator
  或 lock 逻辑、不曾改任何 schema、不曾扩 `PACKAGE_RELEASE_CONTRACTS`、不曾触碰
  `docker-release/`。
- **刻意保留的旧值**：`architecture/fixtures/invalid/tampered-lock.json` 仍钉
  `2026.08.0`，它是历史 lock 的负面 fixture，三次历史 revision bump 同样没有动它。
  `13-项目结果迁移与内网切换实施手册.md` 的示例 front matter 仍写
  `architecture_catalog_revision: "2026.08.3"`，那是与 `FULL_SHA`、`LOCK_SHA256` 并列的
  占位示例，历史 revision bump 也没有把它当作事实源更新。
- **回滚**：revert 唯一最终 PR 并重跑本表全部命令。

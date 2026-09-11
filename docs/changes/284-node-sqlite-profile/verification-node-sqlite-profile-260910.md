---
issue: 284
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/284
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - shared-core
  - external-contract
depends_on: []
status: pending
branch: change/284-node-sqlite-profile
created: 2026-09-10
updated: 2026-09-10
---

# Verification：Node 22 加 SQLite profile 与三处 architecture 合同裁决

## 基线与范围

- Commit SHA: `1c45f9cfb44858d3055290a8923cd2d171051c9d`
- 基线：`origin/main` = `1164318c6a1c40aa9686e9bc6b0d58a79ca714ee`
- 环境：Mac 本机 worktree `/private/tmp/issue-284-node-sqlite-profile`，Python 3，
  `rg` = `/opt/homebrew/bin/rg`（真实二进制，非 shim）
- 本记录负责证明的 acceptance criteria：AC-1 至 AC-9，重点是改动前才观测得到的三条
  基线证据与两次 lock 的 byte-identical 结果。

## 改动前基线观测

这三条只在改动前观测得到，合并后无法重放。全部在基线 `1164318` 上执行，
命令为 `architecture/bin/aisoft-architecture validate`，输入为临时探针声明。

| 探针 | 观测结果 |
|---|---|
| 既有 profile 的 transition 引用 `http://gitea-ci.orb.local:3000/.../issues/142` | `MIGRATION_ISSUE_INVALID` |
| 同一份声明改用 `https://` | `valid: true` |
| 同上再把 Node 版本从 pin `22.22.3` 改成真实的 `22.22.0` | `PROJECT_VERSION_DRIFT` |

内网 tracker 的 scheme 观测（`curl`，同一时间点）：

| URL | 结果 |
|---|---|
| `http://gitea-ci.orb.local:3000/api/v1/version` | `200`，`{"version":"1.26.4"}` |
| `http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/284` | `200` |
| `https://gitea-ci.orb.local/` | `200`，返回 nginx 默认欢迎页 |
| `https://gitea-ci.orb.local/admin/aisoft-platform/issues/284` | `404` |

结论：平台 tracker 只在 http 端口提供服务，443 上是另一个服务。validator 从不解引用
该 URL，因此改动前满足 https-only 的唯一办法是写一个语法合规但不解析的 URL。
这正是裁决 C 的依据。

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| `python3 -m unittest discover -s codex/runtime/tests -p 'test_architecture*.py'`（基线 `1164318`） | PASS | `Ran 39 tests ... OK` |
| `python3 -m unittest discover -s codex/runtime/tests -p 'test_architecture*.py'`（本分支） | PASS | `Ran 53 tests ... OK` |
| `python3 -m unittest discover -s codex/runtime/tests -p 'test_*.py'` | PASS | `Ran 854 tests ... OK` |
| `bash codex/tests/smoke.sh` | PASS | `Codex platform static smoke checks passed.`，`[exited with code 0]` |
| `validate` 原生环境 fixture | PASS | `"profile_id":"linux-node-sqlite-v1","project_id":"fixture-node-sqlite-native","valid":true` |
| `validate` 容器环境 fixture | PASS | `"profile_id":"linux-node-sqlite-v1","project_id":"fixture-node-sqlite-container","valid":true` |
| `lock` 各跑两次后 `cmp` | PASS | 两个环境各自两次输出 byte-identical |

`smoke.sh` 曾在中途红过一次：`release runtime differs outside the separately approved
transport.py revision`。原因是本变更起初改了 `codex/runtime/aisoft_release/contract.py`，
落在 Issue #65 的证据闸门内。处置是撤回该改动并改变设计（lock 不新增字段），
不是扩大闸门豁免清单——那属于 #65 的授权边界。撤回后 smoke 转绿。

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | PASS | `linux-node-sqlite-v1` 加入后 5 个 profile 全部通过 `validate_profile`；`test_catalog_and_all_profiles_validate` 的计数断言由 4 改为 5 |
| AC-2 | PASS | 两份 fixture 分别取 `pm2-legacy` 与 `docker-release/v1`，均 `valid: true`；`test_node_sqlite_profile_slots_and_multi_environment_contracts` 钉住两个取值 |
| AC-3 | PASS | `test_architecture_as_built.py` 逐条断言 `AS_BUILT_EXCEPTION_REQUIRED`、`AS_BUILT_MAJOR_MISMATCH`（含 `0.x` minor 用例）、`AS_BUILT_NOT_REQUIRED`、`AS_BUILT_VERSION_UNPARSED`、`AS_BUILT_DIGEST_FORBIDDEN` |
| AC-4 | PASS（范围已调整） | lock 记录 `3.53.1`/`16.2.6`/`22.22.0` 等真实构建与 `exception_id`、`exception_expires_at`；lock **不**新增字段，理由见上一节与 ADR-0006 |
| AC-5 | PASS | `test_without_as_built_the_exact_pin_still_governs` 与既有 `semver-range.json` 仍返回 `PROJECT_VERSION_DRIFT` |
| AC-6 | PASS | `test_migration_issue_accepts_absolute_http_and_still_rejects_the_rest` 接受绝对 http，并逐条拒绝简写、相对路径、非 http(s) scheme、带凭据、带 query、带 fragment |
| AC-7 | PASS（人工复核） | ADR-0006 记录四条裁决与边界；ADR-0003/0004 加交叉引用；`architecture/README.md` 与 runbook §9 同步 |
| AC-8 | PASS | 既有 39 个 architecture 测试与 854 个 runtime 测试全绿，smoke `exit 0`；既有 4 个 profile 与全部既有 fixture 未改动 |
| AC-9 | PASS | 两个环境各自连续两次 `lock` 输出 `cmp` 无差异 |

## 遗留风险与未完成项

- **下游项目的 OS slot 未解除阻塞。** 按裁决 D 不新增 `os` 取值。运行在已 EOL 的 interim
  Ubuntu 上的主机无法产出有效声明，实测诊断码如下表。正确处置是把该主机迁到受支持的
  LTS，属于应用仓自己的 Change。

  | 写法 | 诊断码 |
  |---|---|
  | `os` slot 上如实写 `25.10` 并加 `as_built` | `AS_BUILT_MAJOR_MISMATCH` |
  | 直接写未收录的 `os.ubuntu.25-10` | `PROJECT_COMPONENT_UNKNOWN` |
  | 假如 catalog 收录了该取值 | `COMPONENT_EOL`（本变更未收录，故不会实际触发） |

- **容器交付基镜像规则已补上执行路径。** 该规则最初只写在 `compatibility_rules` 散文里，
  下游会话实测 fail open：删掉 OCI component 后声明仍 `valid: true`。合并前补为按
  delivery contract 触发的平台规则 `DELIVERY_BASE_IMAGE_REQUIRED`，同一份探针复跑得
  `valid: false`。仓内既有全部容器交付声明本就已声明基镜像，对它们是 no-op；
  digest 本身仍由既有 `OCI_DIGEST_REQUIRED` 校验，可变 tag 照旧 fail closed。
- **工具链从本地 checkout 工作树解析 `architecture/`。** 本变更合并后，本地 `main` 未
  fast-forward 的机器解析不到新 profile，表现像声明写错。已在 `architecture/README.md`
  的 CLI 一节写明先 ff 再重跑。
- **本记录不包含任何部署。** `deployment_lifecycle` 为 `none`，本变更只改平台仓的
  schema、validator、profile 与文档，不部署、不生成任何真实项目的 current lock。
- **fixture 使用的版本组合取自一个真实仓库的运行形态**，但 `project_id` 与 migration Issue
  主机均为中性占位值，profile 本身不复制任何单个项目的取值。

---
issue: 33
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/33
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - security
  - external-contract
  - shared-core
  - compatibility
  - platform-governance
depends_on: []
status: pr-open
branch: change/33
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/34
created: 2026-08-06
updated: 2026-08-06
---

# Verification

## 结论

AISoftPlatform-local implementation 与验证为 **PASS**。Catalog `2026.08.3`、Linux profile
`1.1.2`、NewEmaint target candidate 与三套 committed reference locks 已一致更新；Next.js
`16.3.0`、Prisma 三包 `7.9.1`、React/ReactDOM `19.2.8` 均保持 exact identity。

最终 PR #34 已创建；其 latest-head CI 在 handoff commit 推送后重新判定。人工 merge、merge commit
读回与 NewEmaint #52 消费尚未发生，仍为 `BLOCKED_EXTERNAL`，不得报告为已交付或已解除应用
安全 Gate。

## Acceptance criteria evidence

| AC | Result | Evidence |
|---|---|---|
| AC-1 | PASS | Context7 `/vercel/next.js` 与 npm Registry readback：`next@16.3.0` stable/latest，Node `>=20.9.0`，React/ReactDOM peers `^19.0.0`；catalog 固化 exact URL、integrity 与 2026-08-03 release date。 |
| AC-2 | PASS | Registry readback：`prisma`、`@prisma/client`、`@prisma/adapter-pg` latest 均为 `7.9.1`；catalog 固化三个 distinct integrity 与 2026-07-27 release date。 |
| AC-3 | PASS | React/ReactDOM 仍为 `19.2.8`；Linux profile `1.1.2` 记录 Next.js/Prisma/Node/React compatibility，未引入 range、dist-tag 或 prerelease。 |
| AC-4 | PASS | Focused negative tests 拒绝旧 Next/Prisma、range、`latest` channel/package、Canary/dev、package-set 漂移、Prisma mismatch、错误 Registry URL、future metadata；旧 project version 为 `PROJECT_VERSION_DRIFT`，stale lock 为 `LOCK_DRIFT`。 |
| AC-5 | PASS | Catalog/profile/declarations/references 使用 revision `2026.08.3`；三套 lock 由 CLI 重建，第二次 temp generation 均为 `BYTE_IDENTICAL`。 |
| AC-6 | PASS（platform-local） | Disposable Node `v24.3.0` / npm `11.5.2` 安装四个 exact packages；host rerun 的 `prisma validate` 与 `prisma generate` PASS，Client `7.9.1`；focused 31 tests、CLI 3 tests、installer、ShellCheck、full smoke 201 tests 全部 PASS。 |
| AC-7 | PARTIAL / BLOCKED_EXTERNAL | Gap report 已写清迁移顺序与禁止伪造 merge SHA。最终 exact protected-main SHA 只能在人工 merge 后读回；PR/merge/NewEmaint consumption 均未运行。 |

## Commands and actual results

| Command | Result |
|---|---|
| `PYTHONPATH=codex/runtime python3 -m unittest codex.runtime.tests.test_architecture_schema codex.runtime.tests.test_architecture_lock codex.runtime.tests.test_architecture_transitions codex.runtime.tests.test_release_architecture_integration -v` | PASS，31 tests |
| `PYTHONPATH=codex/runtime python3 -m unittest codex.runtime.tests.test_architecture_cli -v` | PASS，3 tests |
| `bash -n codex/tests/smoke.sh` + `bash -n codex/tests/test-architecture-install.sh` | PASS |
| `shellcheck codex/tests/smoke.sh codex/tests/test-architecture-install.sh` | PASS，ShellCheck 0.11.0 |
| `bash codex/tests/test-architecture-install.sh` | PASS，installer idempotence |
| `bash codex/tests/smoke.sh` | PASS，201 tests |
| `architecture/bin/aisoft-architecture validate ...newemaint... --lock ...` | PASS，revision `2026.08.3`，lock `51466370…77a8` |
| second CLI generation + `cmp` for NewEmaint/SQLite/Windows locks | PASS，三项 `BYTE_IDENTICAL` |
| strict JSON parse over catalog/profiles/fixtures/reference declarations/locks | PASS |
| `git diff --check` | PASS |

## Prisma disposable smoke

一次性目录 `/private/tmp/aisoft-33-prisma.*` 使用 exact dependencies：

- `next@16.3.0`
- `prisma@7.9.1`
- `@prisma/client@7.9.1`
- `@prisma/adapter-pg@7.9.1`

首次 sandbox 内 `prisma validate` 因 `binaries.prisma.sh` DNS 被阻断，分类为
`SANDBOX_PATH_BLOCKED`；同一临时目录在获准 host-network 路径重跑后，schema valid 且成功生成
Prisma Client `7.9.1`。Schema/config 只包含虚拟 PostgreSQL URL，未连接数据库、未运行 migration
或 `prisma db push`。

## NOT RUN / 外部门禁

- Gitea PR #34：`OPEN`；latest-head CI 在最终 handoff push 后读回，本文不预填结果。
- 人工 merge 与 exact merge commit：`BLOCKED_EXTERNAL`，只有人可合并。
- NewEmaint package/lock/audit/build/browser/current lock：`NOT RUN`，不在 #33 mutation scope。
- Docker、Registry、server、database、Secret、deployment、production：`NOT RUN`，未授权且未执行。

## 回滚

平台变更只通过最终 PR 的 revert 回滚，并重新运行同一验证集。不得在 catalog `2026.08.3` 下
恢复 `next@16.2.11`、Prisma `7.8.0` 或放宽 validator；NewEmaint 在 exact merge SHA 可读并完成
应用自有 Gate 前继续保持安全阻塞。

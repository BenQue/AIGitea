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

# Implementation plan

## 任务分解

1. 读回 Issue #33/comment、`origin/main@d20811b`、NewEmaint comment 2077、Context7 官方
   Next.js/Prisma 文档与 npm Registry exact metadata，建立不含 Secret 的 evidence ledger。
2. 将 architecture semantic validator 的 React-only stable package contract 泛化为受治理
   component package-set contract，保留现有 React diagnostics，并增加 Next.js/Prisma
   missing/set/channel/exact-version/Registry/date/mismatch negative tests。
3. 更新 catalog revision、Next.js/Prisma component package snapshots、Linux profile compatibility、
   templates、valid/invalid fixtures、NewEmaint target candidate 与 gap report；保持 React 19.2.8。
4. 以 `architecture/bin/aisoft-architecture lock` 重新生成 NewEmaint、SQLite、Windows reference
   locks，并用第二个 temp output 做 byte-identical 比较，禁止手写 checksum。
5. 在 disposable temp workspace 安装 exact packages，运行 Prisma 7 `validate`/`generate`；再运行
   focused unittest、architecture install/CLI、release integration、full smoke、JSON/diff/scope checks。
6. 写 `03-verification.md` 记录真实 PASS/FAIL/NOT RUN/BLOCKED_EXTERNAL；通过单一最终 PR
   `Closes #33` 交给人工合并。合并后由 owner 读回 exact protected-main SHA 并提供给 NewEmaint #52。

## 涉及文件

- `docs/changes/33/{00-summary,01-spec,02-plan,03-verification}.md`
- `architecture/{catalog.json,README.md,evidence/official-sources.md,profiles/**,templates/**,fixtures/**,reference/**}`
- `codex/runtime/aisoft_architecture/validator.py`
- `codex/runtime/tests/test_architecture_schema.py`
- 必要时更新 `codex/tests/{smoke.sh,test-architecture-install.sh}`，但不引入 CI 联网依赖。

## 数据库迁移

无。Disposable Prisma smoke 只做 schema/config 静态 validate 与 client generation，不连接数据库、
不执行 migration，也不运行 `prisma db push`。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1, AC-2, AC-3 | Registry/Context7 evidence review；`architecture/bin/aisoft-architecture explain --component framework.next.16` 与 `orm.prisma.7` |
| AC-4 | `PYTHONPATH=codex/runtime python3 -m unittest codex.runtime.tests.test_architecture_schema -v`；stale fixture/lock negative cases |
| AC-5 | validate all valid/reference declarations；canonical lock temp comparison；`git diff --check`；strict JSON parse |
| AC-6 | disposable exact `npm install` + `npx prisma validate` + `npx prisma generate`；focused architecture/release unittest；`bash codex/tests/test-architecture-install.sh`；`bash codex/tests/smoke.sh` |
| AC-7 | Review `architecture/reference/newemaint/gap-report.md` 与 `03-verification.md`；人工 merge 后读回 `origin/main` exact SHA |

## 部署与回滚

无部署。本 Change 不修改 Docker、Registry、server、database、Secret 或 production。代码回滚为
revert 最终 PR 并重新运行同一 platform-local test set；NewEmaint 在 exact merge SHA 可读前继续
保持安全 Gate `BLOCKED`。

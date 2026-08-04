# NewEmaint read-only architecture gap report

- Authority: live `gitea/main@dfdb93ca1e36b222ae38a747e78a5db263302c86`
- Collection: sanitized read-only, 2026-08-04
- Current identity: `newemaint` — **BLOCKED_EXTERNAL; no current declaration/lock generated**
- Target candidate: `newemaint-target-candidate`, `linux-node-postgres-v1@1.1.0`, catalog `2026.08.1`
- Application checkout status: pre-existing dirty; this collection performed no writes
- Status: **TARGET CANDIDATE ONLY — NOT MIGRATED, NOT DEPLOYED**

| Area | Observed at authoritative ref | Catalog representation | Required separate Change |
|---|---|---|---|
| Node | root engine `>=22 <23`; mutable Node 22 and legacy Node 18 container tags | Node 22.22.3 sunset; preferred target 24.18.0 | Node/runtime Change with exact runtime, compatibility and rollback evidence |
| npm | `npm@10.0.0` | npm 10.0.0 sunset; preferred target 11.19.0 | package-manager Change with `npm ci`, lock and build parity |
| Prisma | declarations on major 5; lock 5.22.0; `prisma-client-js` | Prisma 5.22.0 sunset; preferred target 7.8.0 | ORM-only Change for config, generator output, driver adapter, queries and migrations |
| PostgreSQL | 15/16 mutable tags in different Compose/deploy paths | 16.14 supported; preferred target 18.4 | database-only Change with authoritative topology, backup, restore, migration and rollback |
| Next.js | lock 14.2.33 | 14.2.33 recorded as **prohibited** because upstream marks 14.x unsupported | Migrate to a supported major before any current lock; an exception cannot override prohibited/EOL |
| React | apps/web resolves 18.3.1; root lock also contains 19.1.0 | 18.3.1 sunset; preferred target 19.3.0 | frontend/framework Change resolving scope and peer compatibility |
| TypeScript | lock 5.8.3 | 5.8.3 sunset; preferred target 6.0.2 | toolchain Change with typecheck/deprecation evidence |
| OCI/proxy | `latest`, major-only and `nginx:alpine` mutable identities | Node 22.22.3 linux/amd64 child digest is catalogued; target uses Node 24 digest and NGINX 1.30.4 | image/release Change with mirror, checksum, SBOM/provenance and rollback evidence |

`target-candidate/architecture.json` 与其 canonical lock 只描述目标架构，不能替代 current bytes、
migration Issues、application CI、Docker/Registry/AppServer 验收或部署证据。`current-transition/`
在每个实际 major migration 都有 NewEmaint 中真实可读的独立 Issue、对应 exception，且全部组件
仍满足 upstream support policy 后才可生成。

当前缺少创建 NewEmaint migration Issues 的授权；此外 Next.js 14 已是 prohibited，因此仅授权
创建 Issues 仍不足以生成有效 current lock。不得以 NewEmaint #51、虚构 URL、target candidate
或放宽 validator 代替这些 Gate。Node、Prisma、PostgreSQL、Next/React、TypeScript 与 OCI/image
迁移均不得合并成一个“已迁移”声明。

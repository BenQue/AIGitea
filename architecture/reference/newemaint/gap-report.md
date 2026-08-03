# NewEmaint read-only architecture gap report

- Authority: `gitea/main@ecbdc674fde1f785cafdee92c6ee88c691104a34`
- Collection: sanitized read-only, 2026-08-02
- Candidate: `linux-node-postgres-v1@1.0.0`, catalog `2026.08.0`
- Application repository status after collection: clean
- Status: **DRY-RUN CANDIDATE — NOT MIGRATED, NOT DEPLOYED**

| Area | Observed at authoritative ref | Target candidate | Required separate Change |
|---|---|---|---|
| Node | root engine `>=22 <23`; Node 22 and legacy Node 18 mutable container tags | Node 24.18.0 + immutable official-image digest | Node/runtime Change; remove legacy base lines only after compatibility and rollback evidence |
| npm | `npm@10.0.0` | npm 11.19.0 | package-manager Change with `npm ci`, lock and build parity |
| Prisma | declarations on major 5; lock 5.22.0; `prisma-client-js` | Prisma 7.8.0 | ORM-only Change for config, generator output, driver adapter, queries and migrations |
| PostgreSQL | 15/16 mutable tags in different compose/deploy paths | 18.4 | database-only Change with authoritative topology, backup, restore, migration and rollback |
| Next.js | 14.2.33 | 16.2.11 Active LTS | framework-only Change using official codemod, build/browser compatibility and rollback evidence |
| React | manifest major 18 range but root lock resolves 19.1.0 | 19.3.0 only after framework compatibility | frontend Change resolving declaration/lock mismatch and Next compatibility |
| TypeScript | lock 5.8.3 | 6.0.2 | toolchain Change with typecheck/deprecation evidence |
| OCI/proxy | `latest`, major-only and `nginx:alpine` mutable identities | tag + digest, SBOM/provenance, NGINX 1.30.4 | image/release Change; never edit live manifests from this catalog Change |

The committed `architecture.json` and `architecture.lock.json` in this evidence directory describe a
target candidate only. They were not copied into NewEmaint, and no package lock, Dockerfile, Prisma
schema, image, server or database was modified. Node, Prisma and PostgreSQL majors must not be merged
into one migration Change.

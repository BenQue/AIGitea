# Official source and compatibility evidence

Catalog evidence retrieved: 2026-08-02 · Server-inventory supplement retrieved: 2026-08-03 ·
Issue #26 transition supplement retrieved: 2026-08-04 · Next review: 2026-11-02 for original
catalog entries, 2026-11-03 for server inventory and 2026-11-04 for transition evidence · Method: one
Context7 query per concept, with official/upstream readback where lifecycle or exact release metadata
was required.

## Issue #26 transition evidence supplement

| Component | Official/upstream readback | Exact conclusion and conflict handling |
|---|---|---|
| Node.js 22 | <https://nodejs.org/en/download/archive/v22.22.3> and <https://nodejs.org/en/about/previous-releases> | `22.22.3` exists and v22 is Maintenance LTS to April 2027, but Context7's current official-doc extraction identifies a newer v22 patch. The catalog preserves the approved exact NewEmaint transition fact as `sunset`; it does not call it latest. |
| npm 10 | <https://docs.npmjs.com/cli/v10/using-npm/changelog/> plus official npm registry metadata | Exact `10.0.0`, integrity and Node engine `^18.17 || >=20.5` were read back. npm has no fixed v10 EOL table, so the catalog date is explicitly a platform exception deadline, not an upstream support promise. |
| Prisma 5 | <https://github.com/prisma/prisma/releases/tag/5.22.0> and <https://www.prisma.io/docs/orm/more/upgrade-guides/upgrading-versions/upgrading-to-prisma-7> | Existing exact `5.22.0` is preserved as sunset. Context7 confirms that Prisma 7 changes generator output, driver adapter and configuration contracts, so migration remains an independent application Change. |
| PostgreSQL 16 | <https://www.postgresql.org/support/versioning/> and <https://www.postgresql.org/docs/release/16.14/> | Exact `16.14` is a supported current minor and major 16 remains supported through 2028-11-09. It is an allowlisted `supported` transition, not proof of NewEmaint database migration or topology. |
| Next.js 14 | <https://nextjs.org/support-policy>, <https://nextjs.org/docs/pages/guides/upgrading/version-14> and official npm registry metadata | Exact `14.2.33` exists and declares Node >=18.17 / React ^18.2, but the current official policy marks 14.x **unsupported**. It is therefore catalogued as `prohibited`, intentionally omitted from transition allowlists and cannot appear in a valid current lock. |
| React 18 | <https://github.com/facebook/react/blob/main/CHANGELOG.md> plus official npm registry metadata | Exact `18.3.1` exists and is described as a bridge to React 19. It is recorded as sunset with a platform deadline; framework peer compatibility remains project-owned. |
| TypeScript 5 | <https://www.typescriptlang.org/docs/handbook/release-notes/typescript-5-8.html> plus official npm registry metadata | Exact `5.8.3` exists. Upstream publishes no fixed 5.8 EOL, so the platform transition deadline is not presented as upstream support. |
| Node 22 OCI | <https://hub.docker.com/_/node> and Docker Registry V2 manifest readback | `node:22.22.3-bookworm-slim` resolves to index `sha256:e21fc383b50d5347dc7a9f1cae45b8f4e2f0d39f7ade28e4eef7d2934522b752`; the catalog pins the selected `linux/amd64` child manifest `sha256:16d364eebf6b62da439dc993d9b80940c78b0ca38438452f011ab9a25c752644`. Index and child digests are not interchangeable. |

The supplement used Context7 resolution/query for Node.js (`/nodejs/nodejs.org`), Prisma
(`/prisma/web`) and Next.js (`/vercel/next.js`), then official readback for exact release, support and
registry identities. NewEmaint remote main was read only at
`dfdb93ca1e36b222ae38a747e78a5db263302c86`; no application file or environment was modified.

| Concept | Official/upstream source | Catalog conclusion | Compatibility evidence / conflict handling |
|---|---|---|---|
| Ubuntu lifecycle | <https://documentation.ubuntu.com/release-notes/24.04/> and <https://wiki.ubuntu.com/Releases> | 24.04.4 preferred; 26.04 prohibited candidate | Context7's Ubuntu page extraction conflated lifecycle columns, so Canonical release notes were read back for exact 2029-05-31 standard-support end and the release table for point-release/long-tail dates. Month-only EOL is normalized to its final calendar day. Both inventoried servers already run 26.04; that is as-built evidence, not catalog approval. 26.04 remains blocked pending first point release plus AISoftPlatform soak. |
| Windows Server lifecycle | <https://learn.microsoft.com/en-us/lifecycle/products/windows-server-2025> | Server 2025 build family preferred; mainstream 2029-11-13, extended 2034-11-14 | Product lifecycle is authoritative when the container base-image table shows slightly different servicing dates. Build 26100 comes from the official base-image table. |
| IIS role | <https://learn.microsoft.com/en-us/windows-server/administration/server-core/server-core-roles-and-services> | `Web-Server` feature manifest pinned to Windows Server 2025 | IIS is an OS role, not an independently supported semver product. Lifecycle inherits the OS; ASP.NET Core Module/hosting bundle is validated with .NET. |
| Node lifecycle | <https://nodejs.org/en/about/previous-releases> | Node 24.18.0 preferred; Node 22.22.3 sunset; Node 20 observed and EOL | Production applications use Active/Maintenance LTS only. Node 24 ends April 2028; Node 22 ends April 2027. Both inventoried servers run Node 20.20.2, while the official table marks v20 EOL after its March 2026 final update. Remediation requires a separate runtime/server Change. |
| Python 3.14 lifecycle | <https://peps.python.org/pep-0745/> and <https://devguide.python.org/versions/> | Observed 3.14.4 is in bugfix support; EOL 2030-10 | Python 3.14 receives about 24 months of bugfix releases and then source-only security fixes until approximately October 2030. No Python migration conclusion is inferred from inventory. |
| .NET lifecycle and release metadata | <https://github.com/dotnet/core/blob/main/release-notes/10.0/releases.json> | .NET/ASP.NET Core 10.0.9, SDK 10.0.301, LTS to 2028-11-14 | Context7 official release metadata is the pinned evidence. Runtime, ASP.NET Core and EF Core stay major-aligned; quarterly refresh handles a newer serviced patch. |
| ASP.NET Core IIS hosting | <https://learn.microsoft.com/en-us/aspnet/core/host-and-deploy/iis/> | ASP.NET Core Module V2 and hosting bundle follow .NET major | In-process single-file deployment is unsupported; the profile requires a reviewed folder or out-of-process model. |
| Prisma 7 | <https://www.prisma.io/docs/orm/more/upgrade-guides/upgrading-versions/upgrading-to-prisma-7> and <https://github.com/prisma/prisma/releases/tag/7.8.0> | Prisma 7.8.0 preferred; Prisma 5.22.0 sunset | Prisma 7 requires Node ^20.19, ^22.12 or ^24, TypeScript >=5.4, `prisma-client` output and a driver adapter. Upstream has no fixed EOL table, so null means unknown, not indefinite support. |
| EF Core providers | <https://learn.microsoft.com/en-us/ef/core/providers/> | EF Core 10 stays same major as Npgsql EF provider 10 | Microsoft warns providers typically do not work across major versions. Npgsql exact 10.0.3 metadata is from the official NuGet feed. |
| Npgsql EF provider | <https://www.nuget.org/packages/Npgsql.EntityFrameworkCore.PostgreSQL/10.0.3> | 10.0.3 preferred with EF Core 10 | Package major compatibility is necessary but not sufficient; PostgreSQL 18 still needs project integration tests. |
| PostgreSQL lifecycle | <https://www.postgresql.org/support/versioning/> | 18.4 preferred; 16.14 supported | PostgreSQL supports each major for five years and recommends the current minor. Major adoption requires its own backup/restore/rollback Change. |
| SQLite release and WAL | <https://sqlite.org/changes.html>, <https://sqlite.org/wal.html>, <https://sqlite.org/backup.html> | SQLite 3.53.3 preferred only in small embedded profile | Same-host local filesystem, one writer, bounded contention, online backup and restore drill are mandatory. SQLite publishes no fixed EOL schedule. |
| Docker Engine | <https://docs.docker.com/engine/install/> | Engine 29.7.1 preferred | Official install docs expose exact package pins and Ubuntu architecture support; packages and repository metadata require offline verification. |
| Docker Compose | <https://github.com/docker/compose/releases/tag/v5.1.4> | Compose 5.1.4 preferred | Official release assets include checksums, provenance and SBOM. Image resolution must retain digest identity. |
| Node OCI image | <https://hub.docker.com/_/node> | `node:24.18.0-bookworm-slim@sha256:6f7b…1452d` | Read-only official registry inspection on 2026-08-02 returned the multi-platform index and docker-node revision; catalog requires tag plus digest and offline attestations. |
| NGINX | <https://nginx.org/en/download.html> | stable 1.30.4 preferred; observed 1.28.3 is legacy | The official download page lists 1.30.4 as stable and 1.28.3 under Legacy versions. Upstream has no fixed EOL date, so security/monthly review remains mandatory and remediation requires a separate proxy/server Change. |
| Next.js | <https://nextjs.org/blog> and <https://nextjs.org/support-policy> | 16.2.11 Active LTS preferred; 14.2.33 prohibited | Vercel's July 2026 security release identifies the exact patched Active LTS. Context7 v16.2 docs require Node >=20.9, React >=18.2 and TypeScript >=5.1; official policy now marks 14.x unsupported, so migration Issues or exceptions cannot make it an allowed transition. |
| React | <https://react.dev/versions> | 19.3.0 preferred candidate for compatible projects | Framework peer compatibility is project-owned; catalog presence never authorizes a Next.js/application upgrade. No fixed upstream EOL. |
| TypeScript | <https://www.typescriptlang.org/docs/handbook/release-notes/typescript-6-0.html> | 6.0.2 preferred candidate | Prisma minimum is satisfied, but TypeScript 6 deprecations require application typecheck and framework tests. No fixed upstream EOL. |
| npm CLI | <https://docs.npmjs.com/cli/v11> and <https://docs.npmjs.com/about-npm-versions> | npm 11.19.0 preferred with Node 24; 10.8.2 observed | `npm ci` enforces package-lock parity; exact package-manager identity and mirrored integrity metadata are required. npm publishes no fixed CLI EOL schedule. The observed npm 10.8.2 must be reviewed together with its EOL Node 20 host runtime. |
| PM2 | <https://github.com/Unitech/pm2> | 7.0.3 observed; no catalog adoption conclusion | Upstream documents updating to the latest release but publishes no fixed support/EOL table. Exact installed metadata is retained and reviewed quarterly; Node compatibility must be validated in a separate application/server Change. |
| Gitea | <https://github.com/go-gitea/gitea/releases/tag/v1.26.4> | 1.26.4 observed from the live API and confirmed as an official upstream release | Upstream publishes the exact signed release but no fixed per-patch EOL date. Security and release review continues; no Gitea upgrade, restart or configuration mutation occurred. |

All version conclusions above are catalog candidates approved only for profile/validator use in this
Change. They are not evidence that any application, image, database or server has migrated or deployed.

## Context7 query ledger

Each row was resolved before querying and each query covered one concept. Official page readback did
not replace Context7; it resolved exact release-table values or extraction conflicts.

| Component | Resolved Context7 library ID | Separately queried concept |
|---|---|---|
| Ubuntu | `/canonical/ubuntu.com` | LTS release lifecycle and support dates |
| Windows Server | `/websites/learn_microsoft_en-us_windows-server` | Windows Server 2025 lifecycle/build support |
| IIS | `/websites/learn_microsoft_en-us_iis` | Windows role installation and ASP.NET Core hosting boundary |
| Node.js | `/nodejs/nodejs.org` | LTS/Current lifecycle and production eligibility |
| Python | `/python/cpython` | Python 3.14 bugfix/security lifecycle and five-year support model |
| .NET / ASP.NET Core | `/dotnet/core` | .NET 10 serviced runtime/SDK metadata and LTS end date |
| Prisma | `/prisma/web` | Prisma 7 Node/TypeScript/generator/adapter compatibility |
| EF Core | `/dotnet/entityframework.docs` | provider major-version compatibility and support policy |
| Npgsql EF provider | `/npgsql/efcore.pg` | EF Core/PostgreSQL provider compatibility; exact package read back from official NuGet |
| PostgreSQL | `/websites/postgresql_current` | supported majors, current minor and five-year lifecycle |
| SQLite | `/websites/sqlite_docs` | WAL same-host/one-writer and online backup constraints |
| Docker Engine | `/docker/docs` | exact-version install, supported Ubuntu releases and digest pinning |
| Docker Compose | `/docker/compose` | digest resolution and plugin release artifacts |
| NGINX | `/websites/nginx` | stable/mainline selection and exact package pinning |
| Next.js | `/vercel/next.js/v16.2.9` | v16 Node/React/TypeScript compatibility and upgrade guidance; exact 16.2.11 security patch read back from Vercel's official release blog |
| React | `/react/react/v19.2.7` | current stable release semantics |
| TypeScript | `/microsoft/typescript/v6.0.2` | current stable toolchain and 6.0 migration constraints |
| npm | `/npm/cli` | v11 Node engine support, `npm ci` and exact package-manager pinning |
| PM2 | `/unitech/pm2` | upstream update guidance and absence of a fixed release/EOL table |
| Gitea | `/go-gitea/gitea` | release support policy and exact-release review boundary |

## Server inventory supplement

The 2026-08-03 supplement used sanitized host-path `orb -m <machine> -u benque` probes after
managed-sandbox access failed. Because the same read-only probes succeeded on the host path, the
earlier result is classified `SANDBOX_PATH_BLOCKED`, not as an OrbStack or server outage. No VM
lifecycle, service, package, application, schema or database mutation was authorized or performed.

| Observed component | Assets | Retrieved / review | Compatibility or gap conclusion |
|---|---|---|---|
| Ubuntu 26.04 LTS, `aarch64` | `gitea-ci`, `prod-sim` | 2026-08-03 / 2026-11-03 | Active upstream LTS, but still a prohibited catalog candidate until 26.04.1 and platform soak evidence. As-built does not mean approved. |
| Node 20.20.2 + npm 10.8.2 | `gitea-ci`, `prod-sim` | 2026-08-03 / 2026-11-03 | Node 20 is EOL; npm has no fixed EOL. A separate runtime/server Change must select and test a supported Node/npm pair. |
| Python 3.14.4 | `gitea-ci`, `prod-sim` | 2026-08-03 / 2026-11-03 | Supported in bugfix phase; upstream month-level EOL is 2030-10. |
| PostgreSQL 18.4 | `gitea-ci`, `prod-sim` | 2026-08-03 / 2026-11-03 | Exact client/server minor matches the preferred catalog candidate. This is inventory only and proves no schema or application compatibility. |
| NGINX 1.28.3 | `gitea-ci`, `prod-sim` | 2026-08-03 / 2026-11-03 | Officially listed as legacy; remediation is a separate proxy/server Change with rollback and service validation. |
| PM2 7.0.3 | `gitea-ci`, `prod-sim` | 2026-08-03 / 2026-11-03 | Upstream fixed EOL is unknown. Review quarterly and validate with the selected Node LTS; inventory does not authorize application or daemon changes. |
| Gitea 1.26.4 | `gitea-ci` | 2026-08-03 / 2026-11-03 | Live API exact version matches the official signed release. Inventory does not establish deployment or upgrade completion. |

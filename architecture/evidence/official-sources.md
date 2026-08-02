# Official source and compatibility evidence

Retrieved: 2026-08-02 · Next review: 2026-11-02 · Method: one Context7 query per concept,
official/upstream readback where lifecycle or exact release metadata required.

| Concept | Official/upstream source | Catalog conclusion | Compatibility evidence / conflict handling |
|---|---|---|---|
| Ubuntu lifecycle | <https://documentation.ubuntu.com/release-notes/24.04/> and <https://wiki.ubuntu.com/Releases> | 24.04.4 preferred; 26.04 prohibited candidate | Context7's Ubuntu page extraction conflated lifecycle columns, so Canonical release notes were read back for exact 2029-05-31 standard-support end and the release table for point-release/long-tail dates. Month-only EOL is normalized to its final calendar day. 26.04 remains blocked pending first point release plus AISoftPlatform soak. |
| Windows Server lifecycle | <https://learn.microsoft.com/en-us/lifecycle/products/windows-server-2025> | Server 2025 build family preferred; mainstream 2029-11-13, extended 2034-11-14 | Product lifecycle is authoritative when the container base-image table shows slightly different servicing dates. Build 26100 comes from the official base-image table. |
| IIS role | <https://learn.microsoft.com/en-us/windows-server/administration/server-core/server-core-roles-and-services> | `Web-Server` feature manifest pinned to Windows Server 2025 | IIS is an OS role, not an independently supported semver product. Lifecycle inherits the OS; ASP.NET Core Module/hosting bundle is validated with .NET. |
| Node lifecycle | <https://nodejs.org/en/about/previous-releases> | Node 24.18.0 preferred; Node 22.22.3 sunset; Node 26 Current not production-approved | Production applications use Active/Maintenance LTS only. Node 24 ends April 2028; Node 22 ends April 2027. |
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
| NGINX | <https://nginx.org/en/download.html> | stable 1.30.4 preferred | Mainline 1.31.3 is not the default. Upstream has no fixed EOL date, so security/monthly review remains mandatory. |
| Next.js | <https://nextjs.org/blog> | 16.2.11 Active LTS preferred | Vercel's July 2026 security release identifies the exact patched Active LTS. Context7 v16.2 docs require Node >=20.9, React >=18.2 and TypeScript >=5.1; Next 14 adoption is a separate framework migration. |
| React | <https://react.dev/versions> | 19.3.0 preferred candidate for compatible projects | Framework peer compatibility is project-owned; catalog presence never authorizes a Next.js/application upgrade. No fixed upstream EOL. |
| TypeScript | <https://www.typescriptlang.org/docs/handbook/release-notes/typescript-6-0.html> | 6.0.2 preferred candidate | Prisma minimum is satisfied, but TypeScript 6 deprecations require application typecheck and framework tests. No fixed upstream EOL. |
| npm CLI | <https://docs.npmjs.com/cli/v11> | npm 11.19.0 preferred with Node 24 | `npm ci` enforces package-lock parity; exact package-manager identity and mirrored integrity metadata are required. No fixed upstream EOL. |

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

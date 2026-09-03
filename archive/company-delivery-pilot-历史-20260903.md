# company-delivery pilot 历史（NewEmaint 公司两 VM 交付，截至 2026-09-03）

> **归档资料：** 本文件逐字收录 Issue #237（2026-09-03）从 `README.md`、`07-内网与生产平移路线.md`、
> `company-delivery/README.md` 与 `company-delivery/runbook.md` 迁出的 NewEmaint pilot 专属段落。它们是
> 已经发生的历史证据，不是当前配置、命令、权限或 live 环境的事实源。
>
> **原路径链接兼容说明：** `company-delivery/` 目录、`runbook.md`、`README.md`、`schema/`、`templates/`、
> `bin/` 与 `compatibility/newemaint-company-pilot-v1.json` 的路径全部**不变**，仍在原位；它们自 #237 起是
> 去项目名的「公司两 VM 离线 handoff operator 参考实现」。指向这些路径的旧链接不会悬空。
> `compatibility/newemaint-company-pilot-v1.json` 的字节亦未改动：它是 pilot 项目数据，归属已由 NewEmaint
> 仓承接 Issue 接管（编号见下），平台仓保留副本只因 operator `1.2.0` builder（`codex/runtime/
> aisoft_company_delivery/bundle.py` `COMPATIBILITY_PATH`）与 `aisoft-inbound-sync@newemaint.timer` unit 名
> 仍由 runtime 绑定；删除副本与参数化由后续平台 Issue 处置。
>
> pilot 当前归属：NewEmaint 仓（`admin/NewEMaint`）承接 Issue **[#75](http://gitea-ci.orb.local:3000/admin/NewEMaint/issues/75)**。

## 1. pilot 身份与 operator 演进（快照）

- 项目：NewEmaint；物理放置：两台公司 Linux VM（`gitea-ci` role=`scm-ci`、`appserver` role=`appserver-prod`）
  + 本地 OrbStack NewEmaint DockerLab（role=`appserver-test`），不新增第三台公司 VM。
- fixed target ID：`newemaint-prod`（Stage 90/100 的 `aisoft-docker-release-gate <action> newemaint-prod <full-sha>`）。
- operator 演进：`1.0.1`（#120 建立 runbook；#124 对 repo-external exact NewEmaint release 运行本地只读
  deterministic handoff regression，PASS 但不生成 Stage evidence）→ `1.1.0`/`1.1.1`（#126/#128 versioned
  contracts 与 preflight 修正）→ `1.2.0`（#130 `greenfield-isolated-install`：inventory v3、transition v2，
  只验证 `scm-ci` 独立 `aisoft-gitea` candidate）。
- compatibility matrix `newemaint-company-pilot-v1.json`（`matrix_revision` `2026.08.4`）`stage_map` 快照：
  `00` PASS、`10-scm-ci` PASS、`10-appserver-prod` PASS、`20` PASS、`30`/`40`/`50` NOT RUN；
  `legacy_observation` NOT RUN。这些 PASS 是 pilot 当时以旧 operator 留下的证据，runbook 已声明不能投影为
  `1.2.0` Stage 00/10 PASS。
- 公司侧 Stage 00–110 与安装：截至迁出时全部 `NOT RUN`。

## 2. 来源：`README.md` §1「当前状态」（2026-09-03 迁出）

- 🟡 NewEmaint 公司交付 pilot（Issue #120）：提供 versioned/checksum-pinned operator bundle、两台公司 Linux VM 的脱敏 inventory、Stage 00–110 人工 runbook 与 strict evidence；真实 release handoff、公司 Gitea/Runner/Registry、backup/restore、AppServer 和 production 全部保持 `NOT RUN`

## 3. 来源：`README.md` §2（2026-09-03 迁出）

NewEmaint pilot 的物理部署固定为**两台公司 Linux VM + 本地 OrbStack DockerLab**：公司
`gitea-ci/scm-ci` 承担 Gitea、入站、Runner、Registry/cache、artifact-only verification 与受控编排；
本地 DockerLab 承担 `appserver-test`；公司 `appserver/appserver-prod` 承担 runtime、PostgreSQL、Nginx
与 fixed target。公司只消费本地已验证的 exact `docker-release/v2` bytes；公司要求内网重建但没有
隔离测试环境时固定 `BLOCKED`。执行合同见
[`company-delivery/runbook.md`](../company-delivery/runbook.md)，本仓库或 PR 状态不代表公司已执行。

（`README.md` §6 快速入口表原句：「NewEmaint pilot 固定为本地 OrbStack DockerLab，历史 `gitea-ci:8091`
已在 Issue #21 收口，不得作为当前入口」。）

## 4. 来源：`07-内网与生产平移路线.md` §5.1（2026-09-03 迁出）

NewEmaint pilot 是项目级物理放置例外，不改变三 role capability：本地 OrbStack DockerLab 先验证 exact
`docker-release/v2` bytes，再由 versioned + checksum-pinned operator bundle 受控搬入公司；公司
`scm-ci` 只做 artifact-only verification，公司 `appserver-prod` 只经 fixed target gate 消费相同 bytes。
公司要求内网重建但没有隔离测试环境时固定 `BLOCKED`。

该 pilot 的 Gitea 建设采用 operator `1.2.0` 的 `greenfield-isolated-install`：新 systemd
Gitea/PostgreSQL 仅使用固定的独立 `aisoft-gitea` namespace 与 loopback candidate tuple；Stage 10
inventory v3 不读取 legacy Docker/HTTP，Stage 20 transition v2 不绑定 legacy health/version/baseline。
`legacy migration/phase-out`、DNS/TLS、反向代理、正式仓库导入与 traffic cutover 都是后续独立 Change；
当前 1.2.0 公司 Stage 00–50 与安装全部 `NOT RUN`。逐阶段合同见
[company-delivery runbook](../company-delivery/runbook.md)。

## 5. 来源：`company-delivery/README.md`（2026-09-03 迁出）

本目录是 Issue #120/#126/#128/#130 的 versioned、checksum-pinned、纯人工 operator workflow。当前 operator
`1.2.0` 准备 NewEmaint 从本地
OrbStack DockerLab 验证过的 exact `docker-release/v2` bytes 搬运到公司两台 Linux VM；它不是安装记录、
部署记录或公司环境验收结果。

（尾段）#124 已对 repo-external exact NewEmaint release 运行本地只读
deterministic handoff regression；这不是公司侧 handoff 或部署。公司 VM、公司 Gitea/Runner/Registry、
backup/restore、NewEmaint target 和 production 均为 `NOT RUN`。

## 6. 来源：`company-delivery/runbook.md` 标题、§1 与 §2（2026-09-03 迁出）

原标题：「NewEmaint 公司两 VM 确定性交付 operator runbook」。

§1 原句：「非生产 role=`appserver-test` 继续由本地 OrbStack NewEmaint DockerLab 承担，不新增第三台公司
VM。」；「`scm-ci` … 不得运行 NewEmaint runtime 或业务 DB。`appserver-prod` 只承载
NewEmaint/PostgreSQL/Nginx/fixed target」；approval tuple 原文绑定「Issue/Change `#120`」。

§2 原文：Issue #120 建立了本 runbook；Issue #124 另行批准以 repo-external exact NewEmaint release 运行本地只读
deterministic handoff regression。该 pre-Stage 00 local exact-release regression 已 PASS，但不生成 Stage
evidence，也不是公司侧 handoff、安装或部署；正式搬运包仍须在 #124 人工合并后从 protected `main` exact
SHA 重新生成。公司 Stage 00–110：`NOT RUN`。

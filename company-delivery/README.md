# Company delivery operator bundle

本目录是公司两台 Linux VM 离线 handoff 的 versioned、checksum-pinned、纯人工 operator workflow **参考实现**
（交付形态由项目自行声明与选用，环境级原则见 `skill-for-codex/references/onboarding-runbook.md` §4）。当前
operator `1.2.0` 把本地 OrbStack DockerLab 验证过的 exact `docker-release/v2` bytes 搬运到公司两台 Linux VM；
它不是安装记录、部署记录或任何项目的公司环境验收结果。建立本目录的 pilot（Issue #120/#126/#128/#130）
历史见 [`archive/company-delivery-pilot-历史-20260903.md`](../archive/company-delivery-pilot-历史-20260903.md)。

## 固定拓扑

| 位置 | role | 职责 | 禁止 |
|---|---|---|---|
| 公司 VM `gitea-ci` | `scm-ci` | Gitea、GitHub 入站、PR/CI、Runner、Registry/cache、artifact-only verification、受控编排 | 应用 runtime、业务 DB、production Secret |
| 本地 OrbStack DockerLab | `appserver-test` | exact release 的非生产 deploy/migration/health/rollback | 作为公司 live evidence |
| 公司 VM `appserver` | `appserver-prod` | 应用 runtime、PostgreSQL、Nginx、fixed production target | Gitea、通用 Runner、源码 build、任意 shell 发布 |

公司侧只有两台 VM；`appserver-test` 是保留的 trust role，但位于本地，不要求第三台公司 VM。

## 内容

- [`runbook.md`](runbook.md)：Stage 00–110，每阶段可单独批准、停止和回滚。
- `bin/aisoft-company-delivery`：固定参数的 inventory、contract verification 与 bundle build CLI。
- `schema/`：strict inventory v1/v2/v3、Gitea transition v1/v2、handoff/evidence v1 JSON schema；v1/v2
  inventory 与 transition v1 只用于历史 evidence 兼容读取。
- `templates/`：结构示例；所有 `example` 文件都不是 live evidence。
- `compatibility/<pilot>-company-pilot-v1.json`：pilot 项目的两 VM 拓扑、版本候选和 fail-closed policy matrix。
  它是项目数据，归属项目仓（承接 Issue 见 archive）；平台保留副本只因 builder `1.2.0`（`bundle.py`
  `COMPATIBILITY_PATH`）绑定该路径，属历史证据，不是新项目的默认拓扑。
- 构建后的 `handoff-manifest.json`、`SHA256SUMS`、`.tar.gz.sha256`：full Git SHA 与 exact release bytes 的
  可携带身份。

## Gitea greenfield 隔离安装合同

`greenfield-isolated-install` 只在独立
`aisoft-gitea` namespace 建立候选 systemd Gitea。目标固定为 Gitea `1.26.4`
（`gitea-1.26.4-linux-amd64`，SHA-256
`0faa36d151918f8f7d6e0f3ae67597d1c338583d695add146ac393109d0fc44a`）和 PostgreSQL `18.4`
upstream provenance（SHA-256
`81a81ec695fb0c7901407defaa1d2f7973617154cf27ba74e3a7ab8e64436094`）。新 units 为
`aisoft-gitea.service`、`postgresql@18-aisoft-gitea.service`，只监听候选 loopback
`127.0.0.1:8888` 与 `127.0.0.1:55432`；完整 paths/identity 以 compatibility matrix 为准。

Stage 10 使用 inventory v3，只验证 candidate 固定端口、路径、unit、tools 与 automation；collector 不接收
legacy port、不运行 legacy Docker/HTTP probe，也不输出 legacy presence、health、version 或 baseline。Stage 20
使用 transition v2，绑定两份 inventory、已验证的 operator 1.2.0 handoff/source SHA 与 PostgreSQL OS
package-set SHA-256 manifest；greenfield 路径的 Stage 30/40 必须保持 `NOT RUN`，Stage 50 仅以前后 candidate
identity/health 作为 prerequisite。legacy Docker container、image、volume、network、database、configuration、
port、repository 和 service lifecycle 均禁止修改，且 legacy observation 固定为 `NOT RUN`。SSH、Runner、timer、
Actions auto deploy、production gate、DNS/TLS、reverse proxy 与 repository import 初始全部 disabled 或
`NOT RUN`。

新实例未来只承载新仓库；legacy migration/phase-out、traffic cutover 与旧实例退役必须另建 Change。本仓库
不会把旧 operator 的公司 evidence 投影到新合同。`1.0.1`、`1.1.0`、`1.1.1` Stage 00 与既有
Stage 10 inventory 仅是历史 evidence，不能作为 `1.2.0` Stage 00/10 `PASS`；`appserver-prod` 仍保持
`NOT RUN`，直到获得独立人工批准。

## 构建边界

builder 只接受 absolute clean repository root、与 `HEAD` 相同的完整 40 位 source SHA、已通过
artifact-only verification 的 `docker-release/v2` release root、空的 mode `0700` 输出目录、显式 UTC
timestamp 和 allowlisted source transport。示意命令中的占位符必须由人工从已批准记录逐字替换；不得把
Secret 放入 argv：

```bash
company-delivery/bin/aisoft-company-delivery build-bundle \
  --repository-root /approved/aisoft-platform \
  --source-sha <40-char-source-sha> \
  --release-root /approved/<project>/releases \
  --release-id <40-char-release-sha> \
  --output-directory /approved/empty-mode-0700-output \
  --created-at <YYYY-MM-DDTHH:MM:SSZ> \
  --source-transport approved-bundle
```

同一组输入重复构建必须得到 byte-identical archive checksum。真实 release bytes 缺失时保持
`NOT RUN`；不得用 repository fixture 或 local fake bundle 作为公司 handoff。

`created-at` 只控制确定性 archive 的时间字段，不是安全校验时钟。每次 build 与 verify 都按运行时 UTC
日期检查 architecture exception 是否仍有效，禁止通过回填时间绕过过期例外。builder 在写 manifest 前
扫描全部 operator、dependency 与 release 的非 archive payload：普通文本只豁免精确的外部引用语法，顶层
concrete Secret-like 内容仍返回固定 `SENSITIVE_CONTENT`、no-echo 并清理部分输出。`images.tar` 在
artifact-only identity/checksum/outer graph 验证后作为 opaque immutable payload 原字节搬运，不解压、不读取
config/layer，也不声称其内部无 Secret。该风险由 release owner 与公司人工授权承担；规则按已验证 artifact
类型统一生效，不使用 release SHA、image digest 或内部路径特判。

## 验证与 evidence

解包前先校验相邻 archive checksum，解包时固定 `umask 077`；解包后调用 `verify-handoff`，它会重新校验
handoff、逐文件摘要、完整 `SHA256SUMS`、compatibility identity 和 release contract，同时保持
`docker_calls=0`、`target_facts=NOT_READ`。

每个批准阶段只写一个 evidence JSON，并在回流前调用 `verify-evidence`。结果只能是 `PASS`、`FAIL`、
`BLOCKED` 或 `NOT RUN`；必须分别记录 `observed`、`changed`、`verified`、`pending`。不得提交或传输
Secret、原始日志、主机名/IP、用户名、配置内容、认证 header 或 credential path。

完整操作合同见 [`runbook.md`](runbook.md)。历史证据：#124 曾对 repo-external exact pilot release 运行本地只读
deterministic handoff regression（见 archive）；这不是公司侧 handoff 或部署。各项目的公司 VM、公司
Gitea/Runner/Registry、backup/restore、fixed target 和 production 进度由项目仓记录；本仓库对任何项目均不构成
公司侧 `PASS`。

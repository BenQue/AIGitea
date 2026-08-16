# Company delivery operator bundle

本目录是 Issue #120 的 versioned、checksum-pinned、纯人工 operator workflow。它准备 NewEmaint 从本地
OrbStack DockerLab 验证过的 exact `docker-release/v2` bytes 搬运到公司两台 Linux VM；它不是安装记录、
部署记录或公司环境验收结果。

## 固定拓扑

| 位置 | role | 职责 | 禁止 |
|---|---|---|---|
| 公司 VM `gitea-ci` | `scm-ci` | Gitea、GitHub 入站、PR/CI、Runner、Registry/cache、artifact-only verification、受控编排 | NewEmaint runtime、业务 DB、production Secret |
| 本地 OrbStack NewEmaint DockerLab | `appserver-test` | exact release 的非生产 deploy/migration/health/rollback | 作为公司 live evidence |
| 公司 VM `appserver` | `appserver-prod` | NewEmaint runtime、PostgreSQL、Nginx、fixed production target | Gitea、通用 Runner、源码 build、任意 shell 发布 |

公司侧只有两台 VM；`appserver-test` 是保留的 trust role，但位于本地，不要求第三台公司 VM。

## 内容

- [`runbook.md`](runbook.md)：Stage 00–110，每阶段可单独批准、停止和回滚。
- `bin/aisoft-company-delivery`：固定参数的 inventory、contract verification 与 bundle build CLI。
- `schema/`：strict inventory/handoff/evidence V1 JSON schema。
- `templates/`：结构示例；所有 `example` 文件都不是 live evidence。
- `compatibility/newemaint-company-pilot-v1.json`：两 VM 拓扑、版本候选和 fail-closed policy。
- 构建后的 `handoff-manifest.json`、`SHA256SUMS`、`.tar.gz.sha256`：full Git SHA 与 exact release bytes 的
  可携带身份。

## 构建边界

builder 只接受 absolute clean repository root、与 `HEAD` 相同的完整 40 位 source SHA、已通过
artifact-only verification 的 `docker-release/v2` release root、空的 mode `0700` 输出目录、显式 UTC
timestamp 和 allowlisted source transport。示意命令中的占位符必须由人工从已批准记录逐字替换；不得把
Secret 放入 argv：

```bash
company-delivery/bin/aisoft-company-delivery build-bundle \
  --repository-root /approved/aisoft-platform \
  --source-sha <40-char-source-sha> \
  --release-root /approved/newemaint/releases \
  --release-id <40-char-release-sha> \
  --output-directory /approved/empty-mode-0700-output \
  --created-at <YYYY-MM-DDTHH:MM:SSZ> \
  --source-transport approved-bundle
```

同一组输入重复构建必须得到 byte-identical archive checksum。真实 NewEmaint bytes 缺失时保持
`NOT RUN`；不得用 repository fixture 或 local fake bundle 作为公司 handoff。

`created-at` 只控制确定性 archive 的时间字段，不是安全校验时钟。每次 build 与 verify 都按运行时 UTC
日期检查 architecture exception 是否仍有效，禁止通过回填时间绕过过期例外。builder 在写 manifest 前
扫描全部 operator、dependency 与 release payload：普通文本只豁免精确的外部引用语法；`images.tar`
必须先通过现有 Docker/OCI graph 验证，再流式扫描全部 reachable config、metadata、attestation 与 layer
内容。它不 extract、不调用 Docker、不读取 target facts，也不对 outer tar header/padding 做通用 key/value
匹配。命中 concrete Secret-like 内容只返回固定 `SENSITIVE_CONTENT`；archive、compression、JSON 或 inner
member 无法在 8 MiB JSON、200,000 members、2 GiB/member、8 GiB expanded bounds 内安全处理时只返回固定
`SENSITIVE_SCAN_BLOCKED`。两类错误均不回显值、片段、offset 或 inner path，并清理所有部分输出。

## 验证与 evidence

解包前先校验相邻 archive checksum，解包时固定 `umask 077`；解包后调用 `verify-handoff`，它会重新校验
handoff、逐文件摘要、完整 `SHA256SUMS`、compatibility identity 和 release contract，同时保持
`docker_calls=0`、`target_facts=NOT_READ`。

每个批准阶段只写一个 evidence JSON，并在回流前调用 `verify-evidence`。结果只能是 `PASS`、`FAIL`、
`BLOCKED` 或 `NOT RUN`；必须分别记录 `observed`、`changed`、`verified`、`pending`。不得提交或传输
Secret、原始日志、主机名/IP、用户名、配置内容、认证 header 或 credential path。

完整操作合同见 [`runbook.md`](runbook.md)。当前仓库 Change 只运行 local fake tests；公司 VM、公司
Gitea/Runner/Registry、backup/restore、NewEmaint target 和 production 均为 `NOT RUN`。

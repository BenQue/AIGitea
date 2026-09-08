---
issue: 278
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/278
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - schema
  - security
  - external-contract
  - shared-core
depends_on: []
status: approved
branch: change/278-baseline-probe-remediation
created: 2026-09-08
updated: 2026-09-08
---

# Baseline probe remediation 与只读诊断合同

## 目标与原因

修复 `company-platform-baseline/v2` 在真实 `systemctl` 与 Gitea 1.26.4 输出上的两处 fail-closed 表达缺口，同时提供一个独立、profile-bound、可离线审阅的 `company-platform-baseline-diagnostics/v1`。诊断合同只回答“为何既有 probe 无法采用”，不改变 baseline 事实、不补写 PASS、不执行现场整改。

## Acceptance criteria

- **AC-1 v2 版本兼容**：新 collector 发出 `collector_version=2.0.1`，published v2 schema 与 verifier 同时接受 `2.0.0` 和 `2.0.1`；既有 2.0.0 envelope 在使用其原始 binding pins 时仍可离线验证。v1 collector 与 v1 schema 的 exact bytes 不变。
- **AC-2 Gitea 版本输出**：binary probe 只新增接受 `[Gg]itea version <strict-version>`，覆盖现场 `gitea version 1.26.4 built with ...`；必须仍拒绝错误产品名、多行、非数值或超出既有版本格式的输出，不放宽 API version schema。
- **AC-3 systemd transient enablement**：`enabled-runtime` 进入 service closed enum，但 `good()` 只把持久 `enabled + active` 判为 PASS；`enabled-runtime + active` 必须是可观察的 GAP。其它未知状态、异常返回码或超限输出仍为 BLOCKED/probe-unavailable。
- **AC-4 独立诊断 envelope**：新增 `company-platform-baseline-diagnostics/v1` 单文件 Python 3.10+ collector/verifier 与 published closed schema。identity/collect/verify 固定 environment、role、host/source/collector/profile pins，并同时绑定原 baseline evidence UUID 与本轮 fresh v4 diagnostic UUID；receipt 固定 `mutation_authorized=false`。
- **AC-5 selected systemd metadata**：诊断只执行 fixed Gitea unit 的 `systemctl show`，property allowlist 精确为 `LoadState`、`ActiveState`、`SubState`、`Result`、`MainPID`、`ExecMainStatus`。输出仅含 closed enum、`main_pid_present=yes|no` 与有界 exit status；不读取或输出 unit 正文、`ExecStart`、environment、PID 数值或 journal。
- **AC-6 server binding 布尔比较**：诊断只打开固定 `/etc/aisoft/gitea/app.ini`，要求 non-symlink regular file、大小不超过 65536 bytes、group/other 不可写；只解析 `[server]` 的 `PROTOCOL`、`HTTP_ADDR`、`HTTP_PORT`，输出仅为 `section_present`、`protocol_http`、`http_addr_matches_profile`、`http_port_matches_profile` 四个 yes/no，不输出任何 key/value、路径、正文、解析异常、其它 section 或 Secret。
- **AC-7 特权 UFW 归一化**：诊断程序不调用 `sudo`；由未来另行授权的现场操作员决定是否以批准身份运行。程序仅执行 `/usr/sbin/ufw status verbose`，清空继承环境并丢弃 stderr，只输出 `active`、`default_deny_incoming`、`rule_count` 与 closed status。权限不足、格式异常或失败保持 BLOCKED，不得把空 stdout 投影成 inactive、false 或零规则，也不得输出原始规则/IP/网段。
- **AC-8 固定目标与零泄露**：所有 subprocess 均为 argv allowlist、无 shell、stdin=`DEVNULL`、4 秒 timeout、65536-byte 上限和固定 `LANG/LC_ALL/PATH`；错误只输出稳定 code/type enum。schema、stdout、stderr、manifest 和错误路径的 Secret sentinel 扫描为零；不发 HTTP、不扫描端口、不读日志/credential/environment/数据库/目录内容，不写现场文件。
- **AC-9 review bundle**：提供只从 exact platform Git commit materialize diagnostic collector/schema/docs、并注入一个 canonical project profile 的 builder；新 output directory 必须为 `0700`、文件 `0600`，manifest 固定每个文件 SHA-256，拒绝已存在目录、非 canonical profile、Git/object/hash drift。builder 仅在开发侧运行，现场只接收审阅后的 bytes。
- **AC-10 真实边界**：fixture 覆盖成功、权限不足、连接/文件不可用、畸形/超限输出、digest/host/profile/parent UUID drift，并连续两次通过 targeted tests。verification 分开记录 source/local、review bundle 与 installed/company live；本 Issue 不安装、不运行公司诊断、不修改 Gitea service/UFW/PostgreSQL/Runner/数据库，也不修改 NewEMaint #79 pin。

## 接口、数据与兼容性影响

`aisoft_company_baseline_v2.py` 的 contract 仍为 `company-platform-baseline/v2`，但 collector version 递增到 2.0.1。schema 新增 `enabled-runtime` 并保留 2.0.0 verifier compatibility；source digest 与 published schema digest 会改变，任何项目重新采集都必须重新 pin，不能复用旧 collector digest 或 UUID。

新增诊断 CLI：

```text
aisoft_company_baseline_diagnostics_v1.py identity
aisoft_company_baseline_diagnostics_v1.py collect <binding pins> --baseline-evidence-id UUID
aisoft_company_baseline_diagnostics_v1.py verify <same binding pins> --baseline-evidence-id UUID
```

诊断 profile 复用 v2 的 canonical `baseline-profile.json` 和 profile schema。诊断输出不合并回 baseline envelope，也不能通过 `supplement` 覆写 host probe；它只形成带 checksum 的独立说明性 evidence。

## 风险与回滚约束

source 可由唯一 PR 普通 revert。2.0.0/2.0.1 verifier compatibility 和 v1 exact hash 测试防止回滚破坏历史证据。诊断 collector 不包含 mutation entrypoint，也不调用 `sudo`；因此本 Issue 没有现场状态回滚。若诊断包输出边界或 profile binding 无法证明，保持 NOT RUN/BLOCKED，不发布 bundle。

## 非目标

- 不把 `enabled-runtime` 归一化为 `enabled`，不执行 `systemctl enable`。
- 不修复或重启 Gitea，不查找其它端口，不访问 legacy 8080，不安装/注册 Runner。
- 不读取/输出完整 unit、`ExecStart`、`app.ini` 正文、journal、credential、environment、数据库、数据目录内容或 UFW 原始规则。
- 不审核 UFW 允许网段是否正确；rule count 不能替代 owner review。
- 不创建 backup/restore、repository/protection/sync/Runner current 事实，不修改 NewEMaint #79、PR #81 或公司服务器。
- 不安装本 Issue source，不执行生成的现场包，不合并最终 PR。

## 未决问题

无。任何扩大 key/property allowlist、读取日志、现场提权执行或 mutation 都必须另行更新合同并取得授权。

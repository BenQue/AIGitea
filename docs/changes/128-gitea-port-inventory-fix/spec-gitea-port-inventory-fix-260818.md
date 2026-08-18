---
issue: 128
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/128
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - external-contract
  - shared-core
  - deployment
  - compatibility
  - reliability
  - platform-governance
depends_on:
  - 126
status: approved
branch: change/128-gitea-port-inventory-fix
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/129
created: 2026-08-18
updated: 2026-08-18
---

# Spec：Stage 10 固定端口 8888 与 inventory 兼容修复

## 目标与现场事实

修正 company-delivery 1.1.0 在公司 `scm-ci` 首次 Stage 10 中暴露的真实兼容缺口，同时保持现有
greenfield-parallel-replacement 安全边界：legacy Docker Gitea 继续使用人工批准端口 `8080`，新 binary +
systemd Gitea 使用唯一固定 target `127.0.0.1:8888`，PostgreSQL 仍使用 `127.0.0.1:55432`。既有
`3000` listener 属于其它应用，不能停止、重配、识别进程或纳入新 Gitea namespace。

本 Change 只交付 operator `1.1.1` source、portable bytes、文档与本地 deterministic tests。它不访问公司
内网，不更改已生成的 1.1.0 Stage 10 `BLOCKED` inventory，不运行 Stage 10 `appserver-prod`，也不授权任何
Gitea/PostgreSQL/Runner/service mutation。

## 固定端口与版本合同

| 对象 | 固定值 | 规则 |
|---|---|---|
| legacy Docker Gitea | 人工批准的 loopback port，本次为 `8080` | 仅作 `docker ps publish=<port>` 与固定 loopback API 输入，不写入 target |
| greenfield Gitea | `127.0.0.1:8888` | collector 只探测 8888；调用方不得覆写；preflight 必须 free |
| greenfield PostgreSQL | `127.0.0.1:55432` | 保持 Issue #126 合同 |
| operator | `1.1.1` | 1.1.0 Stage 00/10 evidence 不可复用；必须重新 build、Stage 00 和逐 scope Stage 10 审批 |

`FIXED_GITEA_TARGET`、transition schema/template、compatibility matrix、README/runbook 与测试必须对上述值完全
一致。仓库中其它 Gitea（例如 OrbStack 平台自身）的 `127.0.0.1:3000` 不得被机械替换。

## systemd 状态合同

### Generic unit normalization

collector 对每个固定 unit 仍只执行 `systemctl is-enabled <unit>` 与 `systemctl is-active <unit>`，不执行
`show`、`cat`、`status`、`journalctl` 或全量枚举。组合归一化规则：

| raw enabled | raw active | sanitized pair | 含义 |
|---|---|---|---|
| `not-found` | `not-found` | `not-found/not-found` | confirmed missing |
| `not-found` | `inactive` | `not-found/not-found` | Ubuntu missing-unit 等价形态 |
| 其它 allowlisted value | allowlisted value | 原 pair | 不扩大语义 |
| 任一 unknown/非 allowlist | 任一值 | 含 `unknown` | BLOCKED |

只有 enabled probe 已确认 `not-found` 时，才允许把 active 的 `inactive` 归一化为 `not-found`。不得把
`disabled/inactive`、`masked/inactive`、`static/inactive` 或任何 active/failed 状态投影为 missing。

### Candidate preflight

- `aisoft-gitea.service` 是 custom target，必须为 normalized `not-found/not-found`。
- `postgresql@18-aisoft-gitea.service` 可为 `not-found/not-found`，或在 port 55432 free、
  `/var/lib/postgresql/18/aisoft-gitea` absent/expected-empty 时为 `disabled/inactive`。
- PostgreSQL pair 的 `enabled/*`、`static/*`、`masked/*`、`disabled/active|failed|unknown` 等均 BLOCKED。
- post-install 合同不变：两个 target unit 都必须 `enabled/active`。
- optional host `gitea`/`act_runner` tool 只有对应 generic unit confirmed missing 时才能投影为 `ABSENT`。
- inbound sync timer 只有 `disabled/inactive` 或 normalized missing 才安全。

## Legacy health 脱敏诊断

legacy `GET /api/v1/version` 仍固定 loopback、3 秒 timeout、最多读取 4097 bytes，且只接受 status 200 与唯一
`{"version":"x.y.z"}` JSON。inventory `legacy.reason` 扩展为以下固定枚举：

- `http-status-3xx`
- `http-status-4xx`
- `http-status-5xx`
- `request-failed`
- `response-invalid`
- 原有 Docker presence、sensitive-output 与 version-unrecognized 固定 reason

不得保存精确 status code、reason phrase、header、Location、body、URL、异常文本或认证内容。非 200 的
health 仍为 `unhealthy`，request failure/invalid body 的 health 为 `unknown`；全部保持 Stage 10 BLOCKED。若 body
命中 sensitive scanner，优先使用 `sensitive-output-rejected`，不再细分。

## Acceptance criteria

- [ ] **AC-1 Fixed target**：company-delivery 的唯一 greenfield HTTP target 为 `127.0.0.1:8888`；legacy
  8080 保持 typed approval input；非 company-delivery 3000 references 不变。
- [ ] **AC-2 Port behavior**：`3000=occupied,8888=free,55432=free` 可满足候选端口 preflight；
  `8888=occupied|unknown` 精确产生 `CANDIDATE_PORT_STATE_GITEA_HTTP`。
- [ ] **AC-3 systemd normalization**：仅 `not-found/inactive` 归一化为 missing；optional tools、timer 与 custom
  candidate unit 正确消费 normalized pair；unsafe/unknown combinations fail closed。
- [ ] **AC-4 PostgreSQL template**：preflight 只在 fixed target `disabled/inactive`、port free、data resource
  absent/expected-empty 时接受已安装 template；post-install 仍要求 enabled/active。
- [ ] **AC-5 Legacy health**：3xx/4xx/5xx、request failure、invalid/sensitive/oversized/duplicate JSON 都生成固定
  sanitized reason；raw body/header/exception/status code 不落盘、不回显。
- [ ] **AC-6 Strict validators**：runtime validator 与 inventory/transition JSON schemas 接受新的 exact safe
  combinations/enum，并拒绝 tampered target/version、宽松 unit pair 和 unknown value。
- [ ] **AC-7 Portable 1.1.1**：VERSION、transition operator const、templates、compatibility、runbook 与 bundle
  全部绑定 1.1.1；deterministic dual build 的 archive SHA 相同，tamper/no-secret tests 通过。
- [ ] **AC-8 Governed delivery**：唯一 readable branch/docs/PR；本地 focused/full/smoke/schema/diff/review 通过，
  PR body 恰有一行 `Closes #128`，最终停在人工合并闸门。
- [ ] **AC-9 Company boundary**：旧 1.1.0 Stage 10 SCM 保持 `BLOCKED` evidence；Stage 10 appserver 与
  Stage 20–110 全部 `NOT RUN`；没有公司 service、Docker、DB、network、repo 或 Secret mutation。

## 接口、数据与兼容影响

- inventory contract 名称保持 `company-delivery-inventory/v2`，新增 fixed `legacy.reason` enum 并收紧/补充
  candidate service semantics；1.1.0 bytes 仍自行验证其历史 inventory。
- transition contract 名称保持 v1，但 `operator_version` 与 target port 是 exact const，因此 1.1.0 transition
  receipt 不能被 1.1.1 validator 接受。
- CLI 不增加 candidate port 参数；调用方只能传 legacy port，防止现场以任意端口绕过 compatibility target。
- 无数据库 schema/data migration；未来 PostgreSQL cluster 创建仍属于独立 Stage 50 live approval。

## 风险、回滚与非目标

source 回滚为 revert 唯一 PR。新 operator 尚未在公司运行，因此没有 live rollback。若未来 1.1.1 Stage 10
失败，只保留 strict BLOCKED evidence，不安装、不重启、不修复现场。

非目标：不释放 3000；不识别其 owner；不修改 legacy 8080；不读取 Docker inspect/env/log、Gitea config、
repository、DB 或 Secret；不运行 appserver inventory；不安装 Gitea/PostgreSQL/Runner；不创建 Stage 20/50
approval；不把 local tests 或 PR CI 写成 company PASS。

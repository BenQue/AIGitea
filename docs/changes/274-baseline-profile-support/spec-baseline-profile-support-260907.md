---
issue: 274
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/274
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - security
  - schema
  - external-contract
depends_on: []
status: approved
branch: change/274-baseline-profile-support
created: 2026-09-07
updated: 2026-09-07
---

# Digest-bound baseline profile v2 合同

## 目标与原因

提供一个项目无关的只读 baseline collector，使项目仓可以声明其已经批准的 SCM 拓扑，同时继续满足固定探针、脱敏、零现场写入、离线可复核和零 mutation 授权。v2 是新合同；v1 继续作为历史回执的不可变 verifier。

## Acceptance criteria

- AC-1：v1 collector、schema 和行为保持字节兼容；v2 使用独立脚本与 `company-platform-baseline/v2` contract/versioned schemas，不静默升级 v1 envelope。
- AC-2：v2 只读取 collector 同目录固定名 `baseline-profile.json`。文件必须是 UTF-8、单一 canonical JSON 加换行、closed schema，且 SHA-256 与显式 `--profile-sha256` pin 一致；profile 本体和摘要进入 inventory，verify/supplement 可离线重算，任一 drift fail closed。
- AC-3：profile 只接受私网或 loopback IPv4、1–65535 数值端口、固定 Gitea/PostgreSQL 二进制、固定 Gitea unit/storage 及受限 PostgreSQL 18 cluster/unit/storage 对应关系；拒绝 hostname、scheme/URL、public/multicast/link-local/unspecified/broadcast 地址、路径穿越、任意命令、未知字段和不一致 identity。
- AC-4：collector 仅执行 profile 推导出的 systemctl exact unit、binary `--version`、两个 exact `ss` port、两个固定 Gitea GET、两个 metadata-only storage probe 与 UFW summary。HTTP 禁认证、代理和 redirect，timeout/输出有界；不读配置、环境、日志、目录内容、凭据或数据库，不执行 shell/sudo/mutation。
- AC-5：Gitea listener 必须包含 profile 声明的 exact 地址；listener exposure 独立记录，外部接口只有在 operator-reviewed UFW 事实满足时才可采用。PostgreSQL 必须只监听声明的 loopback 地址；二进制/API/server 版本分别与 profile 期望值比较。
- AC-6：v2 继承 current/historical、PASS/GAP/BLOCKED/NOT RUN、24 小时 freshness、backup/restore set、人工 supplement 与 `mutation_authorized=false` 语义。缺关键 current、probe/profile/binding 失败或安全差异保持 BLOCKED_EXTERNAL；非关键已知差异才可 adopt-with-remediation。
- AC-7：发布的 profile/inventory schema 与 CLI 输出逐字节一致；fixture 覆盖 external-interface health、hyphen-free PostgreSQL cluster、错 digest、非 canonical、恶意地址/path/unit、profile/inventory 篡改、命令/HTTP/stat allowlist、Secret 哨兵和 v1 checksum 不变。
- AC-8：只交付 source/local tests 和项目消费说明；不安装 collector、不连接公司主机、不修改 NewEMaint 或 live Gitea/UFW/service/DB/Runner/AppServer。

## 接口、数据与兼容性影响

新增 `aisoft_company_baseline_v2.py`。`identity` 返回 host、collector、profile 三个 SHA-256；`collect/verify/supplement` 在 v1 pins 基础上增加 `--profile-sha256`。`schema` 输出 inventory v2 schema，`profile-schema` 输出 profile v1 schema。v2 inventory 嵌入 profile 对象，使离线验证不依赖目标机文件；profile digest 按 canonical JSON 加单个 LF 的 exact bytes 计算。

profile 不携带凭据、URL、hostname、仓库或应用身份。项目仓负责保存自己的具体 profile、source provenance 和 evidence；平台 README 只提供占位符/中性 fixture。

## 风险与回滚约束

v2 profile 扩大了合法目标集合，但不扩大 probe 类型。所有可变字段先经结构和关系校验，再启动任何子进程或 HTTP。错误只输出稳定 code，不回显被拒数据。源码可普通 revert；v1 字节保留，既有回执继续可验证。现场无 mutation，无 live rollback。

## 非目标

在平台仓保存 NewEMaint 的 IP/cluster/路径；自动发现网络或服务；读取 `app.ini`、environment、journal、credential 或 SQL；安装/升级 PostgreSQL/Gitea；创建仓库、Runner、UFW 规则或部署；改变 `company-delivery` greenfield operator 的 1.3.0 合同。

## 未决问题

无。

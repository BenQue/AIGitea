---
issue: 282
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/282
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - external-contract
  - security
depends_on: []
status: approved
branch: change/282-ufw-format-compat
created: 2026-09-10
updated: 2026-09-10
---

# UFW 格式兼容合同

## 目标与依据

上游 https://sources.debian.org/src/ufw/0.36.2-9/src/backend_iptables.py/ 的 get_default_application_policy 输出 skip/allow/deny/reject；规则使用 %-26s %-12s%-26s。长目标字段与 action 之间只有一个空格。

## 验收标准

- AC-1：四种 New profiles 枚举可解析；不改变默认入站策略的判定，不输出该原始策略。
- AC-2：保留现有规则匹配，补充目标至少26字符且单空格分隔 action 的上游格式；动作闭合枚举和 action 后至少两个空格不放宽。未知/重复/畸形行仍拒绝，不跳过未知行。
- AC-3：采集输出 2.0.1；同一 v2 schema/verifier 仅接受2.0.0/2.0.1，仍核验 exact source/collector/profile/host/UUID、checksum、freshness 和 receipt。旧证据不重新解释、不改写。v1文件原样保留，旧2.0.0包不覆盖，历史校验可继续使用原固定包。
- AC-4：正反例、脱敏哨兵、版本与绑定污染、原 diagnostics/baseline 回归通过；builder 的重复构建/漂移拒绝继续通过。

## 非目标、安全与回滚

不改变探针命令、超时、大小、权限、安全读取、输出字段或协议判断；不修改 builder、CI、治理运行规则；不访问公司主机，不发现场命令，不改服务器或数据库。未知格式仍 BLOCKED。source 可 revert，历史离线包保留。修复并不证明 current B1 已通过。

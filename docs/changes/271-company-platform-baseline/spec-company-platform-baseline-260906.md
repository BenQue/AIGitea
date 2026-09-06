---
issue: 271
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/271
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - security
  - schema
depends_on:
  - 268
status: approved
branch: change/271-company-platform-baseline
created: 2026-09-06
updated: 2026-09-06
---

# 公司平台只读接管合同

## 目标与原因

把已存在的公司 Gitea 从历史线索转成可审核的 current inventory。运维人员需要一次运行获得脱敏结果；审核者需要区分历史与现场、已知差异与证据不足；B2/B3 需要明确采用候选和待决项。

## Acceptance criteria

- AC-1：采集前校验 environment=company-scm-ci、role=scm-ci、批准的主机 SHA-256、source SHA、collector SHA-256 和 evidence UUID；stdout 回执绑定所有身份。公司侧零文件写入（包括 bytecode），无 sudo、安装或 mutation。
- AC-2：固定采集 Gitea/PostgreSQL systemd enabled/active、二进制版本、仅 8888/55432 监听、Gitea health/version、存储/权限元数据、UFW 摘要、Runner unit；备份/隔离恢复、外部访问、认证、ACL、公司 repo/protection/Runner 注册/sync 状态使用绑定本轮身份与时间的人工审核脱敏记录。无记录为 NOT RUN，不以二进制版本替代 server 实际版本。
- AC-3：严格 inventory/schema/evidence；current 与 historical 分开；每项状态只为 PASS/GAP/BLOCKED/NOT RUN；网络、认证、ACL、对象存在分别列项。未知字段、重复键、类型错误、超限/含不受控文字、过期或不匹配证据均拒绝且不回显输入。
- AC-4：决定只取 current evidence；缺任一项当前证据或关键安全/健康/恢复差异为 BLOCKED；非关键已知差异为 adopt-with-remediation；全部满足为 adopt。结论始终不授予 mutation，不提供 reinstall/upgrade 动作。
- AC-5：stdout envelope 含 inventory canonical JSON checksum 和验证回执；离线可复核 pin/主机/UUID/checksum/状态语义。提供 B2/B3 决策卡及每段至多 50 行的用户检查块。受控记录不含任意路径、URL、原始日志或配置。
- AC-6：无主机访问或版本化采集器时稳定 BLOCKED_EXTERNAL/NOT RUN；本地 mock 重复运行与负向测试证明命令/输出边界，不能冒充公司现场重复运行。B2/B3 必须依赖 current 基线、#270 已合并 exact pin 与新的具体现场授权。

## 接口、数据与兼容性影响

仅新增独立的 `company-platform-baseline/v1`，不复用 greenfield inventory 版本、不改变其校验或 operator VERSION。只读脚本为单文件 Python 标准库，用户以 `python3 -I -S -B` 运行。schema 与程序的 schema 输出逐字节一致；程序执行严格结构校验和状态语义校验。

固定命令执行无需 shell；环境固定且不读取或继承环境变量。HTTP 仅 loopback:8888 的两个固定 GET，无认证、代理或 redirect；ss 仅两个批准端口，无 process 信息。数据目录只 stat 元数据，不枚举或读取内容；不读取 app.ini、credential path、环境、原始日志或 legacy 8080。PostgreSQL 仅服务/二进制/监听，不发 SQL、pg_dump、恢复或登录。

人工记录仅接受特定枚举/计数/布尔/版本与 digest；由操作员核验原证据后确认，digest 仅证明字节一致，不能证明陈述真实性。无可信记录继续 BLOCKED。host scope、运行时间和同次 UUID 绑定，默认 current 有效期 24 小时；历史无论 PASS 与否不参与决定。

## 风险与回滚约束

本合同批准新增只读实现与测试，不修改生效治理文件，故无需治理文件先行应用。工作区内代码/文档写入与本地提交已授权；“零写入”作用于公司现场。开发侧 Issue 分类投影已授权，不能转成公司系统写权限。源码可普通 revert；现场无状态变化需要回滚。验证仍必须注明实际执行环境。

## 非目标

现场 package install、文件写入、sudo、服务 restart/enable、数据库/UFW/网络/账号/权限/仓库/Runner/timer 变更、部署和清理；legacy 8080；完整配置/环境/凭据/原始日志；自动授权或自动选择 reinstall/upgrade；#270 实现及其他仓库变更。

## 未决问题

实现方向无未决问题。公司主机 current 读回、host pin 与人工证据尚缺，按已批准的用户采集包替代交付路径处理，不扩大权限。

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

# 验证记录

## 基线

原2.0.0固定包的本地合成复现：skip与25字符列可解析；allow/deny/reject及26/27字符列 parse-failed。脚本 /private/tmp/newemaint-79-ufw-format-repro.py，host_probes=0，assertions=PASS。

## 实施验证

PASS：plan 中联合 unittest 命令实际运行 106 tests，OK（7.139s）。覆盖 v1/v2 diagnostics、v1/v2 baseline，包含 builder 两次相同字节构建、漂移/权限/symlink 拒绝、v1 hash guard。

AC-1/2：新增四种策略 × 三种列宽 × 四种动作共48个正例；未知策略、重复策略、短列单空格、未知动作、无分隔符、空来源字段等负例。首轮27 tests曾因空来源仍被旧宽松匹配接受而失败；修复为目标/来源必须含非空白字符，联合回归通过。

AC-3：新采集2.0.1，合成历史2.0.0 BLOCKED按原hash校验保持BLOCKED；错hash及未知版本拒绝，原v1文件hash guard通过。此处为合成历史兼容测试，非重新认定公司旧证据当前有效。

AC-4：check-change-documents 实际输出 changes=130 pass=2 gap=0；git diff --check PASS。apply-classification-labels.sh --verify 282 输出 projected，platform/complex。没有修改builder、CI、探针argv、超时或现场配置。

交接状态：AWAITING_PR_CONFIRMATION；远程push/PR/CI NOT RUN。最终PR策略manual。

## 公司现场

NOT RUN。本票不触及公司主机；旧现场 evidence 不因本地测试改判。

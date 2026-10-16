---
issue: 362
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/362
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - security
  - shared-core
  - deployment
  - rollback
  - platform-governance
depends_on:
  - 360
status: approved
branch: change/362-mac-broker-install-acceptance
created: 2026-10-17
updated: 2026-10-17
reason: 本机共享 system broker 安装和完整恢复涉及安全、共享核心及平台运维，强制 complex/manual。
override_reason: ''
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-mac-broker-install-acceptance-261017.md
  spec: spec-mac-broker-install-acceptance-261017.md
  plan: plan-mac-broker-install-acceptance-261017.md
  verification: verification-mac-broker-install-acceptance-261017.md
pr_url:
---

# #362 Mac system broker 固定版本安装与验收

当前执行状态 **BLOCKED_EXTERNAL / ROOT_AUTHENTICATION_REQUIRED**。整包合同已由直接人类批准；这不是再次等待业务批准。
唯一 owner/session `01a1457e-699f-7372-8b6a-7a21d613d407`；worktree `/private/tmp/issue-362-mac-broker-install-acceptance`，claim 已创建，未发表。
本票只写四份语义文档、一个本人接续 runbook 及本会话 artifact；安装来源始终是 canonical source main 的固定 pin。
正式classification已读回 `projected`：`type/platform`、`complexity/complex`；lifecycle独立读回 `approved`，见artifact `classification-readback.json`。

## 问题/需求总结

#360 已通过 PR361 合并，但 system broker 两个模块仍旧，公开 metadata 绑定旧 source。
安装审阅卡与正式 #362 正文已 fresh 核对；正文 SHA256 `d160cf94bca4b52e459de257ca709ed6a42e7646f921ebaa232f86ec85851bb4`。
直接批准覆盖 snapshot、安装、no-op、完整恢复旧 baseline、再安装、实际只读资格和 F1/F2；最终文档 PR 另一次 manual 确认。

## 影响范围

固定 source `06afadfca2a950ad6ebee4b90a22e9d950bc72fa`，installer SHA256 `485ea19514c5f4b72c84d6cc9576fe0c2b65c34d084e74c8f80e2d6ad6f10897`。
27 静态文件 + 1 生成公开 metadata + exact previous 链/父目录/本次临时 metadata；无 source/runtime/installer/manifest/权限政策修改。
详细范围见 [spec](spec-mac-broker-install-acceptance-261017.md)，个人操作步骤见 [runbook](runbook-mac-broker-install-acceptance-261017.md)。

## 初步方案与建议

合同已批准，保留 `status: approved` 表示合同/启动许可；实际执行暂停由 root 外部条件决定。
固定 `/usr/bin/sudo -n /usr/bin/id -u` 在 host 真实返回 exit 1、`sudo: a password is required`。
系统写入窗口未开启；snapshot 未创建；P1–P6 全部 NOT RUN。F1/F2 两项封闭 fixture 已通过且临时根清理。
恢复入口后先 fresh 核 pin、27 source、完整 target baseline 和共享工具窗口，再执行 P0–P6；不得直接跳到 installer。
本人私密终端认证必须在实际执行同一终端/适用 timestamp 上下文，另一个终端 `sudo -v` 不保证 Codex `sudo -n` 可用。

## 风险

installer 顺序写入；必须由本人协调其他 broker/Controller 使用者避开写入窗口。本地 marker/进程快照不证明排他。
不依赖 `.previous` 单独回滚；fresh snapshot 完整保留，原缺失的新文件只有 exact 路径且字节可证时可删除。
Mac user Loop GAP、VM installed NOT READ、architecture/lock GAP 保留；HSDB 采用/公司部署不由本票推导。
HSDB#15 资源/OID 冻结，公司#32/T06 PAUSED，`IMPLEMENT_PROVIDER=none`。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 本机共享 system broker 安装和完整恢复涉及安全、共享核心及平台运维，强制 complex/manual。
risk_flags:
  - security
  - shared-core
  - deployment
  - rollback
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
```

### 判级证据

- 真实 root-owned 共享工具运维，安装、恢复和平台安全边界均属于 forced complex；policy manual。
- 只消费已合并固定 source；本票文档 HEAD 不作为安装 source。

### 缺失的 acceptance criteria 或决策

- 无新业务决策；唯一已观察执行阻塞为原生 root 认证。窗口协调和写前 snapshot 尚未运行，不能宣称 P0 通过。

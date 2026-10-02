---
issue: 311
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/311
change_type: maintenance
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
reason: 维护共享 runner 主机的工具链来源记录或移除工具链，触及共享 CI 基础设施与回滚，强制 complex。
risk_flags:
  - shared-core
  - ci-integration
  - rollback
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-node22-provenance-261002.md
  spec: spec-node22-provenance-261002.md
  plan: plan-node22-provenance-261002.md
  verification: verification-node22-provenance-261002.md
confidence: high
override_reason: ''
depends_on: []
status: approved
branch: change/311-node22-provenance
pr_url:
created: 2026-10-02
updated: 2026-10-02
---

## 问题/需求总结

#309 的历史主机实测发现 `/opt/node22` 为 Node 22.22.0，属主为 gitea-runner，缺少来源 marker。
#311 要求完整盘点后，选择保留并补 unknown marker 或授权删除。Issue 正文写“三仓”但列了四仓；本变更按四仓执行，不漏 SFMDigitalBoard。

本会话已 live 读回 #311：open，只有 needs-analysis，零评论，无历史合同批准。
本地固定 Git 对象显示 SFMDigitalBoard 的 CI 明确依赖 `/opt/node22/bin`，因此当前不得选择删除。
其它三仓已获本聊天用户只读确认并通过各自 manifest broker fresh-fetch；四个 fixed main SHA 均与初查一致。workflow 与 committed 非 Secret 实现配置未发现额外活动 node22 消费。真实主机确认 Node 22.22.0/npm 10.9.4/pnpm 10.28.0，仍无 marker。

## 影响范围

- 平台仓：本 Issue 的语义文档、盘点证据、后续 `01` §4.2 的最小事实修正。
- 主机：只有选项 A 获批后才允许写 `/opt/node22/.aisoft-runtime-source`；选项 B 必须在零消费方证据与明确删除批准后才可执行。
- 四个应用/平台仓仅只读，不修改 workflow。
- 不修改 AGENTS.md、skills、broker/runtime、CI 脚本、act_runner 配置、node24、Flutter 或任何凭据。

## 初步方案与建议

1. 四仓 fresh 核对已完成，普通 benque 主机探针已完成；保护配置及 effective PATH 字段由 [主机提案](host-action-proposal-node22-provenance-261002.md) 的 root 补读完成。
2. 已锁定保留：SFMDigitalBoard fresh CI 有活动引用；marker 已知消费方和 unknown 字段具备精确候选。
3. 来源无法证明时明确 `unknown`；目录 mtime 不冒充安装日期，本次盘点日期不冒充安装日期，当前二进制哈希不冒充上游包校验值。
4. 本聊天用户“确认，继续”已批准完整合同与精确主机动作；marker 创建、幂等与回滚重建已执行通过。最终 PR 提交尚未批准。

## 风险

漏掉 SFMDigitalBoard 会错误删除在用工具链；旧 ref 不能证明当前消费方；读取完整 profile、runner Secret 或全量环境会越界；补 marker 不得把未知历史包装成可信 provenance。marker 回滚仅删除本次创建且哈希一致的 marker，不能删除目录。

## AI 判级

```yaml
change_type: maintenance
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
reason: 维护共享 runner 主机的工具链来源记录或移除工具链，触及共享 CI 基础设施与回滚，强制 complex。
risk_flags:
  - shared-core
  - ci-integration
  - rollback
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
```

### 判级证据

当前 AGENTS.md 与 classification.py 将共享核心、CI 和回滚强制按 complex；Issue 中的 small 只是候选预期。type 保持 maintenance，policy 固定 manual。该安全判级不取决于最终选择 A 或 B。

### 合同与待确认权限

- 当前用户已确认各项目 fresh read 与 benque 探针；该只读范围已执行，证据附 fresh-consumer-inventory 与 host-inventory。
- A 已锁定，B 按真实消费方证据排除。marker 内容、根权限补读、apply/check/rollback/reapply 命令见 host-action-proposal。
- 本聊天用户已明确确认 gitea-ci/root 限定补读、marker 创建/幂等/精确回滚重建及判级投影；上述动作已执行通过。
- 初始标签写入曾因缺启动授权被自动审核拒绝。取得用户明确启动确认后官方 projector 已 apply，真实 --verify=projected，lifecycle=approved。

## 已批准实施结果

只新增 marker，SHA-256=bd3c6ccaf6929449631684667043dc614607170722d5fb658025b6d281d5db8c；Node binary hash、3783条非marker元数据和配置元数据前后一致。静态补读未发现更多已知消费者；动态profile执行/process Secret环境仍按合同排除。01 §4.2 已同步来源unknown但在用。全部live receipts见verification；应用部署与目录删除不适用，PR/CI未执行。

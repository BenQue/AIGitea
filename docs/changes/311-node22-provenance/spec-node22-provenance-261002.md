---
issue: 311
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/311
change_type: maintenance
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
confidence: high
risk_flags:
  - shared-core
  - ci-integration
  - rollback
depends_on: []
status: approved
branch: change/311-node22-provenance
created: 2026-10-02
updated: 2026-10-02
---

## 目标与原因

保留当前有消费方的 /opt/node22，仅补真实 unknown 来源记录，同时把四仓和 runner 静态配置消费方盘点落到可审阅证据。fresh main 已证实 SFMDigitalBoard 的 CI PATH 和测试守卫仍使用此工具链；删除方案不符合当前事实，已排除。

## 用户故事与方案

1. 维护者能看到四仓全部 workflow 与非 Secret committed 实现/配置的 fixed SHA 清单；活动配置、注释与合成测试分开说明。
2. 维护者能看到 runner unit/drop-in/config/profile 必要静态字段，权限或动态配置边界显式记录。
3. SFMDigitalBoard 继续使用原 node22；本次不换 Node/npm/pnpm 字节、路径或版本。
4. 审阅者看到安装日期、安装者、上游来源/包校验为 unknown，本次记录日期和当前 binary hash 是不同字段。
5. 操作者能在重复执行时获得 no-op，并通过精确 marker 哈希回滚后重建；不删除工具链目录。

## 实现决策与授权范围

锁定 A 路径：保留 node22，只新增 .aisoft-runtime-source。精确 payload、Python apply/check/rollback 命令、主机身份和顺序见 [host action proposal](host-action-proposal-node22-provenance-261002.md)。所有不明历史字段 unknown；contract 与 key=value 形状沿用真实 node24 marker。

完整 payload 已写为 marker-node22-provenance-261002.txt，SHA-256 为 bd3c6ccaf6929449631684667043dc614607170722d5fb658025b6d281d5db8c。
node22 实测 22.22.0、npm 10.9.4、pnpm 10.28.0，当前 Node binary SHA-256 为 8eeefcacdf48f58541a651016e604055d14a992e39df98636b76495bc7244395。
known_consumers 当前只列 admin/SFMDigitalBoard:.gitea/workflows/ci.yml。

本聊天用户“确认，继续”已批准 exact 主机动作。确认明确包含 gitea-ci/root 的限定非 Secret 补读，以及 marker 创建、check、重复 apply、rollback、重新 apply 与最终 check；这是主机动作的独立精确授权，不由分析授权或日后 PR merge 推导。

补读由 readonly-root-detail-proposal-261002.py 固定到 effective runner unit、两个 drop-in、runner config、runner 用户静态 profile 和 systemd symlink 的 metadata 覆盖。额外已知消费者属于盘点内证据补齐：写前更新 known_consumers 与 payload hash，记录差异并校验仍只写 marker。不修改该消费者或其配置。发现会改变处理方向、Secret 需求或范围扩张时停止给人裁决。

仓库只改本 Issue 的语义文档、证据/命令提案和 01 §4.2 的最小 as-built 修正；不修改 AGENTS.md、skills、controller、broker/runtime、CI/部署脚本或任何应用仓。

## Acceptance criteria

- [ ] AC-1：四仓全部 workflow 逐文件 fixed SHA 结果与相关非 Secret committed 引用清单；static runner unit/drop-in/config/profile 的必要字段与 symlink 覆盖回执入 verification。动态 profile/process Secret 环境按批准边界明确排除，不声称全主机无未知消费方。
- [ ] AC-2：marker 与已核对 payload 一致，未知历史字段不伪造；runner 属主、644 权限；node22 目录、Node binary hash/npm/pnpm 版本和非 marker 文件元数据保持；真实 check、重复 no-op、精确 rollback 后重新 apply/final check 均有回执。
- [ ] AC-3：01 §4.2 写来源 unknown 但在用、已知消费方与实测版本；check-change-documents PASS；exact #311 classification --verify projected。
- [ ] AC-4：root 补读与主机 mutation 有明确授权；未读取 .env/auth/registration/凭据/日志/process environ/argv，未 source profile，未修改 node24、Flutter、act_runner 或应用仓。

如静态盘点有真正未读取的 active 配置或无法判断的 PATH 链，AC-1 保留 GAP、不能关闭或归档。symlink 只在目标确实已扫描时归并，不把符号链接本身当成额外消费方。AC-2 不证明上游来源可信，marker 的 unknown 保留。

## 接口、数据与兼容性影响

无数据库/schema/外部 API 变化；Node 路径和版本不变。marker 是新增来源记录，不参与执行。平台 type=maintenance，触及共享 CI/回滚强制 complex，policy=manual。

## 风险与回滚约束

marker 不存在才可创建；内容或属主/权限不同的既有 marker 拒绝覆盖或删除。目录/二进制/版本漂移先停止。partial marker 写入失败 fail closed，保留现场并升级，不能报成功。正常回滚只删除本次 exact matching marker，随后恢复，目录和其它文件不删除。

源命令在 proposal 中供审阅，不安装到主机或全局；执行前比对 code/payload hash。实际环境验收无法由 diff 或 CI 替代。

## 测试与验收映射

优先四仓 fresh Git 对象、真实主机静态字段、marker 回读与 no-op/rollback receipts、代表性 binary hash 和非 marker 文件元数据。Python AST 与 payload 一致性 PASS；主机写/幂等/回滚重建均已真实执行并通过。后续只改文档与 marker 命令，不修改 shell 脚本；按实际变动执行 local 文档/静态检查及最终 required CI，不继承旧 PASS。

## 非目标

不删除、升级、重装 node22/npm/pnpm；不改 workflow；不新增 typed 操作；不改治理文件；不重启服务；不读取 Secret；不安装全局技能；不实施其它 Issue；不 push/PR/merge/deploy（最终 PR 提交另行确认）。

## 未决问题

无。用户已确认合同启动及 exact root 读写/回滚和判级投影；当前已完成。最终 PR 提交仍须独立绑定 exact Issue/branch/manual 的确认。

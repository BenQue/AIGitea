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

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 四仓 fresh 依赖和普通主机盘点，锁定保留方案与可审阅合同 | - | completed |
| T02 | root 限定补读、已批准的 marker 创建/读回/重复/回滚重建与 01 同步 | T01 | completed |
| T03 | 所有启用 AC 验收、语义文档和判级读回，唯一 manual PR 候选 | T02 | blocked（既有 main smoke 回归；两轴审查完成） |

T01 四仓 fresh main 与 benque host probe 均已执行；权限 GAP 保留，处理方向已锁定 A。T02 是 root 补读及 marker 动作的授权 frontier。票据保持 #311 内，不新建子 Issue。
T02 在一次具体完整合同/启动确认后执行；明确主机授权才可 mutation。
T03 的最终 PR 提交单独绑定 #311、change/311-node22-provenance、manual 确认。人合并后再做 exact merge 与终态、清理、归档。

## Expected touch points

- T01：本 Issue summary/spec/plan/verification、盘点附件；其它四仓 Git 对象只读。
- T02：本 Issue verification 与 `01-基础设施-VM-Gitea-Runner.md` §4.2 的最小事实修正；主机 target 只有已批准的 A 路径 marker。
- T03：本 Issue 语义文档、唯一 PR、required CI 读回。不改 runtime、broker、AGENTS.md、skills、CI/部署脚本。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | 四仓 manifest broker fresh main + fixed SHA workflow/间接脚本扫描；受控主机探针逐项脱敏回执 |
| AC-2 | 已批准 exact marker 命令；内容格式/unknown 字段对比；marker 外清单对比；no-op 与精确回滚 |
| AC-3 | 01 与真实回执对比；check-change-documents；apply-classification-labels.sh --verify 311 |
| AC-4 | 只读/主机授权记录与命令 review；没有 Secret/raw environment 输出或跨范围 mutation |

## 部署与回滚

没有应用部署；共享主机持久状态是独立授权面。A 回滚仅删除本次且 hash 一致的 marker，实际回滚后已重建并最终验证。没有主机 mutation 授权时固定 NOT RUN。

## T03 当前阻塞

完整 smoke 受控本地运行 FAIL，registry-preflight 停服务负向断言返回0；fixed main同三文件独立复现同失败。详细命令、源文件哈希与日志摘要见 [local validation](local-validation-node22-provenance-261002.json)。#319修复尚未合入main，等待其真实集成后由本owner更新并重验。不扩张#311范围、不绕过UTF-8失败、不新增产品depends_on。最终PR确认尚未请求。

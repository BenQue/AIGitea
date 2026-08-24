---
issue: 190
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/190
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - platform-governance
  - ci-change
depends_on: []
status: pr-open
branch: change/190-template-sync-broadcast
created: 2026-08-24
updated: 2026-08-24
---

# Spec：change 模板的上游同步广播

## 目标与原因

给 `templates/docs/changes/_template/` 的 vendored 副本补上它缺失的两条声明——
**谁持有副本**、**模板是哪一版**——并让「改动模板必须广播下游」成为平台侧不可绕过的
动作，而不是靠某人恰好跑了一次 `aisoft-project-check.sh`。

裁决为 Issue 正文的方向 1（上游广播）。方向 2/3 的取舍理由写在 summary 的
「### 方向裁决」，本 spec 只定义采用方向的合同。

## Acceptance criteria

- [ ] **AC-1 裁决落文**：三个方向的取舍与理由写进本次变更的文档，不选的两个也写明
      为什么不选。
- [ ] **AC-2 holder 是声明而不是猜测**：`gitea-governance.json` 每个仓库可声明
      `vendors_change_templates`；未声明时取 `true`（宁可多列，不可漏列）；非布尔取值
      被 `load_contract` fail-closed 拒绝。
- [ ] **AC-3 模板有版本号**：`codex/config/change-template-sync.json` 钉住覆盖「文件名
      + 内容」的 `template_digest`；改名或增删一份模板同样导致 digest 变化。
- [ ] **AC-4 不广播就过不了平台 CI**：`codex/tests/smoke.sh` 在钉住的 digest 与当前模板
      内容不一致时失败，且失败输出给出补救命令。
- [ ] **AC-5 广播清单不依赖下游 checkout**：`--refresh-digest` 打印全部声明为 holder 的
      项目，本机没有 `mac_checkout` 的项目同样在清单里，并标为 `unverified` 而不是被
      当作已同步。
- [ ] **AC-6 逐项状态可分辨**：对本机可读的 checkout 区分 `current` / `stale`（列出差异
      文件）/ `missing`（目录不存在）；checkout 停在非 `main` 分支时在行尾标注。
- [ ] **AC-7 非阻塞是被钉住的合同面**：`downstream_required_check` 必须为 `forbidden`，
      否则工具退出 1；smoke 另有断言钉住该取值与 `03` 里的约束句。
- [ ] **AC-8 真实模板改动验证**：改 `templates/docs/changes/_template/` 下任一文件后，
      `--verify-digest` 变红、`--refresh-digest` 指出所有持有过期副本的项目；回滚后转绿。
- [ ] **AC-9 不改下游**：本次变更不在任何下游项目仓库产生提交，也不新增任何下游 CI
      context 或 required check。

## 接口、数据与兼容性影响

**新增 CLI**（`codex/tools/change-template-sync.sh`，只读除非显式 `--refresh-digest`）：

| 调用 | 语义 | 退出码 |
|---|---|---|
| （无参数） | 打印 digest 状态与每个 holder 的副本状态 | 0 无需动作；3 需要动作 |
| `--porcelain` | 同上，制表符流 `name\tstatus\tcheckout\tdetail` | 同上 |
| `--verify-digest` | 只核对钉住的 digest（平台 CI 用） | 0 一致；3 漂移 |
| `--refresh-digest [--today D]` | 刷新 digest 并打印下游同步清单 | 同 plan |

用法错误一律 64，硬错误（manifest 非法、合同源模板缺失、`downstream_required_check`
被改掉）一律 1。

**新增 manifest 键**：`repositories[].vendors_change_templates`（可选布尔，缺省 `true`）。
既有 manifest 不加这个键时行为完全不变——每个仓库都被视为 holder，这正是当前事实。

**新增 manifest 文件**：`codex/config/change-template-sync.json`，`contract_version`
固定 `change-template-sync/v1`。

**兼容性**：不改 `aisoft-project-check.sh` 的 `change-templates` 语义（仍是 `cmp -s`
逐字节相等、仍只是 GAP 而不是错误）；不改任何下游仓库；不新增任何 broker typed 操作。

## 风险与回滚约束

- 回滚是纯删除：撤掉本次变更即回到现状，没有需要清理的残留状态（未声明的
  `vendors_change_templates` 与删除后的行为一致）。
- 逐项状态取自本机 checkout 的工作树而非仓库 `main`，必须在输出里标注非 `main` 分支，
  并明确 `unverified ≠ 已同步`；否则一个停在 feature 分支的 checkout 会被读成
  「这个仓库没有模板」。
- 本机制不修历史欠账。首跑暴露的既存缺口按平台合同走各自仓库的独立 Issue。

## 非目标

- 不迁移下游、不删除下游的 vendored 副本（方向 2）。
- 不挂定时任务、不自动开 Issue（方向 3）——需要独立验收标准。
- 不修 HSDB / NewEMaint / rsdesign-new / SFMDigitalBoard 的既存缺口。
- 不改 `AGENTS.md`：本次运行正在遵循它。
- 不新增 broker typed 操作，不读取任何远端仓库内容。

## 未决问题

- 无。

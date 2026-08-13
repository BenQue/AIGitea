---
issue: 112
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/112
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
reason: vm_profile manifest schema 新增可选工具链声明位并改变 ProfileMigrator 生成/read-back 合同，属 schema/外部契约与平台治理工具变更，强制 complex
risk_flags:
  - platform-governance
  - schema-change
required_docs:
  - summary
  - spec
  - plan
documents:
  summary: summary-profile-path-prepend-260813.md
  spec: spec-profile-path-prepend-260813.md
  plan: plan-profile-path-prepend-260813.md
confidence: high
override_reason: ''
depends_on: []
status: ready-for-review
branch: change/112-profile-path-prepend
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/113
created: 2026-08-13
updated: 2026-08-13
---

## 问题/需求总结

`ProfileMigrator._profile_bytes`（`codex/runtime/aisoft_host_access/profiles.py`）为每个
manifest 声明的 VM 项目生成固定 9 键 profile，没有 PATH 或任何工具链声明位。pre-#61 的
`sfm.env` 手工带有 `PATH=/opt/node22/bin:/home/coder/.local/bin:...` 行，迁移后消失，
sfm 项目 agent 的 Node 被静默降级到系统 v20；当前靠 VM 上未版本化的 systemd drop-in
（`~/.config/systemd/user/aisoft-agent@sfm.service.d/10-path.conf`）临时覆盖，重装/换机即丢。
任何需要非默认工具链的项目都会遇到同类问题——其它项目只是恰好不需要，不是机制健全。

## 影响范围

仅平台仓库 host-access 合同线：`codex/runtime/aisoft_host_access/`（contract/profiles/cli）
与其测试、`codex/config/host-access-broker.json` 的 sfm `vm_profile` 段、
`templates/agent/project.env.example` 注释。不修改 AGENTS.md、CI workflow、
`codex/agent/*` 消费者脚本（#111 地盘）、`codex/tools/project-profile-migration.sh`
（薄封装，无 schema 知识）、systemd 单元与任何业务仓库。

## 初步方案与建议

1. manifest `vm_profile` 新增可选 `path_prepend`（字符串列表）；contract 层 fail-closed
   校验：绝对路径、受限字符集 `[A-Za-z0-9._/-]`、规范化、无重复，非法即拒载 manifest。
2. `_profile_bytes` 在声明时于末尾追加一行 `PATH=<e1>:...:<eN>:$PATH`（prepend 语义，
   profile 由 bash `set -a; source` 消费，`$PATH` 在 source 时展开）；未声明项目输出
   与现状 byte-identical。
3. `read-back`/`consume-check` 的 exact 比对同步携带该行；漂移报 `READ_BACK_MISMATCH`。
4. sfm 声明 `["/opt/node22/bin", "/home/coder/.local/bin"]`（忠实还原 pre-#61 PATH 头部）。
5. `profile-spec` 输出增加 `path_prepend` 投影，供 VM 侧诊断。

## 风险

- PATH 是执行边界：受限字符集 + 绝对路径 + 规范化 fail closed，杜绝注入与相对路径劫持；
  生成行不需要引号即 shell 安全。
- 未声明项目扰动风险：以「与迁移前字面量逐字节相等」测试锁死（AC-4）。
- 回滚：单 PR revert 即可；已迁移 profile 的回滚走既有 `vm.profile.rollback`
  （latest/previous 备份机制不变）。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
reason: vm_profile manifest schema 新增可选工具链声明位并改变 ProfileMigrator 生成/read-back 合同，属 schema/外部契约与平台治理工具变更，强制 complex
risk_flags:
  - platform-governance
  - schema-change
required_docs:
  - summary
  - spec
  - plan
confidence: high
override_reason: ''
```

### 判级证据

- Issue 建议方向即为 host-access-broker manifest 的 `vm_profile` schema 扩展（新增可选
  `path_prepend`）加 `_profile_bytes`/`read-back` 行为变更：新增功能、schema/外部契约、
  平台治理工具三条强制 complex 规则同时命中（AGENTS.md 强制风险规则、03 §2）。
- 生成的 project profile 是 VM agent 运行环境的唯一事实源（`aisoft-agent@.service`
  不设 `Environment=`），PATH 声明直接决定 agent 工具链；安全边界必须由 spec 固化。
- contract_effect=add：为 manifest 与 profile 新增扩展点，未声明项目输出保持
  byte-identical，不属恢复/保持既有合同的 small 候选。

### 缺失的 acceptance criteria 或决策

- 无。AC-1..5 在 Issue 正文明确；profile 中 PATH 形态（`PATH=<entries>:$PATH` 单行
  vs 独立键）由 spec 决定并给出理由（见 spec §接口）。

## 状态记录

- 2026-08-13：判级评论已发（Issue #112）；spec/plan 完成。标签投影
  （complexity/complex + type/platform 等）属 controller/projector 职责，Mac 会话
  broker 无标签 typed 操作，未在本会话执行。
- 2026-08-13：sfm 的实际 VM 重迁移（`vm.profile.plan/apply/read-back`）与 systemd
  drop-in `10-path.conf` 移除是合并后 VM 侧跟进项（见 plan §部署与回滚），不在本
  变更执行。
- 2026-08-13：T01/T02/T03 实施完成（合同层三态校验、生成/read-back、profile-spec
  投影与模板注释）；test_host_access 64 测试与 full smoke（342 tests）全绿；
  最终 PR #113 已创建，停在人工合并。

---
issue: 445
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/445
change_type: security
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - security
  - authorization
  - platform-governance
  - shared-core
depends_on: []
branch: change/445-project-template-scope
created: 2026-11-10
updated: 2026-11-10
---

# 验证：项目来源规范模板 scope

BASE `30c8994e74767fbe660c22bfd739d7d51a9bd6b1`。负责人已选择仅更新 fresh main 已存在的规范模板，首次新增仍拒绝；实现、修复后测试、最终审核、发布及安装均 NOT RUN。

- 基线 `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=codex/runtime python3 -m unittest -v tests.test_project_declared_source.OperationsTest.test_template_owning_changes_need_the_site_source`：1/1 通过；测试验证当前拒绝，不能作为修复通过证据。
- 基线 `tests.test_project_source_e2e`：沙箱回环端口被拒，4 项无法启动；经授权在本机运行隔离的 loopback 假服务和临时仓库后 4/4 通过。这是旧版本基线，不覆盖本票新模板场景。
- 实现前安全预审：Herdr 桌面可见会话 `t24`，Claude Code 实际显示 Opus 5.5 / high，BASE=HEAD `30c8994e74767fbe660c22bfd739d7d51a9bd6b1`。Claude 认为选定设计可行，并要求逐路径检查 fresh main、覆盖历史删除/恢复及错误类型、保留 site source、检查远端漂移并承认传输非原子窗口；项目声明和无签名包记录不能充当独立授权。负责人处理计划提示后，Claude 回复未更改项目文件并等待实际候选；这是设计预审，不是实现后的最终审核。
- 安全边界只读演示：在内存中保持旧 release 前缀，构造任意模板摘要的新 release 并重算无密钥 bundle digest，内部一致性仍成立；这不证明官方来源，也不是 `--verify` 或线上测试。

- T01 开始回执：`aisoft prepare-ticket 445 T01 --provider codex` 返回 `prepared`，ticket_base 为上述 BASE；exact branch `change/445-project-template-scope`，owner `01a1c32a-009d-7663-af62-d65a27032a16`，起始四份合同为 untracked、tracked 工作树干净。回执 `.superpowers/aisoft/445/T01.json` 位于本工作区 ignored 缓存，不能充当测试或审核通过证据。执行端为 Codex；具体模型与推理强度未由 helper 观测。
- 项目侧只读核对：typed `git.fetch.main` PASS，CarbonEngine Gitea main `b97c61d49acd63e3b4a4d56dbdaaed227ed6c25d` 的四份规范模板均为 `100644` blob；#98 本地 HEAD 仍为 `43a81e47a59ecf09262ad1a73fe75dc2cc98090a`，实际修改其中 `spec.md`、`summary.md`。这不是新版本项目采用或真实推送证据。
- 治理步骤验证：`aisoft resolve-route 445 --provider codex` 命中 production complex 的 R3/S1、D4；`aisoft prepare-ticket 445 T01 --provider codex --resume` 核验原回执的 owner 与语义摘要通过；`aisoft check-change-documents` 为 `changes=205 pass=2 gap=0`。这些只证明合同和文档检查，并不证明运行时修复。
- 治理步骤提交后按平台规则停止当前写入；fresh run 必须读回实际治理 commit、Issue 批准、工作区 owner/branch/HEAD 与当前规则后再开始 T02。

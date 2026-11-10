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
git_scope:
  - docs/changes/445-project-template-scope/summary-project-template-scope-261110.md
  - docs/changes/445-project-template-scope/spec-project-template-scope-261110.md
  - docs/changes/445-project-template-scope/plan-project-template-scope-261110.md
  - docs/changes/445-project-template-scope/verification-project-template-scope-261110.md
  - docs/adr/0003-adoption-access-decoupling.md
  - codex/runtime/aisoft_host_access/project_source.py
  - codex/runtime/aisoft_main_integration.py
  - codex/runtime/tests/test_project_declared_source.py
  - codex/runtime/tests/test_main_integration.py
  - codex/runtime/tests/test_project_source_e2e.py
  - codex/runtime/tests/project_source_fixture.py
  - usage/bundle.json
  - docs/governance/review-evidence-index.md
branch: change/445-project-template-scope
created: 2026-11-10
updated: 2026-11-10
---

# Spec：项目来源规范模板 scope

## 目标与原因

项目自主采用官方使用包后，允许项目来源更新目标仓库 fresh main 中已存在的规范模板，同时保留项目来源和站点来源各自的信任边界。当前 1.23.1 项目来源一律拒绝模板 scope，导致已有模板项目无法发布采用变更。

## 范围与非范围

平台通用来源、共享 Git scope、关联 fixture、ADR 与后续使用包候选；不登记具体项目，不扩大凭据或仓库权限，不改其他 Issue 工作区，不修改保留的项目候选或生产环境。main 尚不存在模板时的首次新增不在本票允许范围，继续拒绝。

## Acceptance criteria

- [ ] AC-1：项目来源能对 exact 仓库、Issue、分支、owner 和已提交 spec scope 中的规范模板执行 typed 推送：每个路径必须在 typed 工具新鲜读取的目标仓库 main 中已存在且为普通 100644 blob；首次新增、main 不可验证或路径不匹配一律拒绝。不要求中央站点登记。
- [ ] AC-2：保留规范模板闭集、父目录树和普通文件、防符号链接、其他 Issue 路径、身份、逐提交历史、main 祖先及远端租约的 fail-closed 行为；传输前发现 main 或 HEAD 漂移须拒绝，传输后发现漂移须准确报告可能已发生的写入并停止准备 PR。不得将客户端读回写成原子并发保证；区分项目自主声明和独立审批事实。
- [ ] AC-3：隔离本地 fixture 验证已有模板升级可推送，main 缺少任一目标模板时首次新增被拒；同时覆盖未声明路径、非法类型、错误仓库/owner、远端移动和 site source 不回归。
- [ ] AC-4：覆盖 open-pr 首推、PR 查重、回填及第二次推送相应路径；测试不制造真实远端对象。
- [ ] AC-5：形成可验证的新使用包候选并协调 #444 并行发布；记录 source、fixture、发布、安装与项目实际采用的独立状态。
- [ ] AC-6：固定 BASE/HEAD 接受未参与实现的独立 Claude 安全审核；未运行项如实报告，merge/安装/部署按独立授权办理。

## 风险与回滚约束

负责人 2026-11-10 决定：仅允许更新 fresh main 已存在的规范模板，首次新增继续拒绝；以 #445 的 ADR 补充修订现行 D4 的站点独占规则。fresh main 的现有文件仅证明路径存在，不证明内容可信或批准；项目来源的守卫为协作式校验，不能对抗持有同一项目凭据的本机用户。`git_scope`、summary 状态和项目仓内无签名摘要不构成人工授权或官方来源证明。身份或 scope 校验失败及传输前读到 main 或远端状态变化时拒绝；客户端最后一次读取与服务端接收之间存在非原子窗口，传输后读到漂移时必须如实报告远端可能已写入并停止准备 PR。保持可通过独立变更回退。

## 接口、数据与兼容性影响

不得增加管理员权限、依赖平台中央登记或改变站点来源语义。项目来源无法自动验证分支保护规则，服务端保护与人工合并仍由项目负责；不冒称保护已现场验证。拟改发布包成员，旧版 pin 不会自动更新；既有 #98 候选保留，后续项目采用另行核对和授权。

## 未决问题

无；仅更新 fresh main 已存在模板，首次新增继续拒绝。

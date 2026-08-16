---
issue: 121
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/121
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - agent-governance
  - platform-governance
  - external-contract
  - cross-module
depends_on: []
status: approved
branch: change/121-matt-repository-adapter
pr_url:
created: 2026-08-16
updated: 2026-08-16
---

# Spec：AISoftPlatform Matt repository adapter 与 Analyzer-only profile

## 目标与原因

为 AISoftPlatform 正式仓库建立 Matt skills 所需的 repository-level 配置，并解除首次 platform Analyzer
因 `vm_profile: null` 产生的引导死锁。交付必须保持 Gitea 为 tracker、protected-main 与 human-merge 单闸门，
且 profile 只能启用手工分析能力，不能启用 implementation、timer、service 或部署。

## Acceptance criteria

- [ ] **AC-1**：`docs/agents/issue-tracker.md`、`triage-labels.md`、`domain.md` 存在，并分别与
  `templates/docs/agents/` 同名文件 byte-identical。
- [ ] **AC-2**：`CLAUDE.md` 保留 `@AGENTS.md`，且恰有一个 `## Agent skills` block；该 block 指向三份
  `docs/agents` 配置，并明确 AISoftPlatform Gitea、namespaced Matt triage labels 与 single-context。
- [ ] **AC-3**：canonical host-access manifest 中 `aisoft-platform.vm_profile` 精确为
  `name=aisoft-platform`、`repo_dir=work/AISoftPlatform`、`analysis_provider=codex`、
  `implement_provider=none`、`timer_unit=null`，不声明 `path_prepend`。
- [ ] **AC-4**：合同 loader 将 approved profile set 固定为包含 AISoftPlatform 的五个项目；focused test
  验证 contract 字段与 `profile-spec --profile-name aisoft-platform` 的完整脱敏投影，不触达真实 VM 或凭据。
- [ ] **AC-5**：`AGENTS.md`、`codex/vendor/mattpocock/`、全局 skill 安装态、Gitea protection/required CI、
  credential、service/timer 与部署状态零修改。
- [ ] **AC-6**：`git diff --check`、focused unittest、完整 runtime suite 与
  `bash codex/tests/smoke.sh` 真实通过；任何未执行的 live/company 检查保持 `NOT RUN`。
- [ ] **AC-7**：只有一个 `change/121-matt-repository-adapter` branch/docs/worktree tuple 与一个最终 PR；
  PR body 恰有一行 `Closes #121`，不合并 PR。

## 接口、数据与兼容性影响

- repository adapter 新增三个纯文档配置入口；Matt skills 后续从这些路径解析 tracker、triage 与 domain。
- host-access manifest 对 `aisoft-platform` 从无 VM profile 变为有受控 profile；现有 typed operation 的
  名称、参数、身份路由均不变。
- `analysis_provider=codex` 只在人工调用 poller 时选择 Analyzer adapter；`IMPLEMENT_PROVIDER=none` 保持
  Development Loop 禁用，`timer_unit=null` 保持无自动调度。
- 无 schema migration、数据库、制品或业务 runtime 影响。

## 风险与回滚约束

| 风险 | 缓解 |
|---|---|
| profile 意外开放 implementation/自动执行 | 精确字段断言；`none`/`null` 两道静态闸门 |
| installed bytes 未刷新却误判可用 | source、installed 与 live 三层分开记录；合并后另行授权安装/read-back |
| profile apply 使用错误身份 | 只能由既有 `vm.profile.plan/apply/read-back` 验证 exact project-agent；本 PR 不读凭据 |
| repository adapter 形成第二套 Gitea 规则 | 三文件必须与 canonical templates byte-identical |

回滚 source 为单 PR revert。若未来已经独立执行 profile apply，回滚 source 前先停用任何手工 poll，随后由
另行授权的 typed `vm.profile.rollback` 恢复固定 backup；不得手改 profile 或 token 文件。

## 非目标

- 不创建、读取、轮换或复制 Secret/PAT/key。
- 不安装 broker/runtime/global skills，不执行 `vm.profile.apply`，不启用或重启 timer/service。
- 不修改 `AGENTS.md`、upstream Matt vendor、broker operation surface、labels taxonomy、branch protection 或 CI。
- 不继续 #120 的 triage/spec/plan/implementation；#120 等待 #121 人工合并及后续 read-back。
- 不访问公司内网，不执行任何公司 VM、测试或生产部署。

## 未决问题

无。

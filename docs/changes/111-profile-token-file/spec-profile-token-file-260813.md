---
issue: 111
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/111
change_type: bugfix
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - platform-governance
  - credential-handling
  - shared-core
depends_on: []
status: ready-for-review
branch: change/111-profile-token-file
pr_url:
created: 2026-08-13
updated: 2026-08-13
---

# Spec：平台工具统一 GITEA_TOKEN_FILE 解析（#111）

## 目标与原因

#61/#70 之后项目 profile 的凭据合同是 `GITEA_IDENTITY` + `GITEA_TOKEN_FILE`
（固定路径、mode 400/600 的 token 文件），不再内联 `GITEA_TOKEN`。
`codex/tools/` 下 5 个平台工具仍把内联 `GITEA_TOKEN` 当作唯一形态，导致已迁移
项目的 `aisoft-project-check --remote` 远程检查全 GAP，且其余治理工具在迁移后
的 profile 下不可用。本变更把 token 解析集中为一份共享实现、让 5 个工具在
过渡期同时接受两种形态（文件优先、内联弃用），补漂移防护检查，并把升级顺序
规则固化进运维手册。

## Acceptance criteria

- [ ] AC-1：5 个工具（`aisoft-project-check.sh`、`ensure-gitea-collaborator.sh`、
      `mark-deployed-issues.sh`、`sync-gitea-labels.sh`、
      `sync-gitea-repository-settings.sh`）在环境只提供 `GITEA_TOKEN_FILE`
      （mode 400/600 有效文件）时正常完成各自操作，每工具有对应测试证明。
- [ ] AC-2：`aisoft-project-check.sh --remote` 对只含 `GITEA_TOKEN_FILE` 的
      profile 不再因 token 形态对 `labels-readback`/`ci-context` 报
      `远程配置缺失: GITEA_TOKEN`；测试以等价 fixture 覆盖（remote-ready 闸门
      只取决于 env 形态），四个已迁移项目的实测读回由合并后的运维会话复核。
- [ ] AC-3：token 解析集中在唯一共享实现 `codex/agent/gitea-token.sh`，
      5 个工具全部 source 该实现，不各自复制解析逻辑；新增工具可直接复用。
- [ ] AC-4：每工具测试覆盖内联与文件两种形态，且覆盖宽权限（如 644）token
      文件 fail-closed；共享库自身有单元测试（两种形态、双形态并存文件优先、
      缺失、空文件、宽权限、符号链接、非法字符集、token 不落 stdout/argv）；
      `bash codex/tests/smoke.sh` 全绿。
- [ ] AC-5：`06-运维手册与踩坑集.md` 踩坑集新增 🕳️19，记录「共享消费者 +
      逐项目迁移」的升级顺序规则。
- [ ] AC-6（漂移防护，对应 Issue 建议 3）：新增扫描测试断言
      `codex/tools/*.sh`、`codex/agent/*.sh`、`sync/*.sh`（排除 tests 目录）中
      凡引用内联 `GITEA_TOKEN`（排除 `GITEA_TOKEN_FILE` 子串命中）的脚本，
      必须同时引用 `GITEA_TOKEN_FILE` 或 source 共享解析库，否则测试失败。

## 接口、数据与兼容性影响

### 共享解析库 `codex/agent/gitea-token.sh`

- 形态：被 source 的函数库，非可执行入口；不改变调用方 shell 选项
  （不 set -e/-u/pipefail；在解析函数内部关闭 xtrace 以防 token 经 `-x` 泄漏，
  与 5 个工具既有的脚本级 `set +x` 语义一致）；兼容 `set -u` 调用方。
- 落点理由：`install-vm.sh` 以 `codex/agent/*.sh` 通配把 agent 脚本扁平安装到
  VM `$AGENT_DIR`，且把 `ensure-gitea-collaborator.sh` 安装到同一目录；库放
  `codex/agent/` 即自动进入两种布局，无需修改安装脚本。
- 函数 `aisoft_resolve_gitea_token`，解析顺序与返回码：
  1. `GITEA_TOKEN_FILE` 非空 → 安全闸门：常规非符号链接文件、mode 400/600
     （GNU `stat -c` 优先、BSD `stat -f` 回退）、首行非空、字符集
     `^[A-Za-z0-9._-]+$`。任一违规：stderr 输出 `BLOCKED_EXTERNAL: ...`，
     返回 20，**不回退**到内联形态（fail closed）。通过：以文件首行覆盖并
     `export GITEA_TOKEN`，若调用环境同时带内联值则 stderr 提示忽略内联，
     返回 0。
  2. 否则内联 `GITEA_TOKEN` 非空 → 字符集校验（违规返回 20），stderr 输出
     弃用提示 `DEPRECATED: inline GITEA_TOKEN is deprecated; migrate this
     profile to GITEA_IDENTITY + GITEA_TOKEN_FILE (#61, #111)`，返回 0。
  3. 两者皆无 → 返回 1，不输出（缺失场景的措辞由调用方按自身合同给出）。
- token 值只进 shell 变量，随后沿既有 curl stdin config 模式传输；
  不进 argv、stdout、日志；库函数 stdout 恒为空。

### 5 个工具的接入（统一模式，逐工具保持既有退出合同）

- 统一 source 模式（双候选，兼容扁平安装布局与仓库布局）：
  优先 `<script_dir>/gitea-token.sh`，回退 `<script_dir>/../agent/gitea-token.sh`；
  两者皆缺按各工具失败合同处置（`mark-deployed-issues.sh` 警告后 exit 0，
  其余报错退出）。
- `sync-gitea-labels.sh`：必需项收敛为 `GITEA_URL/OWNER/REPO`；解析返回 1 →
  `GITEA_TOKEN_FILE or GITEA_TOKEN is required` 退出 1；返回 20 → 以 20 退出。
- `sync-gitea-repository-settings.sh`：同上，缺失时沿用该工具 usage 类退出码 2。
- `mark-deployed-issues.sh`：保持「绝不使 deployment 失败」合同——解析返回
  非 0（含 20）时 `WARN` 后 exit 0；违规详情已由库写入 stderr（fail closed 的
  含义是拒用不安全凭据、跳过标记，而非使部署管线变红）。
- `aisoft-project-check.sh`：`--remote` 就绪判定中 token 项改为调用解析库；
  返回 1 → `remote_reason='远程配置缺失: GITEA_TOKEN_FILE 或 GITEA_TOKEN'`；
  返回 20 → `remote_reason='GITEA_TOKEN_FILE 未通过安全闸门'`；两项远程检查
  照旧以该 reason 记 GAP。其余检查零变化。
- `ensure-gitea-collaborator.sh`：bot_token 回退链变为
  `GITEA_BOT_TOKEN`（显式覆盖，最高优先）→ 共享解析（文件优先、内联弃用）→
  role credential file。解析返回 20 → `blocked` 硬失败；返回 1 → 继续走
  credential file。admin_token 链路不变。
- 兼容性：内联 `GITEA_TOKEN` 在过渡期继续可用（多一条 stderr 弃用提示），
  stdout 机器可读输出与各工具退出码语义不变；纯文件形态为新增能力。
  收紧内联形态（拒绝而非弃用）不在本变更内，须待全部项目迁移完成后另立 Issue。

### 漂移防护检查

新增 `codex/tests/test-gitea-token-consumers.sh`：扫描
`codex/tools/*.sh`、`codex/agent/*.sh`、`sync/*.sh`（排除 `*/tests/*`），
对匹配内联 `GITEA_TOKEN`（正则排除 `GITEA_TOKEN_FILE`）的文件断言其同时包含
`GITEA_TOKEN_FILE` 或 `gitea-token.sh`（source 共享库）。接入 `smoke.sh`，
新消费者若只认内联形态将直接挡在 smoke。

## 治理授权（精确文件清单）

本 spec 授权且仅授权以下文件操作：

- 新增 `codex/agent/gitea-token.sh`（共享 token 解析库）
- 修改 `codex/tools/aisoft-project-check.sh`、
  `codex/tools/ensure-gitea-collaborator.sh`、
  `codex/tools/mark-deployed-issues.sh`、
  `codex/tools/sync-gitea-labels.sh`、
  `codex/tools/sync-gitea-repository-settings.sh`（仅 token 解析接入）
- 新增 `codex/tests/test-gitea-token-lib.sh`、
  `codex/tests/test-gitea-token-consumers.sh`
- 修改 `codex/tests/test-project-check.sh`、
  `codex/tests/test-ensure-gitea-collaborator.sh`、
  `codex/tests/test-mark-deployed-issues.sh`、
  `codex/tests/test-sync-gitea-labels.sh`、
  `codex/tests/test-sync-gitea-repository-settings.sh`（补两形态与 fail-closed 用例）
- 修改 `codex/tests/smoke.sh`（仅接入新测试与对应 bash -n/ShellCheck 项）
- 修改 `06-运维手册与踩坑集.md`（仅新增 🕳️19 升级顺序规则行）
- 新增 `docs/changes/111-profile-token-file/` 语义文档

清单之外的治理文件（含平台 `AGENTS.md`、`codex/config/*`、broker、CI workflow、
`codex/install-vm.sh`、`codex/tools/gitea-readonly.sh`、`codex/agent/common.sh`、
Issue #112 涉及的 `project-profile-migration.sh` 与 runtime）不在授权范围，
实施 run 不得触碰。

## 风险与回滚约束

- 单 PR revert 即完整回滚：全部为脚本/测试/文档修改，无 schema、无状态残留、
  无部署动作。
- 凭据安全：解析库复用已验证的 mode 400/600 闸门语义（`gitea-readonly.sh`/
  `common.sh` 同源），文件违规绝不回退内联；测试含 sentinel 防泄漏断言
  （argv/stdout/stderr/xtrace）。
- 行为回归风险集中在 5 个工具的既有内联路径：每工具测试保留内联形态用例，
  断言 stdout 与退出码不变（仅新增 stderr 弃用提示）。
- `mark-deployed-issues.sh` 的 fail-closed 与「不使部署失败」合同的组合已在
  接口节明确：拒用不安全凭据 + exit 0 + WARN，不产生半成品标签写入。

## 非目标

- 不重构 `gitea-readonly.sh`（#107 已适配，其内联优先的 ladder 服务于
  break-glass credential 场景）与 `codex/agent/common.sh`（已是严格文件形态）。
- 不收紧（拒绝）内联 `GITEA_TOKEN`——那是全部项目迁移完成后的独立变更。
- 不修改 `install-vm.sh`、broker manifest、CI workflow、项目 profile 本身。
- 不执行四个已迁移项目的真实远程读回（VM 侧运维复核，见 plan）。

## 未决问题

无。

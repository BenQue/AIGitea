# Codex-first Development Loop 运行时实施计划

> **归档资料：** 本文件记录 provider-neutral Loop 的首轮实施过程，不是当前执行计划。当前 source、
> provider 与启用边界见 [04](../04-Agent编排与定时任务.md) 和
> [08](../08-双工具共存与实施.md)；正文命令、测试数字和状态不得直接当作当前事实。
> 文中 checkbox 是 2026-07-16 的进度快照、不是当前待办，任何 agent 不得据此重跑任务。
>
> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 完成 Phase D3 文档迁移，并实现、测试和非生产验证 provider-neutral Development Loop；Codex 全矩阵通过后才进入 Claude Code adapter 适配。

**Architecture:** Python 3 标准库实现 classification、contract、state/lock、Gitea、verifier 和 controller；Shell 只提供 poller、Codex adapter 和安装入口。Controller 独占 Git/Gitea 状态变更，provider 只在隔离 worktree 内修改文件，verifier 独立执行合同允许的命令。

**Tech Stack:** Python 3 标准库、Bash、Git、curl、jq、Codex CLI、Gitea REST API、`unittest`、ShellCheck。

## Global Constraints

- Issue 是唯一主键；所有 Issue 必须有 `00-summary.md`，complex 还必须有 `01-spec.md` 和 `02-plan.md`。
- `type/feature`、`type/platform`、功能性更改、schema/数据迁移、外部契约、认证/安全、共享核心、跨模块、CI/部署/回滚和 Agent 治理强制为 complex。
- 信息不足或冲突时省略 `effective_complexity`，不添加 complexity 标签，并进入 `awaiting-triage`。
- `approved` 只是 Loop 启动信号；controller 必须重新校验合同，不能只信任标签。
- 第一版只允许一个 active Issue；默认 provider 为 Codex，不自动切换 Claude。
- 每个 Issue 最多 8 轮；同一根因最多连续失败 3 次；单次 provider 超时默认 2700 秒。
- 状态默认保存到 `$XDG_STATE_HOME/aisoft-loop/` 或 `$HOME/.local/state/aisoft-loop/`，凭据不得写入状态或日志。
- Provider 不得修改标签、提交、推送、开 PR、合并或部署；controller 不得自动合并或执行生产部署。
- 生产保持 script-only；AISoftPlatform 自身只做版本控制、静态验证和经明确批准的 VM 安装，不走应用部署流水线。
- 当前目录中的未跟踪 v2 脚本只作为只读 as-built 参考，不直接提交或覆盖。

---

### Task 1: 完成 Phase D3 文档迁移

**Files:**
- Modify: `02-CI与自动部署流水线.md`
- Modify: `05-通知与多人协作.md`
- Modify: `06-运维手册与踩坑集.md`
- Modify: `07-内网与生产平移路线.md`
- Modify: `09-v3平台简化与Loop-Engineering文档改造规划.md`
- Modify: `codex/tests/smoke.sh`

**Interfaces:**
- Consumes: `09` §8、§10 Phase D3 和根 `AGENTS.md` 的部署边界。
- Produces: 一致的“AI 参与首次非生产部署、生产 script-only、单 PR 合并闸门”文档合同。

- [ ] **Step 1: 增加会失败的 D3 smoke 断言**

  在 `codex/tests/smoke.sh` 检查四册分别包含 `首次部署`、`READY_FOR_REVIEW`、`标准故障包`、`生产服务器永远不需要 AI API`，并拒绝 `对应闸门` 与 `三道闸门可以分派`。

- [ ] **Step 2: 确认测试先失败**

  Run: `bash codex/tests/smoke.sh`

  Expected: non-zero，指出至少一个 D3 标记缺失或旧三闸门文本仍存在。

- [ ] **Step 3: 更新四册**

  `02` 写入首次部署验收、两次幂等执行、一次故意失败、回滚和 `03-verification.md`；`05` 改为 analysis/升级/PR ready/CI/部署/回滚通知；`06` 增加脱敏故障包；`07` 明确 controller 可在内网服务器或办公客户端，生产无 AI API。

- [ ] **Step 4: 更新迁移状态并验证**

  Run: `bash codex/tests/smoke.sh && git diff --check`

  Expected: smoke 通过；`09` 只把 Phase D3 标为完成，runtime 仍为未完成。

- [ ] **Step 5: 提交**

  ```bash
  git add 02-CI与自动部署流水线.md 05-通知与多人协作.md \
    06-运维手册与踩坑集.md 07-内网与生产平移路线.md \
    09-v3平台简化与Loop-Engineering文档改造规划.md codex/tests/smoke.sh
  git commit -m 'docs: complete v3 deployment and operations migration'
  ```

---

### Task 2: 建立 classification parser 与确定性路由

**Files:**
- Create: `codex/runtime/aisoft_loop/__init__.py`
- Create: `codex/runtime/aisoft_loop/classification.py`
- Create: `codex/runtime/tests/test_classification.py`
- Modify: `codex/tests/fixtures/classification/{small,complex,unclear}.yaml`

**Interfaces:**
- Consumes: analyzer 限定 YAML block 文本。
- Produces: `Classification.from_yaml(text) -> Classification`、`Classification.validate() -> None`、`Classification.route() -> Route`。

- [ ] **Step 1: 写 parser/routing 失败测试**

  测试必须覆盖：small、complex、unclear 省略 effective、feature 强制 complex、显式 complex 不降级、显式 small 命中风险后升级、未知字段、重复字段、非法枚举和 YAML anchor/tag 拒绝。

- [ ] **Step 2: 确认测试失败**

  Run: `PYTHONPATH=codex/runtime python3 -m unittest codex.runtime.tests.test_classification -v`

  Expected: import failure because `aisoft_loop.classification` does not exist.

- [ ] **Step 3: 实现限定 schema**

  固定字段顺序为 `change_type`、`requested_complexity`、`assessed_complexity`、条件性 `effective_complexity`、`contract_effect`、`reason`、`risk_flags`、`required_docs`、`confidence`、`override_reason`。仅接受标量和 `- item` 列表；禁止通用 YAML 对象构造。

- [ ] **Step 4: 运行测试**

  Run: `PYTHONPATH=codex/runtime python3 -m unittest codex.runtime.tests.test_classification -v`

  Expected: all classification tests pass.

- [ ] **Step 5: 提交**

  ```bash
  git add codex/runtime codex/tests/fixtures/classification
  git commit -m 'feat: add deterministic issue classification parser'
  ```

---

### Task 3: 实现合同加载与启动校验

**Files:**
- Create: `codex/runtime/aisoft_loop/contract.py`
- Create: `codex/runtime/tests/test_contract.py`
- Create: `codex/runtime/tests/fixtures/repos/{small,complex,unclear}/`

**Interfaces:**
- Consumes: repo path、Issue JSON、标签名称、`docs/changes/N/`。
- Produces: `load_contract(repo, issue) -> Contract`；失败抛出 `ContractError(terminal_state, lifecycle_label, reasons)`。

- [ ] **Step 1: 写失败测试**

  覆盖 small 合同完整、small 缺可测验收、complex 缺 spec、complex 缺 plan、unclear、标签冲突、summary issue/branch 不匹配、强制风险伪装 small、governing `AGENTS.md` self-mod 请求。

- [ ] **Step 2: 确认测试失败**

  Run: `PYTHONPATH=codex/runtime python3 -m unittest codex.runtime.tests.test_contract -v`

  Expected: import failure because `aisoft_loop.contract` does not exist.

- [ ] **Step 3: 实现 front matter 与合同规则**

  只解析模板定义的受限 YAML；检查 Issue open、`approved`、单一 type/complexity、`change/N`、summary 字段、Acceptance criteria；complex 强制 spec/plan，无未决问题；普通 worker 永不修改本运行 governing `AGENTS.md`。

- [ ] **Step 4: 运行测试**

  Run: `PYTHONPATH=codex/runtime python3 -m unittest codex.runtime.tests.test_contract -v`

  Expected: all contract tests pass.

- [ ] **Step 5: 提交**

  ```bash
  git add codex/runtime/aisoft_loop/contract.py codex/runtime/tests
  git commit -m 'feat: validate loop contracts before execution'
  ```

---

### Task 4: 实现原子状态、全局锁和重试预算

**Files:**
- Create: `codex/runtime/aisoft_loop/state.py`
- Create: `codex/runtime/tests/test_state.py`

**Interfaces:**
- Produces: `StateStore.load/save(issue)`、`GlobalLock.acquire()`、`LoopBudget.record_failure(root_cause)` 和四种终态枚举。

- [ ] **Step 1: 写失败测试**

  覆盖原子写入、损坏 JSON 拒绝、0600 mode、凭据字段拒绝、第二进程锁冲突、8 轮限制、同根因第 3 次进入 `FAILED_LIMIT`、根因变化重置连续次数。

- [ ] **Step 2: 确认测试失败**

  Run: `PYTHONPATH=codex/runtime python3 -m unittest codex.runtime.tests.test_state -v`

  Expected: import failure because `aisoft_loop.state` does not exist.

- [ ] **Step 3: 实现状态与锁**

  使用同目录临时文件、`fsync`、`os.replace` 和 `fcntl.flock(LOCK_EX|LOCK_NB)`；拒绝 key 名含 token/password/secret/auth/credential。

- [ ] **Step 4: 运行测试并提交**

  Run: `PYTHONPATH=codex/runtime python3 -m unittest codex.runtime.tests.test_state -v`

  Expected: all state tests pass.

  Commit: `git commit -am 'feat: add loop state and single-issue lock'`（先显式 `git add codex/runtime`）。

---

### Task 5: 实现 verifier 与安全命令合同

**Files:**
- Create: `codex/runtime/aisoft_loop/verifier.py`
- Create: `codex/runtime/tests/test_verifier.py`
- Create: `templates/loop/verification.json`

**Interfaces:**
- Consumes: 版本化 JSON command array，每项为 argv array、timeout、required。
- Produces: `Verifier.run_all(cwd) -> VerificationReport`，保留 exit code 和脱敏后的有限输出。

- [ ] **Step 1: 写失败测试**

  覆盖 argv 执行而非 shell、timeout、required failure、optional failure、输出截断、token/Authorization/.env 脱敏、空命令拒绝、路径越界拒绝。

- [ ] **Step 2: 确认测试失败**

  Run: `PYTHONPATH=codex/runtime python3 -m unittest codex.runtime.tests.test_verifier -v`

  Expected: import failure because `aisoft_loop.verifier` does not exist.

- [ ] **Step 3: 实现 verifier**

  使用 `subprocess.run(argv, shell=False, cwd=worktree, timeout=...)`；环境仅继承 allowlist；每个输出最多 64 KiB；报告不保存完整环境。

- [ ] **Step 4: 运行测试并提交**

  Run: `PYTHONPATH=codex/runtime python3 -m unittest codex.runtime.tests.test_verifier -v`

  Expected: all verifier tests pass.

  Commit: `git commit -m 'feat: add deterministic loop verifier'` after staging listed files.

---

### Task 6: 实现 provider-neutral Gitea adapter

**Files:**
- Create: `codex/runtime/aisoft_loop/gitea.py`
- Create: `codex/runtime/tests/test_gitea.py`

**Interfaces:**
- Produces: `GiteaClient.get_issue/set_labels/comment/create_pr/get_pr/get_commit_status`；HTTP transport 可注入 mock。

- [ ] **Step 1: 写失败测试**

  覆盖 token 只进入 header、不进入 URL/异常/日志；标签三维互斥；unclear 清 complexity；PR body 含 `Closes #N` 和合同文档；CI pending/success/failure 映射；429/5xx 有界退避；4xx 不盲重试。

- [ ] **Step 2: 确认测试失败**

  Run: `PYTHONPATH=codex/runtime python3 -m unittest codex.runtime.tests.test_gitea -v`

  Expected: import failure because `aisoft_loop.gitea` does not exist.

- [ ] **Step 3: 实现 adapter**

  使用 `urllib.request` 和注入 transport；仅 API client 拥有标签、评论和 PR mutation；任何异常先移除 Authorization 后再格式化。

- [ ] **Step 4: 运行测试并提交**

  Run: `PYTHONPATH=codex/runtime python3 -m unittest codex.runtime.tests.test_gitea -v`

  Expected: all Gitea tests pass.

  Commit: `git commit -m 'feat: add provider-neutral Gitea adapter'` after staging listed files.

---

### Task 7: 实现 Codex adapter 与 Loop controller

**Files:**
- Create: `codex/runtime/aisoft_loop/provider.py`
- Create: `codex/runtime/aisoft_loop/controller.py`
- Create: `codex/runtime/aisoft_loop/cli.py`
- Create: `codex/runtime/tests/test_controller.py`
- Create: `codex/agent/loop-controller.sh`
- Create: `codex/agent/codex-provider.sh`

**Interfaces:**
- Provider input: JSON 文件，含 immutable contract、当前 task、failure evidence、allowed paths、禁止动作。
- Provider output: JSON 文件，字段固定为 `status`、`summary`、`changed_files`、`root_cause`、`escalation`。
- Controller output: `READY_FOR_REVIEW`、`NEEDS_HUMAN_DECISION`、`BLOCKED_EXTERNAL`、`FAILED_LIMIT` 或 `CONTINUE`。

- [ ] **Step 1: 写 controller 失败测试**

  使用 fake provider/Gitea/verifier/git 覆盖：happy path、普通失败后修复、范围扩张升级、同因 3 次、总轮数、外部阻塞、CI failure feedback、PR success、永不 merge/deploy、provider 输出越权文件拒绝。

- [ ] **Step 2: 确认测试失败**

  Run: `PYTHONPATH=codex/runtime python3 -m unittest codex.runtime.tests.test_controller -v`

  Expected: import failure because controller modules do not exist.

- [ ] **Step 3: 实现最小状态机**

  顺序固定为 load/revalidate contract → acquire worktree/lock → provider turn → changed-path check → verifier → commit/push → create/read PR → CI poll → terminal/update state。任何 mutation 前重新检查 issue/labels。

- [ ] **Step 4: 实现 Codex wrapper**

  `codex-provider.sh` 使用 `codex exec --ephemeral --sandbox workspace-write --ask-for-approval never`，不拼接 shell 字符串；controller 用文件传入 JSON，并校验 provider JSON schema。

- [ ] **Step 5: 运行测试、语法和 ShellCheck**

  ```bash
  PYTHONPATH=codex/runtime python3 -m unittest discover -s codex/runtime/tests -v
  bash -n codex/agent/loop-controller.sh codex/agent/codex-provider.sh
  shellcheck codex/agent/loop-controller.sh codex/agent/codex-provider.sh
  ```

  Expected: all pass.

- [ ] **Step 6: 提交**

  Commit: `git commit -m 'feat: add Codex-first development loop controller'` after staging Task 7 files.

---

### Task 8: 迁移 analyzer、poller 和安装入口

**Files:**
- Create: `codex/agent/common.sh`
- Create: `codex/agent/analyze-codex.sh`
- Create: `codex/agent/provider-poll.sh`
- Create: `codex/install-vm.sh`
- Create: `codex/tests/test-agent-runtime.sh`
- Modify: `codex/tests/smoke.sh`

**Interfaces:**
- `analyze-codex.sh N`: 只读 provider 分析，wrapper 校验、写 `change/N` summary、更新标签/评论。
- `provider-poll.sh`: `needs-analysis` 调 analyzer；`approved` 调 controller；全局锁冲突正常跳过。
- `install-vm.sh`: 复制 skills/runtime/scripts，不复制凭据，不启用 timer/provider。

- [ ] **Step 1: 写 mock 失败测试**

  Mock curl/git/codex，覆盖 small/complex/unclear 路由、单一 `change/N`、token 不在 argv/stdout/stderr、provider 不改标签、poller `IMPLEMENT_PROVIDER=none`、安装幂等且不覆盖已有 config/credentials。

- [ ] **Step 2: 确认测试失败**

  Run: `bash codex/tests/test-agent-runtime.sh`

  Expected: non-zero because tracked runtime scripts do not exist.

- [ ] **Step 3: 实现 wrappers 与安装**

  从 as-built 行为迁移但不复制其 v2 `spec/N`、旧 summary 标题、明文 Authorization argv 或 one-shot implementation 语义。

- [ ] **Step 4: 全量验证并提交**

  ```bash
  bash codex/tests/test-agent-runtime.sh
  bash codex/tests/smoke.sh
  bash -n codex/agent/*.sh codex/install-vm.sh
  shellcheck codex/agent/*.sh codex/install-vm.sh
  PYTHONPATH=codex/runtime python3 -m unittest discover -s codex/runtime/tests -v
  ```

  Expected: all pass; no credential value appears in test output.

  Commit: `git commit -m 'feat: route Gitea issues through v3 loop runtime'` after staging Task 8 files.

---

### Task 9: 完成 pilot governance 与 synthetic matrix

**Files:**
- Modify in pilot: `worktrees/rsdesign-issue-8/AGENTS.md`
- Create in pilot: `docs/changes/8/03-verification.md`
- Modify: `09-v3平台简化与Loop-Engineering文档改造规划.md`
- Modify: `08-Codex双工具共存与实施.md`

**Interfaces:**
- Consumes: Issue #8 AC-1–AC-8 和 Tasks 2–8 runtime。
- Produces: fresh-run governance evidence 与 synthetic small/complex/unclear/override/terminal matrix。

- [ ] **Step 1: 受控治理步骤应用 AC-8**

  当前中央 worker 不受 pilot `AGENTS.md` 治理，只应用已批准的 self-mod proposal；提交并推送 `change/8`。不得同时修改产品代码。

- [ ] **Step 2: fresh verifier 重新读取**

  启动新的只读 Codex `exec --ephemeral`，读取 pilot `AGENTS.md` 和 Issue #8 spec，断言普通 worker 永远不修改 governing `AGENTS.md`，并把真实输出写入 verification。

- [ ] **Step 3: 运行 synthetic matrix**

  ```bash
  PYTHONPATH=codex/runtime python3 -m unittest discover -s codex/runtime/tests -v
  bash codex/tests/test-agent-runtime.sh
  bash codex/tests/smoke.sh
  ```

  Expected: small、complex、unclear、explicit override、scope escalation、CI feedback 和四种终态全部有自动测试证据。

- [ ] **Step 4: 更新状态并提交**

  只把 synthetic 与 governance 项标为完成；真实 Issue、VM 安装和非生产部署仍保持未完成。

---

### Task 10: 真实 pilot、VM 安装与通用平台边界验收

**Files:**
- Modify in pilot: `docs/changes/<small-issue>/00-summary.md`
- Modify in pilot: `docs/changes/<small-issue>/03-verification.md`
- Modify in pilot: `docs/changes/8/03-verification.md`
- Modify: `README.md`
- Modify: `04-Agent编排与定时任务.md`
- Modify: `08-Codex双工具共存与实施.md`
- Modify: `09-v3平台简化与Loop-Engineering文档改造规划.md`

**Interfaces:**
- Produces: 一个明确标注的真实 complex pilot PR/CI、VM 可回滚安装、通用每项目 profile，以及“应用项目部署验收不等于平台仓库部署”的边界证据。

- [x] **Step 1: 重新 GET 外部基线**

  读取 VM service/timer、provider 配置、16 标签、Issue #8、开放 PR、pilot branch 和 test environment health；只记录脱敏信息。

- [x] **Step 2: 纠正项目承载边界**

  rsdesign-new Issue #10 曾作为 real small 候选创建，Codex 只读分析判定为 docs/small 并生成 summary；用户随即明确平台流程不得由 rsDesign 专用仓库承载。该 Issue 已取消关闭，未实现、未建 PR、未合并、未部署，analysis branch 仅保留审计。共享 small 路由继续由 synthetic tests 覆盖；真实 small 改为每个新 profile 自己的接入验收，不再是 AISoftPlatform 或 Claude adapter 的项目专用完成条件。

- [x] **Step 3: 在临时目标安装 runtime**

  先对临时 HOME 连续运行两次 `codex/install-vm.sh`，比较文件清单与 mode；再备份 VM 当前 agent 目录并安装，但保持 timer 停止和 `IMPLEMENT_PROVIDER=none`。

- [x] **Step 4: 验证通用 small 路由而不制造应用 PR**

  使用共享 classification/contract/controller synthetic matrix 验证 docs/bug/test/refactor small、范围升级、verifier failure 和 CI feedback。每个接入项目再用自己的真实 Issue、技术栈和 CI 验证，不从 rsDesign pilot 继承结论。

- [x] **Step 5: 运行 Issue #8 complex Loop**

  重新校验 spec/plan 和 `approved`，由 controller 完成范围内剩余变更、创建最终 PR并读取 CI；最终停在 `READY_FOR_REVIEW`，不自动合并。

  2026-07-16 已完成：首次运行捕获 worktree stdout 污染并安全停止；`bb0d5d5` 修复和回归后，PR #9 CI 通过并停在人工合并闸门，随后由人合并且测试环境健康。原计划在同一 pilot 继续 real small，后被用户的通用平台边界澄清 supersede；后续 small 属于每项目 profile 验收。

- [x] **Step 6: 分离平台完成条件与应用部署验收**

  AISoftPlatform 是文档、模板、skills 和 runtime source，不需要应用部署流水线。rsdesign-new 合并后测试健康只作为已有 as-built/pilot 证据；两次幂等部署和故意失败回滚仍是每个有部署范围的应用 profile 接入门禁，不是共享 controller 或 Claude adapter 的专用前置条件。

- [x] **Step 7: 记录与收尾验证**

  已更新中央状态与边界；`bash codex/tests/smoke.sh` 通过 72 项 Python tests、ShellCheck、label/profile/install mocks，VM 临时安装和 systemd verify 通过，`git diff --check` 通过。pilot PR #9 merged、Issue #8 closed、测试两个健康入口为 `ok`；误建 Issue #10 closed 且无实现 PR。

- [ ] **Step 8: 提交但不自动合并**

  中央 runtime 分支已提交；pilot PR #9 已由人合并。GitHub push 因分支包含内部 Gitea/VM 地址和验证细节被安全策略拒绝，必须在用户知晓该外发风险后另行明确批准；未绕过策略，也未自动合并中央 `main`。

### Task 11: 每项目 profile 与去专用化

**Files:**
- Create: `codex/agent/project-poll.sh`
- Create: `codex/systemd/aisoft-agent@.service`
- Create: `codex/systemd/aisoft-agent@.timer`
- Create: `templates/agent/project.env.example`
- Modify: `codex/install-vm.sh`
- Modify: `codex/tests/test-agent-runtime.sh`
- Modify: `README.md`、`04`、`08`、`09`、global/composite/ops skills 和 onboarding runbook

**Interfaces:**
- Consumes: 现有 `provider-poll.sh`、`AGENT_ENV_FILE`、`AISOFT_LOOP_STATE_DIR` 和 `LOOP_WORKTREE_ROOT`。
- Produces: `<profile>.env → project-poll → shared provider-poll`，每项目独立 state/lock/worktrees，systemd template 安装但不 enable/start。

- [x] **Step 1: 先写 profile 隔离回归**

  断言 installer 复制 project wrapper 与两个 unit、不生成 profile/凭据；断言 profile traversal 和非 400/600 mode 被拒绝，state/worktrees 位于项目 namespace。测试先因文件不存在而失败。

- [x] **Step 2: 实现最小通用入口**

  `project-poll.sh` 只选择 profile、校验权限、设置 namespace 并 exec 共享 poller。systemd unit 只调用 wrapper；installer 不 daemon-reload、不 enable、不 start。

- [x] **Step 3: 完整中央与 VM 临时安装验证**

  运行 smoke、72 项 Python tests、ShellCheck、两次临时 HOME manifest、profile mock 和 VM `systemd-analyze verify`；真实结果写回状态文档。

  结果：中央 smoke 通过；VM 一次性 HOME 两次安装一致，共 35 files / 7 scripts；没有 profile、credential 或 timer enablement；两个 systemd template 通过 verify。唯一输出警告来自既有 `/etc/systemd/system/mailpit.service` 的 `nobody` 用户，与本候选无关。

- [x] **Step 4: 提交并形成 Claude Code handoff**

  中央通用化提交为 `2f34778`；所有真实 project timer 保持 disabled。Claude adapter 只替换 provider，不复制 profile、state、Git/Gitea 或 verifier。

## 完成定义与 Claude Code handoff

以下全部满足后，共享 Codex 阶段才算完成：Phase D3 一致；runtime 自动测试全绿；pilot governance fresh-run 通过；至少一个明确标注的 real integration pilot 到达 `READY_FOR_REVIEW` 并由人决定合并；临时/VM 安装可回滚；每项目 profile 和 state/worktree 隔离通过；没有自动合并或生产部署。真实 small、CI failure feedback 和非生产部署/回滚由共享 synthetic 加各目标项目接入矩阵共同承担，不要求 AISoftPlatform 自身部署，也不允许把 rsDesign 固化进 adapter。

Claude Code 适配另开 complex 变更，只实现 provider adapter 和 parity 测试，复用相同 controller、state、lock、Gitea、verifier、标签、终态和验证矩阵，不复制状态机。

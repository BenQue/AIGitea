# 新项目接入 AISoft 平台 · v3 Runbook

> 本 runbook 面向任意 Gitea 项目。rsdesign-new 只是历史试点证据，不是默认仓库、目录、端口或部署合同。按顺序完成，每步验收后再继续；目标项目未通过自己的验收前保持 implementation disabled。

## 1. 参数与仓库

先确定唯一 profile 名称，再确定 `GITEA_URL`、`OWNER`、`REPO`、本地只读/工作克隆、技术栈、测试命令与 verifier 配置。只有应用项目才需要应用端口、Nginx 端口、健康端点、数据存储和回滚方式；纯文档或平台规范仓库不需要虚构部署流程。

把仓库放到 Gitea，验证历史完整、默认分支正确、Mac/内网客户端可以 clone 和 push feature branch。随后由 owner/admin 创建并回读 `main` 保护：禁止 direct/force push，保留目标 CI context，并启用不含 `ci-bot` 的 merge allowlist。collaborator gate 只验证并保持该规则，不负责创建或放宽保护。

### 1.1 Mandatory `ci-bot` collaborator gate

对每个通过 AISoftPlatform skill 初始化、接入或准备部署的本地 Gitea **软件仓库**，在 owner/admin 已创建上述 `main` 保护之后、标签、project profile、Analyzer、Loop、CI 或部署配置之前，必须运行：

```bash
AISOFT_ONBOARDING_MODE=software-repository \
GITEA_URL=<exact-gitea-url> \
GITEA_OWNER=<exact-owner> \
GITEA_REPO=<exact-repo> \
GITEA_EXPECT_URL=<exact-gitea-url> \
GITEA_EXPECT_OWNER=<exact-owner> \
GITEA_EXPECT_REPO=<exact-repo> \
GITEA_ADMIN_CREDENTIAL_FILE=/home/benque/gitea-ci-credentials.txt \
GITEA_BOT_CREDENTIAL_FILE=/home/benque/gitea-ci-credentials.txt \
/mnt/mac/Users/benque/MyDocs/AISoftPlatform/codex/tools/ensure-gitea-collaborator.sh
```

先以 `coder` 身份从 mode 600 project profile 只读解析非 secret 的 URL/owner/repo，再在能读取 VM-local 管理员与 `ci-bot` credential file 的 `benque` operator context 运行上述 gate。不得输出 profile/token，也不得把 token 复制到 Mac 或命令参数。若 VM 尚未安装候选工具，只能在关联平台 PR 已合并后使用 AISoftPlatform 权威 source；不得把未合并 candidate 复制到全局稳定目录。工具合同：

- collaborator 固定为统一的 `ci-bot`，permission 固定为精确 `write`；没有任意用户或 `admin` 参数。
- 当前为 `write` 时不 PUT；缺失或 `read` 时单次 PUT，随后分别以管理身份和 `ci-bot` 身份回读 `write`。
- 管理身份在写前/写后回读 `main` branch protection；禁止 direct/force push，`ci-bot` 不得进入 push、force-push 或 merge allowlist，原有 status-check/approval/merge 字段必须保持不变。Gitea 1.26.4 的 branch-protection GET 对普通 `write` collaborator 返回 `403`，不得为让 bot 调用该管理端点而升级其权限。
- `ci-bot` 还必须以自身 token GET 目标 private repository，作为真实访问证据。
- 任一 credential、API、permission、branch protection 或 bot-access 验证失败，终止全部后续接入并报告 `BLOCKED_EXTERNAL`。
- token 只能来自 mode 400/600 profile/credential file，经 curl stdin config 使用，不能出现在 argv、日志、输出、Git config 或仓库内容中。

已有仓库的回补先使用同一工具的 `--check`。只从明确 AISoftPlatform project profiles/接入记录生成 `repository/current_permission/main_protection/planned_action` 清单并等待人工确认；不得枚举全部 Gitea 仓库后批量授权，不得自动纳入 AISoftPlatform 等平台控制仓库。

## 2. 共享项目契约

在仓库加入：

- 项目真实命令和禁令对应的 `AGENTS.md`。
- 一行 `@AGENTS.md` 的 `CLAUDE.md`。
- 从平台仓库 `templates/docs/changes/_template/` 复制 `00-summary.md`、`01-spec.md`、`02-plan.md`、`03-verification.md`。
- lockfile、包管理源和固定运行时版本。
- 能检查关键依赖的健康端点。

所有 change 文档的共同 front matter 至少包含 `issue`、`gitea_url`、`change_type`、`requested_complexity`、`assessed_complexity`、`effective_complexity`、`contract_effect`、`confidence`、`risk_flags`、`status`、`branch`、`pr_url`、`created` 和 `updated`。`00-summary.md` 另外保存 analyzer 的 `reason`、`required_docs` 和 `override_reason`；`needs-human-decision` summary 必须在 front matter 和 `## AI 判级` YAML 中都省略 `effective_complexity`，且不得创建 complex spec/plan。

## 3. CI 与部署

适配 PR CI、main 部署、pack、deploy、health-check、promote 和 rollback。保留：

- 构建产物完整性检查。
- 不可变制品和环境配置分离。
- 数据备份和向后兼容迁移。
- SQLite 的停应用后迁移。
- PM2 delete+start 与 online 断言。
- HTTP health check 和失败回滚。

AI 可以参与开发/测试环境首次部署。把所有成功手工步骤固化为脚本，连续运行两次，并故意制造一次失败验证回滚。把真实结果写入关联 Issue 的 `03-verification.md`。生产只执行验收后的脚本。

## 4. Gitea 治理

- 先通过 §1.1 collaborator gate，给 `ci-bot` 精确 `write` 仓库权限，用于 private read、Issue/评论/标签、受控 feature branch 和 PR；不给 `admin` 或合并权。
- 保护 `main`，禁止直接 push，要求准确的 `CI / test (pull_request)` context。
- 建七个类型标签：`type/bugfix`、`type/feature`、`type/docs`、`type/test`、`type/refactor`、`type/maintenance`、`type/platform`。它们是 Issue 作者可提供、AI 按证据校验的变更类型输入。
- 建两个互斥的复杂度标签：`complexity/small`、`complexity/complex`。它们是 AI 判级后的输出；无法安全判级时两者都不添加。
- 建八个标签：`needs-analysis`、`awaiting-triage`、`spec-drafting`、`spec-review`、`approved`、`pr-open`、`completed`、`deployed`。
- 使用单一 `change/N` 分支和最终 PR `Closes #N`。

三个维度正交：`type/*` 是变更类型输入，`complexity/*` 是 AI 有效复杂度输出，八个无前缀标签是生命周期状态。`needs-analysis` 触发 analyzer；`approved` 启动 Loop；`spec-review` 只是可选协作状态；`pr-open` 等最终 CI/review；`completed` 表示最终 PR 已合并且明确无需部署；`deployed` 表示确定性部署和验证完成。两个交付终态互斥。

## 5. Analyzer 接入

- 从 `templates/agent/project.env.example` 复制到 VM 的 `~/.config/aisoft/projects/<profile>.env`，填入该项目自己的 Gitea 坐标、token 和 `AGENT_REPO_DIR`，设为 mode 600；不得提交该文件。
- 每个 profile 使用 `~/.local/state/aisoft-loop/projects/<profile>/` 保存锁、Issue state 和 worktrees，不与其他仓库共享。
- 为项目准备只读工作克隆和依赖/索引。
- 安装 `$aisoft-platform` 与 `$gitea-analyze-change`。
- 先用低风险 Issue 验证：读取 evidence、输出五节 summary，并以 `change_type`、`requested_complexity`、`assessed_complexity`、`effective_complexity`、`contract_effect`、`risk_flags`、`required_docs`、`confidence` 和 `override_reason` 确定性判级。
- 用功能新增验证 `type/feature` 和 `effective_complexity: complex`；用信息不足的 Issue 验证 `needs-human-decision`、`contract_effect: unclear` 且不输出 `effective_complexity`。
- Analyzer 不修改产品代码、Git 或 Gitea 标签/评论，不创建最终 PR、不部署；wrapper/controller 负责 `00-summary.md`、分支、评论和标签状态变更。
- 普通实现 worker 永远不得编辑约束本次运行的 `AGENTS.md`。complex spec 只能授权其生成治理 patch/proposal；目标文件之外的独立受控治理步骤负责应用，随后用 fresh run 验证并采用新规则。其他 protected files 仍要求 complex spec 精确列出文件、验证与回滚。

## 6. Development Loop 接入

只在平台 `08` 的 Codex skills 和 controller 验证完成后启用：

- 使用 provider-neutral controller；不要为 Codex/Claude 复制两套 Loop。
- 每个 active Issue 使用隔离 worktree 和锁。
- 第一阶段只运行一个 active Issue。
- 外层 verifier 独立运行项目命令，不信任模型自述。
- 同一根因三次失败、合同冲突、范围扩张或高风险决策时升级给人。
- 最终状态只允许 `READY_FOR_REVIEW`、`NEEDS_HUMAN_DECISION`、`BLOCKED_EXTERNAL`、`FAILED_LIMIT`。
- 只有人可以合并最终 PR。
- 使用 `aisoft-agent@<profile>.service/.timer` 作为项目级 systemd 实例；安装模板不等于启用。必须显式执行 `systemctl --user enable --now aisoft-agent@<profile>.timer`，且只有该项目验收通过后才允许这样做。

## 7. 接入验收

按顺序验证：

1. Trivial PR 的 CI context 正确且受分支保护约束。
2. 合并后测试环境确定性部署和健康检查通过。
3. Analyzer 对真实 Issue 输出确定性分类，wrapper/controller 写入正确且互斥的标签。
4. Small Issue 从明确合同进入 Loop 并准备绿色 PR。
5. Complex Issue 缺 spec/plan 时拒绝，补齐后按 plan 执行。
6. 普通测试失败由 Loop 自修复。
7. 合同冲突、外部阻塞和三次同因失败正确升级。
8. CI failure feedback 能进入下一轮。
9. 非生产首次部署执行两次并完成故意失败回滚。
10. 生产负向测试证明 provider 无生产部署权限。

中央 Codex runtime/adapter 先通过共享 synthetic 与至少一个明确标注的 pilot；每个新项目仍需完成与自身技术栈、CI 和部署范围对应的验收。随后 Claude adapter 复用同一 profile、controller、verifier 和状态合同，不复制项目专用状态机。

### 合并后收尾

1. 明确无需部署的变更在最终 PR 合并后，把唯一 lifecycle 更新为 `completed`；
   需要部署的应用不得使用该标签。
2. 把 `codex/tools/mark-deployed-issues.sh` 复制或以固定版本纳入应用仓库，并只在
   应用健康检查成功后调用；工具会把包括 `completed` 在内的其它 lifecycle 替换为
   唯一 `deployed`。
3. 用显式 `GITEA_URL/GITEA_OWNER/GITEA_REPO` 运行
   `codex/tools/sync-gitea-repository-settings.sh`，读回 merge 后删除源分支为 true。
4. 在应用自身 PR 中验证多 `Closes #N`、标签保留、API 失败 best-effort 和
   `--disable` 回滚；平台仓库验证不能替代应用验收。

### GitHub 入站项目

1. 从 `sync/templates/project.env.example` 创建 600 profile；GitHub 与 Gitea token
   分别存为 400/600 文件，不写入 profile、argv 或 Git config。
2. 运行 `sync/install.sh` 两次确认幂等。安装完成后 timer 必须仍为
   disabled/inactive。
3. 只运行 one-shot `inbound-sync.sh reconcile <profile>`，验证同 SHA 幂等、
   新 SHA 建不可变分支与 PR、history rewrite/conflict fail closed、secret redaction。
4. 真实读回 bot 不能 push/merge `main`，并由目标仓库 PR CI 与内部审批重新授权。
5. 以上证据写入该项目 `03-verification.md` 后，才可单独批准 enable timer。

## 8. 安全回滚

在 Loop 试点前记录当前 timer、provider、agent 脚本、工作树、开放 Issue/PR 和标签状态。保持 `IMPLEMENT_PROVIDER=none`，直到专项实施明确启用新 controller。

试点失败时停止 controller，保留 analyzer，开发回到 Mac 人机交互；CI、制品和生产部署不受影响。未经单独批准，不删除旧脚本、认证或 provider 配置。

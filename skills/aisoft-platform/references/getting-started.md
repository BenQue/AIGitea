# 新用户上手指南 · 带用户开始第一个项目

本指南写给 AI 工具执行：用户说「带我上手 AISoft 平台」「帮我配好环境开始新项目」时，按下面的顺序一步一步带用户走。
给人读的一页概览是平台仓 `usage/USER-GUIDE.md`；流程合同以项目内 `.aisoft/platform-usage.md` 为准，本指南只做引导，不复述合同。

## 执行规则

- **一次一步**：每步先说要做什么、谁来做，执行或请用户执行，再跑核对命令，读到预期结果才进入下一步。
- **读不到预期就停**：把命令、实际输出和本步的「失败时」一栏报告给用户，不换别的办法绕过去。
- **分清谁做**：标着「维护者」的步骤需要 sudo、改平台 manifest 或注册 marketplace，AI 不代执行，只把命令交给用户或维护者，等对方回复后再读回。
- **不碰凭据**：不打印、不复制 token、密码、`.env`、认证文件；登录由用户在工具自己的界面里完成。
- **先问清工具**：开始前问用户用哪一种（Claude Code、Codex、Cursor，可以多选），后面只走所选工具的小节。

## 第 0 步：认清两种角色

| 角色 | 负责 | 本指南中的标记 |
|---|---|---|
| 平台维护者 | 安装 host-access broker、在平台 manifest 里登记新项目、把使用发布包采用进项目 | 维护者 |
| 开发者 | 本机登录所选工具、核对技能与版本、在项目里开 Issue 和开发 | 开发者 |

一个人可以同时是两种角色；即便如此，维护者步骤也由用户本人执行。

## 第 1 步：所有工具共用的本机前提（开发者核对，缺了找维护者）

1. **命令行工具**：`bash`、`python3`、`jq`、`rg`、`git` 都能找到。核对：`command -v bash python3 jq rg git`，五行路径都有输出。
   失败时：报告缺哪个，请用户自行安装后重跑。
2. **host-access broker（维护者）**：一切 Gitea 与 Git 远端访问都经 `/usr/local/libexec/aisoft/host-access-broker`。
   它由维护者在平台检出里运行 `codex/install-host-access-broker.sh` 安装（需要 sudo）。
   开发者核对：`/usr/local/libexec/aisoft/host-access-broker --project <项目 id> --operation git.fetch.main`，在项目检出里运行，
   返回 JSON 的 `status` 为 `PASS`。
   这只证明本机能经 broker 连到该项目，不证明接入已验收（接入验收见第 3 步）。
   失败时：把返回体的 `code` 与 `message` 原样报告。`requested project is not explicitly managed` 说明项目还没登记，转第 3 步；
   `requested operation is not allowlisted` 是本机操作表比平台旧，请维护者重装 broker，不要往权限方向查；其它 `REQUEST_DENIED` 是合同拒绝，照原文报告。
3. **私有 Gitea**：匿名访问得到 `404` 不说明对象不存在，不要据此下结论，一律经 broker 读取。

## 第 2 步：按所选工具准备本机

项目级技能（`aisoft-platform`、`issue-session-flow` 等）随使用发布包进入项目仓（第 4 步），打开项目就能用，
开发者不需要往用户目录装平台技能。下面只处理每个工具自己的登录与外部技能包。

### Claude Code

1. **登录**：用户在终端运行 `claude`，按提示完成登录。核对：`claude --version` 有版本输出（CLI 可用），`claude auth status` 读到 `"loggedIn": true`（已登录）。
2. **superpowers**：从 Claude 官方市场安装，在 Claude Code 会话里运行 `/plugin install superpowers@claude-plugins-official`（用户执行）。
3. **Matt 技能包**：Claude 侧由平台自有 marketplace 钉版本。用户在会话里运行
   `/plugin marketplace add <平台检出路径>`，再运行 `/plugin install mattpocock-skills@aisoft-platform`；这是本机 installed 层动作，由用户本人执行。
   核对（在平台检出里）：`bash skill-for-claude/check-plugin-pin.sh` 首行为 `PIN_CLEAN`。
   失败时：`PIN_DRIFT` 或 `PIN_NOT_INSTALLED` 不要声称已就绪，报告给用户，由用户决定是否重装。

### Codex

1. **登录**：用户在终端运行 `codex`，按提示完成登录。核对：`codex --version` 有版本输出（CLI 可用），`codex login status` 读到已登录。
2. **superpowers**：从 Codex 官方插件市场安装（用户在 Codex 的插件管理里操作）。
   官方市场拿不到平台 pin 的版本时，版本核对会读到 `PIN_NOT_INSTALLED`，这是已登记的外部限制，不阻塞开发。
3. **Matt 技能包与 `aisoft-matt-workflow`**：随发布包进入项目级 `.agents/skills/`，开发者不需另装。

### Cursor

1. **登录**：用户运行 `cursor-agent login` 完成登录。核对：`cursor-agent status` 显示已登录。
2. **技能与规则**：全部在项目里——`.cursor/skills/`（平台技能、Matt 与 superpowers 快照）与 `.cursor/rules/aisoft-platform.mdc`。
   平台不往用户目录安装任何东西，开发者也不需要另装插件。
3. 采用发布包时要带 Cursor（第 4 步的 `--tools` 含 `cursor`），否则项目里没有这些落点。

### 本机外部技能包版本读回（必需，用平台检出里的维护层工具）

在平台检出里运行 `bash codex/tools/check-external-skill-versions.sh`。它一次报告所有工具，只看所选工具的行，不以最后的
`RESULT` 行作为门槛（那一行也会因为没选的工具而变成 `REVIEW_NEEDED`）。

| 所选工具 | 看哪几行 | 预期 |
|---|---|---|
| Claude Code | `SUPERPOWERS claude`、`MATT claude` | 都是 `PIN_CLEAN` |
| Codex | `SUPERPOWERS codex` | `PIN_CLEAN`，或已登记的 `PIN_NOT_INSTALLED`（官方市场没有 pin 版本，不阻塞） |
| Cursor | 本步不看，技能在项目里，第 4 步采用后再核对 | - |

失败时：所选工具的行出现 `PIN_DRIFT`（版本与平台 pin 不同）或 `UNKNOWN`（读不懂本机状态）就停下，请维护者先过 `08` §5 的适配清单再继续。

### 平台仓维护者附加（维护层，可选）

只在维护平台仓本身时，把平台技能另装到某个用户目录，安装与读回传同一个目标 home：Claude 侧
`bash skill-for-claude/install.sh <目标 home>` 后 `bash skill-for-claude/check-drift.sh <目标 home>` 读到 `CLEAN`；Codex 侧
`bash codex/install-skills.sh <目标 home>` 后 `bash codex/check-drift.sh <目标 home>` 无漂移。普通项目开发跳过本节。

## 第 3 步：新项目登记（维护者）

新项目要先进平台的两份 manifest：`codex/config/gitea-governance.json`（仓库、可见性、project agent、required CI）与
`codex/config/host-access-broker.json`（项目 id、仓库、Mac 检出）。这一步按 [onboarding-runbook.md](onboarding-runbook.md)
§1 与 §5 在平台仓走自己的 Issue 与 PR，由人合并后两台重装 broker。

完成判据由维护者给出：runbook §1.1 的接入证据齐全，并且维护者用 broker 的 `host.onboarding.check`（manager-audit 身份）对该项目读回通过。
维护者告知完成后，开发者在项目检出里重跑第 1 步第 2 项，`git.fetch.main` 返回 `PASS` 只作为本机连通的核对。

## 第 4 步：把使用发布包采用进项目

### 采用（维护层）

1. 维护者在项目里为这次采用开一个 Issue，建该 Issue 的 change worktree。
2. 维护者在平台检出里运行 `bash codex/tools/usage-bundle.sh --adopt <项目 change worktree> --tools <所选工具>`，
   `--tools` 取 `claude`、`codex`、`cursor` 的逗号组合（缺省 `claude,codex`）。工作树必须干净。
3. 项目照常判级、确认、走唯一 PR，由人合并。

### 开发者读回

1. 在合并后的项目检出里读回：
   - `.aisoft/bin/aisoft version`：打印 `bundle_version`。
   - `.aisoft/bin/aisoft bundle status`：本仓与 pin 版本一致。
   - `.aisoft/bin/aisoft project-check`：没有 `GAP:` 行。有 GAP 就按行在项目里建 Issue 修复，不要手改 `.aisoft/` 下的文件。
2. 用 Cursor 时，在平台检出里加 `--repo <项目检出>` 重跑上面的版本读回，`SUPERPOWERS cursor` 与 `MATT cursor` 两行都应为 `PIN_CLEAN`；
   不是就停下报告。用 Codex 时，项目级 `.agents/skills/` 里的 Matt 快照目前没有工具核对，如实告诉用户这一项未核对，不要声称已核对。
3. 项目 `AGENTS.md` 的「项目事实」由项目自己填写（技术栈、测试命令、健康端点、交付形态等，见 `.aisoft/platform-usage.md` §4）。

## 第 5 步：跑通第一张 Issue（开发者）

先读项目内 `.aisoft/platform-usage.md` §2，再带用户走一遍。

1. **开 Issue**：把需求写成可测的验收标准，经 broker `gitea.issue.create`（带 `--entry-label triage/needs-triage`）创建。
2. **判级与路由**：运行 `$triage #N`，输出判级并查路由表（[route-policy.md](route-policy.md)）得到路由卡；
   模型按路由卡的 `tier` 选，各工具的型号映射见平台 `08` §7.3。
3. **建工作区**：`.aisoft/bin/aisoft change-name N <短描述>` 得到分支名，建 change worktree，
   再 `.aisoft/bin/aisoft claim-worktree --branch <分支>` 绑定本会话。
4. **确认点 1**：把合同与路由行给用户看，用户回「确认」后才开始实现。它只授权实现，不授权 PR、合并或部署。
5. **实现与验证**：在合同内实现、测试、修复；`.aisoft/bin/aisoft classify --apply N` 后用 `--verify N` 读回 `projected`。
6. **确认点 2**：本地验证完成后给出唯一最终 PR 的候选，用户回「开」后才用 `.aisoft/bin/aisoft open-pr N --title <标题> --body-file <正文>` 建 PR。
7. **人合并**：PR 只由人合并；合并不等于部署。合并后按 `issue-session-flow` 收尾（`aisoft complete` 先 dry-run 再 `--apply`）。

用户读到这里时，告诉他们后面的每张 Issue 都是第 5 步的重复。

## 常见卡点

| 现象 | 含义 | 处理 |
|---|---|---|
| broker 返回 `requested operation is not allowlisted` | 本机 broker 操作表比平台旧 | 请维护者重装 broker 后重试 |
| broker 返回其它 `REQUEST_DENIED` | 合同拒绝（项目未登记、参数或标签不合法等） | 原样报告 `code` 与 `message`，不要重试或换路径 |
| broker 偶发 `TRANSPORT_ERROR` | 传输异常，服务端是否已执行不确定 | 只读操作可重试一次；写操作（如建 Issue）先读回结果，确认没有生效再重试 |
| `requested project is not explicitly managed` | 项目没登记 | 回第 3 步 |
| Gitea 匿名 `404` | 私有仓库，不说明不存在 | 经 broker 读取 |
| `PIN_DRIFT` | 外部技能包版本不是平台 pin | 维护者先过 `08` §5 适配清单 |
| Codex superpowers `PIN_NOT_INSTALLED` | 官方市场没有 pin 版本，已登记 | 不阻塞，照常开发 |
| `project-check` 有 `GAP:` | 项目与 pin 版本不一致或项目声明缺项 | 按行在项目里建 Issue 修复 |

# 新项目接入 AISoft 平台 · v3 Runbook

> 本 runbook 面向任意 Gitea 项目。rsdesign-new 只是历史试点证据，不是默认仓库、目录、端口或部署合同。按顺序完成，每步验收后再继续；目标项目未通过自己的验收前保持 implementation disabled。

## 1. 参数与仓库

先确定唯一 profile 名称，再确定 `GITEA_URL`、`OWNER`、`REPO`、本地只读/工作克隆、技术栈、测试命令与 verifier 配置。只有应用项目才需要应用端口、Nginx 端口、健康端点、数据存储和回滚方式；纯文档或平台规范仓库不需要虚构部署流程。

把仓库放到 Gitea，验证历史完整、默认分支正确、Mac/内网客户端可以 clone 和 push feature
branch。随后先把 exact repository、classification、visibility、project agent 和 required status
contexts 纳入 `codex/config/gitea-governance.json` 并经平台 PR 人工合并；未知仓库不能继续接入。

### 1.1 Mandatory governance manifest 与 project-agent gate

Issue #35 发布后，按顺序执行：

1. `gitea-governance.sh --manifest ... validate` 验证 strict contract；public 必须在 exact allowlist，
   其它仓库默认 private。
2. 以 `bootstrap-gitea-service-account.sh` 一次创建一个 manifest-declared bot/PAT。manager audit、
   manager mutation 和每项目 token 使用独立 mode 600 file；账号/PAT 不复制到其它项目。
3. 仅以人工 site admin credential 对一个 exact repository 运行 `bootstrap-manager`，把非 site-admin
   `aisoft-platform-manager` 校准为 repository Admin；pre/post snapshot 均须保存。
4. 使用 manager audit token 运行 `gitea-governance.sh check`，显示 current/expected/planned action、
   cross-project Write violations 和 protection blockers。默认只读。
5. 使用 manager mutation token 对一个 exact repository 运行 `apply`；命令必须携带 Issue #35、
   已合并 platform SHA、platform root 和独立 evidence directory。工具校准 visibility、project-agent
   Write、merge 后删分支和 `main` protection，同时保留 exact status/approval contract。
6. 项目 profile 改用自己的 token，真实验证 private repo read、Issue/comment/label、feature push、
   PR、main push denied、main merge denied。只有 exact JSON evidence 全 PASS 后才允许
   `retire-shared-bot`。

所有 `main` 均禁止 direct/force push；merge allowlist 只能是人工 `admin`。platform manager、
project agent 与 legacy `ci-bot` 不得进入 push/force-push/merge allowlist。任一 credential、API、
permission、visibility、protection、cross-project 或 read-back 失败均终止为 `BLOCKED_EXTERNAL`。

Issue #61/#70 发布后，已在 host-access manifest 中的项目从 fixed broker 访问 host；Mac checkout 只用
repo-local protected-file helper，VM profile 只用 `GITEA_IDENTITY` + fixed mode 600 token file。Issue #73
candidate 允许项目在 manifest 中声明 strict `git_remote_name`；未声明兼容 `origin`，NewEmaint 固定
`gitea`。调用方不能传 remote name/URL/owner/repository/refspec，broker 也不创建或改写 remote。
新项目仍必须先通过独立 AISoftPlatform Issue/PR 同时更新 governance 与 host-access manifests，再执行
本节的账号/权限流程。
`orbstack-access-diagnostics` 不得作为接入前置，只在 broker failure 且真实状态仍矛盾时 emergency 使用。

平台 manifest PR 人工合并并安装后，逐项目按以下顺序接入：

1. `host.access.audit` 只读核对 protected-file metadata、token identity/scope、repository permission 与
   protected `main`/required CI。
2. credential 缺失时停止；credential provision/create/rotation 必须获得独立明确审批，Issue `approved`
   不构成 Secret mutation approval。
3. `mac.git.bind` 只在 canonical checkout 写 repo-local exact Gitea URL scoped helper/username 和
   `credential.useHttpPath=true`；不写 token/path，不修改 remote。
4. `host.onboarding.check` 只读聚合 access audit、canonical checkout、manifest remote fetch/push URL 和
   exact helper binding；任一缺失或 drift 均 fail closed。
5. 最后运行本项目 fresh-session typed Issue/change/PR/required-CI canary。一个项目的 PASS 不授权另一个
   项目；每个项目使用独立 adoption Issue 与 evidence。

平台 #73 PR 人工合并前不得创建 NewEmaint adoption Issue；合并后才单独完成 NewEmaint binding/live
canary。其它项目不得批量启用。

标准入口（只替换尖括号；token file 只写路径，不打印内容）：

```bash
PLATFORM_ROOT=/mnt/mac/Users/benque/MyDocs/AISoftPlatform
MANIFEST="$PLATFORM_ROOT/codex/config/gitea-governance.json"

"$PLATFORM_ROOT/codex/tools/gitea-governance.sh" \
  --manifest "$MANIFEST" validate

"$PLATFORM_ROOT/codex/tools/gitea-governance.sh" \
  --manifest "$MANIFEST" check \
  --token-file <manager-audit-token-file> \
  --repository admin/<repo>

"$PLATFORM_ROOT/codex/tools/gitea-governance.sh" \
  --manifest "$MANIFEST" apply \
  --token-file <manager-mutation-token-file> \
  --repository admin/<repo> \
  --issue 35 \
  --merged-sha <full-origin-main-sha-containing-issue-35> \
  --platform-root "$PLATFORM_ROOT" \
  --evidence-dir <new-mode-700-evidence-directory>
```

`bootstrap-manager` 使用人工 site-admin credential，但除此以外参数与 apply 相同；它只给一个
exact repository 添加 manager Admin 并写 pre/post snapshot，不修改 visibility、agent 或 protection。

### 1.2 Legacy `ci-bot` collaborator gate（迁移期）

Issue #35 live reconciliation 前，已有 profile 可以继续运行下列 fixed gate 保持服务；不得用它接入
新项目：

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

已有仓库的回补先使用同一工具的 `--check`。只从明确 AISoftPlatform project profiles/接入记录
生成 `repository/current_permission/main_protection/planned_action` 清单并等待人工确认；不得枚举
全部 Gitea 仓库后批量授权。新 project agent 验收前保留 `ci-bot`，验收后逐仓库退出。

## 2. 共享项目契约

在仓库加入：

- 从平台 `templates/project/AGENTS.md` 复制并按项目填充的 `AGENTS.md`（前两节为平台常驻
  指针，除更新事实外不删改；「项目事实」节写真实命令、健康端点、交付形态与禁改边界——
  交付形态由本项目 delivery profile 决定，平台只统一流程不变量，不强制统一部署方案）。
- 从 `templates/project/CLAUDE.md` 复制的一行 `@AGENTS.md`。
- 已接入的存量仓库回补同一指针：逐仓独立 Issue + 小 PR（经该仓 project-agent 通道），把
  AGENTS.md 对齐模板前两节；不得批量脚本改写全部仓库。
- 从平台仓库 `templates/docs/changes/_template/` 复制 `summary.md`、`spec.md`、`plan.md`、`verification.md` 四个语义模板。新 change 文档实名使用 `<role>-<short-description>-<YYMMDD>.md`，并在 summary front matter 的 `documents` 字段把 `summary`/`spec`/`plan`/`verification` 显式映射到真实 basename；remote/history evidence 已存在的 `change/N`、`docs/changes/N/` 与 pre-#57 纯数字文档只作读取或维护兼容，新 writer、first push 和 first PR 不得创建。
- Matt 编排初始化：显式调用 `$setup-matt-pocock-skills`，tracker 选 `Other`，使用平台 `templates/docs/agents/issue-tracker.md`、`triage-labels.md`、`domain.md` 三件套（经 `$aisoft-matt-workflow` 校验平台边界后执行），不得另建第二套 Gitea 模板。
- lockfile、包管理源和固定运行时版本。
- 能检查关键依赖的健康端点。

所有 change 文档的共同 front matter 至少包含 `issue`、`gitea_url`、`change_type`、`requested_complexity`、`assessed_complexity`、`effective_complexity`、`contract_effect`、`confidence`、`risk_flags`、`status`、`branch`、`pr_url`、`created` 和 `updated`。映射的 `summary` 文档另外保存 analyzer 的 `reason`、`required_docs` 和 `override_reason`；`needs-human-decision` summary 必须在 front matter 和 `## AI 判级` YAML 中都省略 `effective_complexity`，且不得创建 complex spec/plan。

## 3. Mandatory host-role gate

Agent project profile（Gitea 坐标/provider/state）和 host profile（machine identity/capability）
是两个独立合同，不能互相代替。任何承载 SCM、CI 或应用 runtime 的 Linux 主机都必须在
自己的 complex Change 中选择且只选择一个 role：

- `scm-ci`：source checkout、build、bounded test、package、registry/artifact publish、
  批准的缓存/通知/Runner 和 artifact retention dry-run；
- `appserver-test`：消费已批准制品，执行非生产 deploy/migration/start/health/rollback；
- `appserver-prod`：只消费测试证明匹配的制品并运行确定性生产脚本。

平台 PR 合并并发布稳定版本后，运行 `codex/install-host-role.sh` 两次验证幂等；installer
只能复制 schema、catalog、guard 和示例，不得创建 live profile、credential、service、timer
或部署。目标主机从 `templates/hosts/host-profile.example.json` 生成
`/etc/aisoft/host-profile.json`，填入真实 hostname 与 `/etc/machine-id`，capability 集必须与
catalog 中 role 完全相同；文件 root-owned、mode `400/440/600/640`，父目录不得 group/other
writable。

所有 root-owned deploy/start/database wrapper 在 mutation 前调用固定入口：

```bash
/usr/local/libexec/aisoft/verify-host-role --action <fixed-action> --resource <fixed-resource>
```

调用接口不允许覆盖 profile/hostname/machine-id，不接受任意 shell。`0` 才可继续；`20`
表示 role deny，`30` 表示 profile/request 无效，`40` 表示 identity mismatch，`64` 表示调用
错误，任何非零都必须零 mutation。测试 fixture 只能通过 source 后替换 OS probe，不能形成
已安装 CLI 的测试模式或环境变量后门。

在 `scm-ci` 故意请求 `start/application`，必须连续两次返回 20，并证明 PID、listener、DB
和文件无变化。应用项目必须把部署目标指向独立 `appserver-test`；不能因为旧 pilot 曾在
`gitea-ci` 运行 PM2 就复制 legacy workflow。host profile 安装通过也不代表应用已迁移，
迁移/数据/回滚仍在应用自己的 Issue、branch、PR 和 live Gate 中验收。

## 4. CI 与部署

新 Linux 软件仓库默认消费平台
[`docker-release/v2`](../../docker-release/README.md)，而不是复制 `rsdesign-new` 的 PM2
脚本。接入顺序：

1. 项目独立 Issue/spec/plan/PR 实现 Dockerfile、Compose、migration service、业务 health、
   Gitea Registry publish 和 offline bundle；平台 candidate 不能替代应用验收。
2. 从 `docker-release/templates/target-profile.example.json` 生成 test/prod target profile，
   按环境填写 hostname、`appserver-test`/`appserver-prod` role、transport、路径、Compose
   project 和 #23 architecture identity，设为 mode `0400/0600`。模板和仓库都不填 Secret。
3. Secret 只在目标机受保护 env file；release manifest、architecture lock、Compose、state、
   argv、日志和 verification 不保存 Secret 值。
4. Builder 生成以完整 Gitea merge SHA 为 ID 的 `release.json`、digest-pinned images、Compose/
   architecture checksums、producer-normalized Compose model 和 offline inventory。V2 对每个 service 同时记录 Registry digest
   `reference`、content `image_id`、deterministic `transport_reference`/`runtime_reference`；后两者
   必须等于 `aisoft.local/<lower-owner>/<lower-repo>/<service>:<full-sha>`。Builder 先按 digest
   inspect，再 tag、重复 inspect exact ID/`linux/amd64`，最后按 tag save。目标 AppServer 不
   build/install/git pull/访问公网。
5. 先运行 artifact-only `verify-artifact`，再用逐 action root-owned grant 分别执行 read-only
   `verify-target`、`stage`、`migrate`、`activate`、`status` 和 `rollback`。Stage 不读取 database
   Secret、不运行 migration/up；migrate 不 stage/up；activate 不 stage/migrate。故意覆盖 bundle
   tamper、host-role mismatch、missing receipt、migration failure 和 health failure rollback；再由
   独立生产 Gate 提升同一 identity。Legacy `deploy` 只为既有 v1 调用方保留。

NewEmaint 的示例 profile 仅说明平台字段，不授权修改 NewEmaint 仓库、创建真实 Secret、执行
migration 或部署。其首个消费实现仍须在 NewEmaint 自己的 exact
`change/N-short-description`、映射的 `docs/changes/N-short-description/` 语义文档和唯一最终 PR
中完成。

Offline consumer 只接受 `docker-release-offline-bundle/v2` +
`docker-release-offline-inventory/v2`，在 load 前验证 archive/inventory/Compose/architecture
checksums、tar member 与逐 service tag allowlist；load 后按 runtime tag 验证 exact image ID 与
`linux/amd64`，不依赖 `RepoDigests`。既有 legacy manifest 只保留 Registry digest path；legacy
offline bundle 必须从受控 producer 重新发布，禁止手改 archive/inventory 冒充 V2。

接入 Docker target 前还要读取平台 versioned image-store matrix。Runtime 只接受由同 fixture
真实 E2E 支持的唯一 row；Engine 29 不能自动等同 containerd，必须用 `DriverStatus` marker
只读检测。Issue #27 已在两个独立 disposable Engine 29 containerd daemon 上完成 Registry 与
offline transport、Compose runtime/identity/health 和 exact cleanup E2E，containerd row 由已提交的
`issue-27-containerd-a75181cd7209` evidence 固定为 `supported`。Classic 没有同等级真实证据，继续
`rejected`；不得把 fake tests、源码结论或应用 synthetic verifier 写成 classic 环境 PASS。
Compose 5.1.4 同样需要同等级 disposable Engine 29/containerd consumer E2E 与 committed evidence；
在此之前不得扩展 supported matrix。

已有 PM2 应用在独立迁移验收前继续作为 legacy adapter。维护这些应用时保留：

- 构建产物完整性检查。
- 不可变制品和环境配置分离。
- 数据备份和向后兼容迁移。
- SQLite 的停应用后迁移。
- PM2 delete+start 与 online 断言。
- HTTP health check 和失败回滚。
- `scm-ci` 只构建/测试/发布制品，AppServer 才执行 application/database mutation。
- `/opt/artifacts` retention 先验证项目 allowlist、完整 SHA/checksum、引用、数量和期限，只
  输出 dry-run/audit ledger；删除另行授权。

AI 可以参与开发/测试环境首次部署。把所有成功手工步骤固化为脚本，连续运行两次，并故意制造一次失败验证回滚。把真实结果写入关联 Issue 映射的 `verification` 文档。生产只执行验收后的脚本。平台 local fake PASS、安装候选或 PR CI 不能写成真实 AppServer/production deployed。

## 5. Gitea 治理

- 先通过 §1.1 manifest/project-agent gate；platform manager 为 exact-repo Admin，项目 agent 为
  exact-repo Write，二者均不给 merge。§1.2 `ci-bot` 只服务尚未迁移的已有 profile。
- 保护 `main`，禁止直接 push，要求准确的 `CI / test (pull_request)` context。
- 建七个类型标签：`type/bugfix`、`type/feature`、`type/docs`、`type/test`、`type/refactor`、`type/maintenance`、`type/platform`。它们是 Issue 作者可提供、AI 按证据校验的变更类型输入。
- 建两个互斥的复杂度标签：`complexity/small`、`complexity/complex`。它们是 AI 判级后的输出；无法安全判级时两者都不添加。
- 建八个标签：`needs-analysis`、`awaiting-triage`、`spec-drafting`、`spec-review`、`approved`、`pr-open`、`completed`、`deployed`。
- 建七个 Matt triage 标签：`triage/bug`、`triage/enhancement`（category）与 `triage/needs-triage`、`triage/needs-info`、`triage/ready-for-agent`、`triage/ready-for-human`、`triage/wontfix`（state）；canonical manifest 共 24 个。`triage/ready-for-agent` 不等于平台 `approved`。
- 新 Change 使用单一 `change/N-short-description` 分支和最终 PR `Closes #N`（编号仍是唯一主键，slug 只用于人类识别）；已存在于 remote/history 的 `change/N` 仅作证据驱动的维护兼容。

四个维度正交：`type/*` 是变更类型输入，`complexity/*` 是 AI 有效复杂度输出，八个无前缀标签是生命周期状态，`triage/*` 是 Matt 编排状态。`needs-analysis` 触发 analyzer；`approved` 启动 Loop；`spec-review` 只是可选协作状态；`pr-open` 等最终 CI/review；`completed` 表示最终 PR 已合并且明确无需部署；`deployed` 表示确定性部署和验证完成。两个交付终态互斥。

## 6. Analyzer 接入

- 从 `templates/agent/project.env.example` 复制到 VM 的 `~/.config/aisoft/projects/<profile>.env`，填入该项目自己的 Gitea 坐标、token 和 `AGENT_REPO_DIR`，设为 mode 600；不得提交该文件。
- 每个 profile 使用 `~/.local/state/aisoft-loop/projects/<profile>/` 保存锁、Issue state 和 worktrees，不与其他仓库共享。
- 为项目准备只读工作克隆和依赖/索引。
- 安装 `$aisoft-platform` 与 `$gitea-analyze-change`。
- 先用低风险 Issue 验证：读取 evidence、输出五节 summary，并以 `change_type`、`requested_complexity`、`assessed_complexity`、`effective_complexity`、`contract_effect`、`risk_flags`、`required_docs`、`confidence` 和 `override_reason` 确定性判级。
- 用功能新增验证 `type/feature` 和 `effective_complexity: complex`；用信息不足的 Issue 验证 `needs-human-decision`、`contract_effect: unclear` 且不输出 `effective_complexity`。
- Analyzer 不修改产品代码、Git 或 Gitea 标签/评论，不创建最终 PR、不部署；wrapper/controller 负责映射的 `summary` 文档、readable 分支、评论和标签状态变更。
- 普通实现 worker 永远不得编辑约束本次运行的 `AGENTS.md`。complex spec 只能授权其生成治理 patch/proposal；目标文件之外的独立受控治理步骤负责应用，随后用 fresh run 验证并采用新规则。其他 protected files 仍要求 complex spec 精确列出文件、验证与回滚。

## 7. Development Loop 接入

只在平台 `08` 的 Codex skills 和 controller 验证完成后启用：

- 使用 provider-neutral controller；不要为 Codex/Claude 复制两套 Loop。
- 每个 active Issue 使用隔离 worktree 和锁。
- 第一阶段只运行一个 active Issue。
- 外层 verifier 独立运行项目命令，不信任模型自述。
- 同一根因三次失败、合同冲突、范围扩张或高风险决策时升级给人。
- 最终状态只允许 `READY_FOR_REVIEW`、`NEEDS_HUMAN_DECISION`、`BLOCKED_EXTERNAL`、`FAILED_LIMIT`。
- 只有人可以合并最终 PR。
- 使用 `aisoft-agent@<profile>.service/.timer` 作为项目级 systemd 实例；安装模板不等于启用。必须显式执行 `systemctl --user enable --now aisoft-agent@<profile>.timer`，且只有该项目验收通过后才允许这样做。

## 8. 接入验收

按顺序验证：

1. Trivial PR 的 CI context 正确且受分支保护约束。
2. governance check 证明 visibility 与 public allowlist/private default 一致，project agent 没有
   cross-project Write/Admin，manager/project agent/legacy bot 均不能 merge `main`。
3. `scm-ci` 的 application start 负向 guard 证明零 mutation。
4. 合并后由独立 `appserver-test` 确定性部署和精确 SHA health 通过。
5. Analyzer 对真实 Issue 输出确定性分类，wrapper/controller 写入正确且互斥的标签。
6. Small Issue 从明确合同进入 Loop 并准备绿色 PR。
7. Complex Issue 缺 spec/plan 时拒绝，补齐后按 plan 执行。
8. 普通测试失败由 Loop 自修复。
9. 合同冲突、外部阻塞和三次同因失败正确升级。
10. CI failure feedback 能进入下一轮。
11. 非生产首次部署执行两次并完成故意失败回滚。
12. 生产负向测试证明 provider 无生产部署权限。

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
5. 以上证据写入该项目映射的 `verification` 文档后，才可单独批准 enable timer。

## 9. 安全回滚

在 Loop 试点前记录当前 timer、provider、agent 脚本、工作树、开放 Issue/PR 和标签状态。保持 `IMPLEMENT_PROVIDER=none`，直到专项实施明确启用新 controller。

试点失败时停止 controller，保留 analyzer，开发回到 Mac 人机交互；CI、制品和生产部署不受影响。未经单独批准，不删除旧脚本、认证或 provider 配置。

## 9. Architecture declaration onboarding

在 collaborator/branch-protection gate 通过后、任何 dependency upgrade 或部署前：

1. 从平台 `architecture/templates/project-architecture.example.json` 复制为项目
   `.aisoft/architecture.json`；只使用 strict JSON，V1 不接受 YAML。
2. 选择一个 versioned profile，按仓库 lock、Dockerfile/schema 和脱敏 runtime metadata
   声明精确 component。每个 slot 只能选择 preferred 或一个同 category、显式 allowlisted 的
   `supported`/`sunset` transition；禁止目录名推测、Secret、`latest`、semver range、
   mutable-only OCI 和 `prohibited`/EOL component。
3. 用 `aisoft-architecture lock` 生成并提交 `architecture.lock.json`，连续两次输出必须
   byte-identical；随后用 `validate --lock` 检查 drift。
4. 每个 transition 必须引用应用仓中真实可读的绝对 HTTPS migration Issue，并有唯一匹配的
   owner/reason/risk/controls exception；多个 component 可以引用一个逐项列明范围的 umbrella
   Issue，但不能共享 exception。expiry 不得超过创建日起 180 天或 component `migrate_by`，
   到期当日 fail closed。Preferred 不需要 exception；`prohibited`/EOL 不可绕过。
5. Docker target profile 可声明 `architecture_project_id`；一旦声明，release lock project、
   profile、catalog、checksum/self-hash 和 transition expiry 必须全部匹配，且在 Docker 调用前
   验证。已有未声明该字段的 v1 target profile 保持兼容。
6. Current lock 表达实际 release bytes，target candidate 只表达目标。Candidate lock 不等于
   项目已迁移或已部署，也不能复制成 current。多个相互依赖的 runtime/framework/ORM/database/
   container major 可以由应用仓一个 complex umbrella Change 统一治理，但必须逐 component
   保留 compatibility/test/rollback Gate，不能报告部分完成；#22 只接收治理 identity/checksum，
   不授权 migration。

平台 installer 只复制 versioned validator/catalog/schema/template，不创建项目 declaration、
凭据、service 或 timer。离线环境先验证官方 checksum/signature、SBOM/provenance 和 OCI digest，
再导入批准 mirror；production lock 不由自动 updater 修改。

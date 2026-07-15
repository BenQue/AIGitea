# 新项目接入 AISoft 平台 · v3 Runbook

> 以 rsdesign-new 为模板。按顺序完成，每步验收后再继续。Loop 尚未通过 Codex 验证时，保持 implementation disabled，使用 Mac 人机交互开发。

## 1. 参数与仓库

确定 `REPO`、应用端口、Nginx 端口、技术栈、测试命令、构建命令、健康端点、数据存储和回滚方式。端口与基础设施见平台文档 `01`。

把仓库放到 Gitea，验证历史完整、默认分支正确、Mac/内网客户端可以 clone 和 push feature branch。

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

- 给 ci-bot 最小 feature-branch、Issue 和 PR 权限，不给合并权。
- 保护 `main`，禁止直接 push，要求准确的 `CI / test (pull_request)` context。
- 建七个类型标签：`type/bugfix`、`type/feature`、`type/docs`、`type/test`、`type/refactor`、`type/maintenance`、`type/platform`。它们是 Issue 作者可提供、AI 按证据校验的变更类型输入。
- 建两个互斥的复杂度标签：`complexity/small`、`complexity/complex`。它们是 AI 判级后的输出；无法安全判级时两者都不添加。
- 建七个标签：`needs-analysis`、`awaiting-triage`、`spec-drafting`、`spec-review`、`approved`、`pr-open`、`deployed`。
- 使用单一 `change/N` 分支和最终 PR `Closes #N`。

三个维度正交：`type/*` 是变更类型输入，`complexity/*` 是 AI 有效复杂度输出，七个无前缀标签是生命周期状态。`needs-analysis` 触发 analyzer；`approved` 启动 Loop；`spec-review` 只是可选协作状态；`pr-open` 等最终 CI/review；`deployed` 表示部署验证完成。

## 5. Analyzer 接入

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

Codex 全部通过后，再用相同矩阵接入和验证 Claude adapter。

## 8. 安全回滚

在 Loop 试点前记录当前 timer、provider、agent 脚本、工作树、开放 Issue/PR 和标签状态。保持 `IMPLEMENT_PROVIDER=none`，直到专项实施明确启用新 controller。

试点失败时停止 controller，保留 analyzer，开发回到 Mac 人机交互；CI、制品和生产部署不受影响。未经单独批准，不删除旧脚本、认证或 provider 配置。

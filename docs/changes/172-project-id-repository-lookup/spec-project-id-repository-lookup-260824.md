---
issue: 172
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/172
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - platform-governance
depends_on: []
status: approved
branch: change/172-project-id-repository-lookup
created: 2026-08-24
updated: 2026-08-24
---

# Spec：`--project` 只有一个命名空间，repository 由它反查

## 1. 目标与原因

让 `mark-completed-issues.sh` 在 `project_id != repository name` 的项目上可用——今天它在那 6 个
项目上连 dry-run 都跑不到 Issue 循环。

根因不是 #163 引入的：`--project` 从 #115 起就同时被喂给 broker（project id 命名空间）和
governance manifest 查表（repository name 命名空间）。默认值 `aisoft-platform` 两名同名，
给了它长期伪装；#163 的 `deployment_lifecycle` 查表只是把这个既有缺陷变成了 hard failure。

本 spec 把 `--project` 的取值语义钉成**唯一一个**——host-access manifest 的 project id——
并让 repository 由它反查得到，而不是由调用方在同一个参数里兼职提供。

## 2. Acceptance criteria

映射关系：Issue 正文 AC-1 → 本文 AC-1；AC-2 → AC-2；AC-3 → AC-3；AC-4 → AC-4；AC-5 → AC-5/AC-6。

- [ ] **AC-1 mismatch 项目可用**：对 `project_id != repository name` 的项目，
      dry-run 与 `--apply` 都不再因 governance manifest 查表非零退出。
      判定基线用 `localwms`（真实 manifest 对里 `localwms → LocalWMS`）。
- [ ] **AC-2 读到的是该 repository 的真实取值**：反查到 repository 之后，
      `deployment_lifecycle` 取自**那条 manifest 记录**，而不是空串、报错或写死的缺省。
      可观测判据：project id 指向一个 governance 里声明 `none` 的 repository 时，
      含 `verification` 的 Issue 判为 `set-completed` / `no-deployment-chain`；
      指向一个声明 `application-deploy` 或未声明的 repository 时，判为
      `skip` / `requires-deployment`。两种结论只由 repository 侧的声明决定，
      与 project id 的字面值无关。
- [ ] **AC-3 两侧都 fail-closed 且指名哪一侧**：project id 不在 access manifest 里 → 非零退出，
      消息指明 access manifest 与该 project id；repository 不在 governance manifest 里
      （或那里不是恰好一条）→ 非零退出，消息指明 governance manifest 与该 **repository**。
      两种情况在 dry-run 与 `--apply` 下都如此，且都不调用 broker。
      access manifest 文件不存在或不是合法 JSON 同样非零退出。
- [ ] **AC-4 coinciding 项目行为逐字不变**：`aisoft-platform`（两名同名）的
      `deployment_lifecycle: none` 仍被读到，含 `verification` 的 Issue 仍判为
      `set-completed` / `no-deployment-chain`，不含的仍判为 `set-completed` 且不带 `reason`；
      无映射文档仍 `skip` / `documents-unresolved`；`--range` 解析、无选择器报错、
      dry-run 零 broker 调用、判断不泄漏到 broker 参数面——全部不变。
- [ ] **AC-5 覆盖落在测试里**：`codex/tests/test-mark-completed-issues.sh` 覆盖 AC-1..AC-4，
      其中 mismatch 形状是 fixture 的**默认**形状（#163 留下的断言全部从修好的路径上跑过），
      并有一条用例使用仓库里两份**真实** manifest 断言 `localwms` 解析成 `LocalWMS`。
- [ ] **AC-6 `bash codex/tests/smoke.sh` 全绿**，`bash -n` 通过；环境可用时 ShellCheck 通过。

## 3. 裁决：反查，而不是新增 `--repository`

Issue 正文要求在两个方向里择一。**采用方向 1（反查）**，依据是一条已经存在的契约事实。

`codex/runtime/aisoft_host_access/contract.py:401-405` 在加载 access manifest 时已经强制：

```
_require(project_id not in project_ids,  f"duplicate project_id: {project_id}")
_require(repository not in repositories, f"duplicate repository mapping: {repository}")
_require(repository in governance_by_name, f"repository is absent from governance: {repository}")
```

三条合起来的意思是：`project_id → repository` 是一个**双射**，而且值域已经被保证落在
governance manifest 的 repository 集合里。于是——

- 方向 2 想新增的「两份 manifest 之间的一致性校验」**已经存在**，而且在加载期就跑，
  比任何工具级的事后核对都早。再加一个 `--repository` 参数只会得到那个保证的一份更弱的副本。
- 方向 2 还会新开一个调用方能填错的口子：调用方要同时说对两个名字。本 Issue 的成因恰恰就是
  「一个参数要同时说对两个命名空间」，方向 2 把它变成「两个参数各说对一个」，量级变小，
  性质不变。
- 方向 1 让调用方只需说对一件事，剩下的从已经被校验过的声明里读。

**不新增任何命令行参数**，`--project` 的默认值仍是 `aisoft-platform`。

## 4. 接口、数据与兼容性影响

### 4.1 `mark-completed-issues.sh`

新增 access manifest 解析，与已有的 governance 解析逐条同构：

```
AISOFT_ACCESS_MANIFEST                              （覆盖，本次新增的名字）
→ <tool_dir>/../config/host-access-broker.json      （仓库布局）
→ /usr/local/share/aisoft/host-access-broker.json   （扁平安装）
```

解析后一次 `jq` 反查，与 governance 那次同一种 fail-closed 写法（`[...] as $entries`，
`length == 1` 才取值，否则 `error(...)`）：

```
repository = access.projects[] | select(.project_id == $project) | .repository
```

随后 governance 查表把 `--arg name "$project"` 换成 `--arg name "$repository"`。
报错文案分成两条，各自指名 manifest 与查的键。

`--project` 继续原样传给 broker（`mark-completed-issues.sh:222`）——那一侧本来就对。

### 4.2 不变的面

- 命令行参数集合、默认值、输出 JSON 的字段与取值（`action`/`reason`/`detail`/`applied`/`result`）。
- dry-run 不调用 broker；`--apply` 才写；`--range` 解析规则。
- `required_docs` × `deployment_lifecycle` 的合取判定表（`03` §11），一格都不动。
- broker typed 操作与参数面；两份 canonical manifest 的**内容**。
- `AISOFT_GOVERNANCE_MANIFEST` 的名字与语义。

### 4.3 兼容性

- coinciding 的 4 个项目（`aisoft-platform`/`myapp`/`rsdesign-new`/`smoke-test`）：
  反查得到与输入同名的 repository，后续路径逐字不变。
- mismatch 的 6 个项目：从「总是非零退出」变成可用。没有任何调用形态从「能用」变成「不能用」，
  除非它跑在一个读不到 access manifest 的环境里——那种环境同样读不到 broker，
  `--apply` 本来就不可能成功。
- 新增的运行前提是 access manifest 可读。这是本变更把 `contract_effect` 记为 `change`
  而不是 `restore` 的原因。

## 5. 治理文件修改授权

本 spec 显式授权修改：

- `codex/tools/mark-completed-issues.sh` —— 仅限 manifest 解析与 repository 反查，
  不改判定表、参数集合与输出 schema。
- `codex/tests/test-mark-completed-issues.sh` —— fixture 形状与新增用例。
- `03-Issue-Spec-Plan与单闸门开发流程.md` §11 —— 仅限把「manifest 读不到或查不到该项目条目时
  报错退出」这句话更新为跨两份 manifest 的说法，并说明 `--project` 收的是 project id。
  判定表与终态语义不动。

**不授权**修改 `AGENTS.md`、controller、CI/部署脚本、broker 的操作表或参数校验、
`skill-for-claude/` 下任何 skill、两份 canonical manifest 的内容。

## 6. 非目标

- 不改 `apply-classification-labels.sh`、`aisoft-project-check.sh`、`mark-deployed-issues.sh`。
  三者已核查无同类混用，见 summary「风险」第三条。
- 不改任何项目的 `deployment_lifecycle` 声明。`LocalWMS` 仍不声明、仍取缺省
  `application-deploy`——本变更让工具**读对**它，不改它是什么。
- 不给 broker 新增「查询 project→repository 映射」的 typed 操作。工具在 dry-run 下不该需要
  broker，加一个查询操作会让 dry-run 反过来依赖它。
- 不补写任何真实 Issue 的生命周期标签。本变更只让工具可用；跑不跑、对谁跑，仍由人在收尾时决定。
- 不修 LocalWMS #66。它已由人工 broker 写入达到 `completed`（见 Issue 正文备注），无需回补。

## 7. 未决问题

- 无。

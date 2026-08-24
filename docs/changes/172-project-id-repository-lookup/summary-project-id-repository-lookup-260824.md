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
pr_url: ''
created: 2026-08-24
updated: 2026-08-24
reason: 修改治理工具解析 manifest 的方式并给它新增一个运行前提（access manifest 必须可读），属平台治理变更，强制 complex
required_docs:
  - summary
  - spec
  - plan
override_reason: ''
documents:
  summary: summary-project-id-repository-lookup-260824.md
  spec: spec-project-id-repository-lookup-260824.md
  plan: plan-project-id-repository-lookup-260824.md
---

## 问题/需求总结

`codex/tools/mark-completed-issues.sh` 的 `--project` 一个参数被当成两个不同命名空间使用：

- `mark-completed-issues.sh:100` —— `jq --arg name "$project" '.repositories[] | select(.name == $name)'`
  查的是 **governance manifest 的 repository name**（`LocalWMS`）。
- `mark-completed-issues.sh:222` —— 同一个 `$project` 传给 broker 当
  **host-access manifest 的 project id**（`localwms`）。

两者在 `aisoft-platform` 上恰好同名，所以这个混用从 #115 引入起一直没有代价。
#163 加进来的 `deployment_lifecycle` 查表把它变成了 hard failure。

现场复现（2026-08-24，当前 HEAD，同一台 Mac、同一个 checkout，只换 `--project`）：

```
$ bash codex/tools/mark-completed-issues.sh --repo "$PWD" --project localwms 163
ERROR: mark-completed: cannot read deployment_lifecycle for localwms from
  .../codex/config/gitea-governance.json: jq: error (at ...:180):
  not exactly one manifest repository named localwms
exit=1

$ bash codex/tools/mark-completed-issues.sh --repo "$PWD" --project aisoft-platform 163
{"issue":163,"action":"set-completed","applied":false}
exit=0
```

**这不是「`--apply` 才崩」。** Issue 正文订正了初始报告的这一点：manifest 读取在
`mark-completed-issues.sh:96-108`，位于 Issue 循环与 `--apply` 分支之前且无条件执行，
上面第一条命令没有 `--apply` 也退出 1。症状是**工具在这些项目上整体不可用**。

## 影响范围

受影响的是 `project_id != repository` 的项目。两份 canonical manifest 对照，10 个项目里 6 个：

| project_id | repository | 今天能用 |
|---|---|---|
| `hsdb` | `HSDB` | 否 |
| `localwms` | `LocalWMS` | 否 |
| `newemaint` | `NewEMaint` | 否 |
| `sap-table-migrate` | `SapTableMigrate` | 否 |
| `sfm-digital-board` | `SFMDigitalBoard` | 否 |
| `wmpda` | `WMPDA` | 否 |
| `aisoft-platform` / `myapp` / `rsdesign-new` / `smoke-test` | 同名 | 是 |

连带后果：#163 引入的 `deployment_lifecycle` 分支在那 6 个仓库上从未被执行过；
`issue-session-flow` 收尾第 2 步在它们上面一步都走不下去。

改动路径：

1. `codex/tools/mark-completed-issues.sh` —— 新增 access manifest 解析，
   按 `project_id` 反查 `repository`，用反查结果查 governance manifest。
   `--project` 的取值语义收敛成**唯一一个**：host-access manifest 的 project id。
2. `codex/tests/test-mark-completed-issues.sh` —— fixture 改成 `project_id != repository`
   的形状，让 #163 留下的每一条断言都从修好的路径上跑过；补两侧缺失的负向用例，
   并用真实 manifest 对钉住 `localwms → LocalWMS`。
3. `03-Issue-Spec-Plan与单闸门开发流程.md` §11 —— 「查不到该项目条目就报错」现在跨两份
   manifest，说明书要跟上（本变更授权修改，见 spec §5）。

**不改动**：`--project` 的默认值 `aisoft-platform`、输出 schema、dry-run/`--apply` 两段式、
`required_docs` 与 `deployment_lifecycle` 的合取判定表、broker typed 操作表与参数面、
`apply-classification-labels.sh`、`mark-deployed-issues.sh`、两份 canonical manifest 的内容、
`skill-for-claude/issue-session-flow/SKILL.md`（它写的已经是 `--project <id>`，修好之后逐字正确）、
`AGENTS.md`、CI 与部署脚本。

## 初步方案与建议

**采用「按 `project_id` 反查 `repository`」，不新增 `--repository` 参数。**
Issue 正文把两个方向都列了出来，裁决依据是一条已经存在的契约事实：

`codex/runtime/aisoft_host_access/contract.py:401-405` 已经强制

- `project_id` 唯一（`duplicate project_id`）
- `repository` 唯一（`duplicate repository mapping`）
- **`repository` 必须存在于 governance manifest**（`repository is absent from governance`）

也就是说 host-access manifest 已经是 `project_id → repository` 的双射，而且「governance
里查得到」这件事已经被校验过。方向 2 想加的「两份 manifest 之间做一致性校验」不是要新增的
东西——**它已经存在**；再加一个 `--repository` 参数，等于把一个强保证复制成一份更弱的副本，
同时给调用方新开一个能填错的口子。方向 1 只是去消费那个既有保证。

解析姿态照抄工具里已有的两条，不新增第三条规则：

| manifest | 覆盖 | 仓库布局 | 扁平安装 |
|---|---|---|---|
| governance | `AISOFT_GOVERNANCE_MANIFEST` | `codex/config/gitea-governance.json` | `/usr/local/share/aisoft/gitea-governance.json` |
| access（本次新增） | `AISOFT_ACCESS_MANIFEST` | `codex/config/host-access-broker.json` | `/usr/local/share/aisoft/host-access-broker.json` |

两份文件由 `codex/install-vm.sh:42-45` 与 `codex/install-host-access-broker.sh:144-147`
装进同一个 share 目录，仓库布局里也在同一个 `codex/config/`，所以不存在「一个在、另一个不在」
的安装形态。`AISOFT_ACCESS_MANIFEST` 是本变更新增的名字（`AISOFT_GOVERNANCE_MANIFEST`
是 `change_control.py` 已有的），存在的理由是可测性：没有它，用 env 覆盖 governance 的既有测试
会顺着扁平安装分支读到**本机真实的** `/usr/local/share/aisoft/host-access-broker.json`，
测试结果就依赖主机状态了。

**两侧都 fail-closed，且报错要说明是哪一侧缺。** 沿用工具头部已经写死的姿态
（「a prerequisite it cannot satisfy is an error」）：project id 不在 access manifest 里、
repository 不在 governance manifest 里，都非零退出，消息分别指名 access 侧与 governance 侧。
今天两种情况会挤成同一条 governance 报错，正是它把「站错命名空间」伪装成「manifest 缺条目」。

## 风险

- **扁平安装读到旧 access manifest**：VM 侧从 `/usr/local/share/aisoft/host-access-broker.json`
  读，重装前该文件是旧的。但本次不改 manifest 内容，只改谁读它；旧文件里的
  `project_id`/`repository` 映射与新文件一致，所以陈旧只在「新接入的项目还没进旧文件」时有影响，
  且表现为 fail-closed 报错而不是误判。收尾按 `issue-session-flow` 一律在平台 checkout 上跑、
  命中仓库布局优先。
- **既有测试断言被大改**：把 fixture 改成 `project_id != repository` 的形状，会动到 #163 留下的
  大部分断言行。缓解：断言的**语义**逐条不变，只是项目标识与仓库名分开；并额外保留一个
  两名同名的项目（`aisoft-platform`）继续覆盖 coinciding 路径，避免把回归覆盖换掉。
- **误以为顺手修好了别处**：`codex/tools/` 下已核查，没有第三处同样的混用
  （`apply-classification-labels.sh` 只喂 broker，单命名空间；`aisoft-project-check.sh:483`
  用 `$GITEA_REPO` 查 governance，命名空间正确；`mark-deployed-issues.sh` 不接受 `--project`）。
  本变更不去改它们。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 修改治理工具解析 manifest 的方式并给它新增一个运行前提（access manifest 必须可读），属平台治理变更，强制 complex
risk_flags:
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
confidence: high
override_reason: ''
```

### 判级证据

- `AGENTS.md`：「Agent 或平台治理变更一律按 complex 处理」——`mark-completed-issues.sh`
  是经 broker 写 Gitea 生命周期标签的治理工具，本变更改的是它读取治理事实的路径。
- `contract_effect: change`：工具新增一个运行前提（access manifest 必须可读、必须能查到该
  project id），这是对它运行契约的新增，不是单纯把坏掉的行为恢复原状。
- 触及共享核心：消费 `aisoft_host_access.contract` 已经校验的 `project_id → repository` 双射，
  与 `aisoft_gitea_governance.contract` 的仓库条目同时被读。
- 修改合同文档 `03` §11，须由本 spec 显式授权（`AGENTS.md` 治理文件条款）。

### 缺失的 acceptance criteria 或决策

- 无。Issue 正文 AC-1..AC-5 完整且可测；Issue 明确要求「修复方向择一、在 spec 里裁决」，
  裁决与依据见上文「初步方案与建议」与 spec §3。

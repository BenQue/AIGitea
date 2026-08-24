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

# Implementation plan：按 project id 反查 repository

## 任务

| ID | 内容 | 依赖 | 状态 |
|---|---|---|---|
| T01 | `mark-completed-issues.sh` 解析 access manifest，按 `project_id` 反查 `repository`，用它查 governance；两侧报错分别指名 | - | completed |
| T02 | `test-mark-completed-issues.sh` fixture 改成 mismatch 形状，#163 既有断言全部走修好的路径；补两侧负向用例与真实 manifest 用例 | T01 | completed |
| T03 | `03` §11 把「查不到该项目条目」更新为跨两份 manifest 的说法 | T01 | completed |
| T04 | `bash -n`、`bash codex/tests/smoke.sh`、可用时 ShellCheck | T01–T03 | completed |

## 改动点

### T01 `codex/tools/mark-completed-issues.sh`

在现有 governance manifest 解析块之后插入同构的 access manifest 解析块（同一段注释风格，
说明为什么需要第二份 manifest）：

```
access_manifest="${AISOFT_ACCESS_MANIFEST:-}"
  → "$tool_dir/../config/host-access-broker.json"
  → /usr/local/share/aisoft/host-access-broker.json
[ -f "$access_manifest" ] || fail "host access manifest not found: $access_manifest"
```

反查，与 governance 那次同一种 fail-closed 写法：

```
repository="$(jq -er --arg id "$project" '
  [.projects[] | select(.project_id == $id)] as $entries
  | if ($entries | length) == 1 then $entries[0].repository
    else error("not exactly one manifest project with id " + $id) end
' "$access_manifest")"
```

失败时 `fail "cannot resolve repository for project id $project from $access_manifest: ..."`。

随后把既有 governance 查询的 `--arg name "$project"` 改成 `--arg name "$repository"`，
报错文案改成 `cannot read deployment_lifecycle for repository $repository (project $project) from $manifest: ...`。

`$project` 传给 broker 的那一行（`:222`）不动。`requires-deployment` / `no-deployment-chain`
两条 detail 文案里出现的项目名改用 `$repository`——那句话说的是仓库有没有部署链路。

### T02 `codex/tests/test-mark-completed-issues.sh`

fixture 新增 access manifest（`$TMP/host-access-broker.json`），三条映射刻意做成
**两种形状都覆盖**：

| project_id | repository | governance 声明 |
|---|---|---|
| `aisoft-platform` | `aisoft-platform` | 无（缺省）——coinciding 回归覆盖 |
| `no-deploy-project` | `NoDeployRepository` | `none` |
| `explicit-deploy-project` | `ExplicitDeployRepository` | `application-deploy` |

`run` / `run_with_manifest` 两个 helper 同时导出 `AISOFT_ACCESS_MANIFEST`。
#163 留下的断言**语义逐条不变**，只是 `--project no-deploy-project` 现在要经过反查才拿到
`NoDeployRepository` —— 这正是 AC-2「取值由 repository 侧决定、与 project id 字面值无关」的证据。

既有的「仓库布局解析」用例（`$TMP/config/`）同时放两份 manifest，覆盖两条 layout 分支。

新增用例：

- **access 侧缺失**：`--project absent-project` → 非零退出，消息含 access manifest 路径与
  `absent-project`，不含 `deployment_lifecycle`；dry-run 与 `--apply` 都是，broker.log 为空。
- **governance 侧缺失**：access manifest 里加一条 `dangling-project → DanglingRepository`，
  governance 里没有该 repository → 非零退出，消息含 `DanglingRepository`。
  （这个形状真实 manifest 里不可能出现——`contract.py:405` 会拒绝——但工具不能假设自己读到的
  一定是被校验过的文件，这条用例钉的是工具自身的 fail-closed。）
- **access manifest 不可读**：文件不存在 / 非法 JSON → 非零退出。
- **真实 manifest 对**：`AISOFT_ACCESS_MANIFEST` 与 `AISOFT_GOVERNANCE_MANIFEST` 指向
  `$ROOT/codex/config/` 下两份真实文件，`--project localwms` + 含 `verification` 的 fixture Issue
  → `skip` / `requires-deployment`（`LocalWMS` 未声明 → 缺省 `application-deploy`），
  且退出 0。这一条同时钉住 AC-1 与 AC-2 在生产 manifest 上的结论；
  它只断言解析成功与结论，不复制 manifest 内容——真实 manifest 的键值仍由
  `codex/runtime/tests/test_deployment_lifecycle.py` 钉。

### T03 `03-Issue-Spec-Plan与单闸门开发流程.md` §11

- 「manifest 读不到或查不到该项目条目时，工具报错退出而不是静默跳过」改写为跨两份 manifest：
  `--project` 收的是 host-access manifest 的 project id，repository 由它反查，
  两侧任一查不到都报错退出。
- 声明缺失走缺省（`application-deploy`）这一句不动。

## 验证映射

| AC | 验证方式 |
|---|---|
| AC-1 | `test-mark-completed-issues.sh`：mismatch fixture（`no-deploy-project → NoDeployRepository`）在 dry-run 与 `--apply` 下都退出 0；真实 manifest 用例 `--project localwms` 退出 0 |
| AC-2 | 同一个 project id 只改 governance 侧声明就翻转结论：`NoDeployRepository`(none) → `no-deployment-chain`，`ExplicitDeployRepository`(application-deploy) → `requires-deployment`；真实 manifest 上 `localwms` → `requires-deployment` |
| AC-3 | 三条负向用例（access 侧缺失 / governance 侧缺失 / access manifest 不可读）均非零退出，消息各自指名；broker.log 为空 |
| AC-4 | #163 与 #115 留下的既有断言全部保留并通过；`aisoft-platform` coinciding 映射单独覆盖 |
| AC-5 | 上述用例都在 `test-mark-completed-issues.sh` 内，由 `smoke.sh:157` 调起 |
| AC-6 | `bash -n codex/tools/mark-completed-issues.sh codex/tests/test-mark-completed-issues.sh`；`bash codex/tests/smoke.sh`；`command -v shellcheck` 有则跑 |

## 回滚

单 PR，revert 即可。工具级改动，无迁移、无制品、无部署，回滚后行为回到本变更前
（mismatch 项目重新不可用，coinciding 项目不受影响）。

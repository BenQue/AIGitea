---
issue: 143
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/143
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - agent-governance
  - platform-governance
  - security
depends_on: []
status: approved
branch: change/143-broker-actions-run-read
created: 2026-08-22
updated: 2026-08-22
---

# Spec：broker 只读 Actions 运行与日志操作

## 1. 目标

让 agent 能从一个 commit SHA 出发，拿到该 SHA 对应 Actions 运行的**步骤级结论**，并在需要时拿到某个 job 的**日志**——两件事都只读、都 project-scoped、都有显式的体量与脱敏边界。

## 2. 裁决一：本机 Gitea 1.26.4 实际可用的端点（先核实，不照抄）

`environment = local-orbstack`，`GET /api/v1/version` 返回 `{"version":"1.26.4"}`。端点形状从**本机自己的** `/swagger.v1.json` 读出（匿名可读的 API 文档端点，不涉及任何凭据、不返回任何仓库数据）：

| 端点 | 返回 | 用途 |
|---|---|---|
| `GET /repos/{owner}/{repo}/actions/runs?head_sha=<sha>` | `ActionWorkflowRunsResponse{total_count, workflow_runs[]}` | 由 SHA 找运行 |
| `GET /repos/{owner}/{repo}/actions/runs/{run}/jobs` | `ActionWorkflowJobsResponse{total_count, jobs[]}` | 运行下的 job |
| `GET /repos/{owner}/{repo}/actions/jobs/{job_id}/logs` | `text/plain` | 一个 job 的日志 |

关键事实：`ActionWorkflowJob` 带 `steps` 数组，元素为 `ActionWorkflowStep{name, number, status, conclusion, started_at, completed_at}`。**步骤名、结论与耗时都能直接拿到，不需要解析日志**——这决定了 §3 的操作粒度。

### 2.1 被否决的候选形状

- **`GET /repos/{owner}/{repo}/actions/tasks`**：返回的是较旧的 `ActionTask` 形状（`status`、`run_number`、`head_sha`…），**没有 `steps`**。用它就只能回到「整体成功/失败」，正是本 Issue 要解决的那堵墙。
- **`GET /admin/actions/runs`**（以及 `/orgs/{org}/…`、`/user/…` 三个同名端点）：跨仓库、要 site-admin 身份。与「project-scoped」直接冲突，且 broker 的 project-agent 身份本就不该有 site-admin（`_verify_identity` 显式拒绝带 `is_admin` 的自动化身份）。
- **`GET /repos/{owner}/{repo}/actions/runs/{run}` 作为唯一入口**：可用，但要求调用方先从 `target_url` 里抠出 run id（见 §4）。
- **所有 `rerun` / `dispatches` / `disable` / `enable` 端点**：写操作，明确不做。

## 3. 裁决二：两个操作，而不是一个

| 操作 | 入参 | 回答什么 |
|---|---|---|
| `gitea.actions.run.read` | `sha` | 哪些 job、哪些步骤、各自结论与耗时 |
| `gitea.actions.job.logs.read` | `job` | 某个 job 到底输出了什么 |

**为什么不是一个**：两者代价差一个数量级。步骤级摘要是几百字节的结构化数据，日志可以是几 MB。把它们合成一个操作，等于每次想问「那 8 个步骤跑了没有」都要把整份日志拖进上下文——而 §2 已经证明这个问题**根本不需要日志**就能回答。分开之后，便宜的问题有便宜的答案。

**为什么不是只做摘要**：Issue 的「更大的代价」一节说的是 CI 失败无法排查。一次失败时 agent 现在只有 `status = failure`；有了 `run.read` 也只多出「哪个步骤 failure」。要回答「为什么」，必须能看到那个步骤的输出。

## 4. 裁决三：入参用 SHA（日志用 job id，但不需要抠 URL）

`gitea.actions.run.read` 用 `--sha`，与 `gitea.commit.status.read` 同构：

- 调用方手上本来就有 SHA（刚推的 commit、PR 的 head），**不需要从 `target_url` 里抠 run id**；
- 一个 run id 在调用方手里不带任何项目归属信息，用它当主入参会让「这个 id 属于哪个仓库」变成调用方的责任；SHA 加上 project-scoped 的 URL 前缀则天然闭合。

`gitea.actions.job.logs.read` 只能用 job id，因为 Gitea 只按 job 暴露日志。但这不构成「抠 URL」：**job id 来自 `run.read` 的返回**，调用方永远不需要解析 Web UI 路径。

### 4.1 SHA 必须精确（并纠正 Issue 的一处前提）

`--sha` 必须精确匹配 `^[0-9a-f]{40}$`（复用既有的 `COMMIT_SHA_RE`）：缩写 SHA 在发出任何请求之前就被 `ARGUMENT_INVALID` 拒绝，因此「没有运行」与「你给错了 SHA」不可能混淆。

**Issue 正文说 `gitea.commit.status.read` 在缩写 SHA 上返回 `statuses: []` 的假成功，这一条与当前代码不符。** `broker.py` 对该操作已经有同一条精确 SHA 校验，实测（已安装的 broker，`--sha 90ca1f9`）返回的是：

```
{"code": "ARGUMENT_INVALID", "message": "commit status requires an exact lowercase SHA-1", ...}
```

也就是说这个坑此前已经堵上了。本操作沿用同一条既有规则，而不是新发明一条——记在这里是为了不把一个已被修掉的问题当作本变更的功劳。

### 4.2 空结果与读取失败的区分

- SHA 合法但没有对应运行 → `{"sha": …, "total_count": 0, "runs": []}`，`status` 为 `PASS`；
- 仓库不存在 / 无权限 / 上游异常 → `BrokerError`，即 `{"code": "HTTP_404" | "HTTP_403" | …, "status": "BLOCKED_EXTERNAL"}`，非零退出。

两者在返回结构上完全不同形，读者不需要靠猜。

## 5. 裁决四：脱敏（本变更唯一的实质风险）

Actions 日志可能包含环境变量、token 或依赖源地址。broker 是治理写路径的收口，开一个能把 runner 日志原样吐出来的读操作，**必须先回答脱敏问题**。

### 5.1 两层，不是一层

- **第一层（上游）**：Gitea 自己会把注册为 Actions secret 的值在日志里掩成 `***`。这一层免费，但只覆盖「注册过的 secret」。
- **第二层（broker 侧）**：只覆盖第一层管不到的东西——workflow 里从别处取得、未注册为 secret 的凭据。这是 `.gitea/workflows/` 里最容易出现的形态。

只靠第一层不够：它的覆盖面等于「有人记得把它注册成 secret」，而忘记注册正是凭据泄漏最常见的成因。

### 5.2 第二层实际掩掉什么

1. **本次请求所用的凭据本身**（精确字符串匹配）——最强的一条：broker 手里就有那个 token 的明文，日志里出现它必然是泄漏；
2. `Authorization: token|Bearer|Basic <值>` 的值部分；
3. URL 里的 userinfo（`scheme://user:pass@host` → `scheme://***@host`）；
4. 形如 `NAME=值` / `NAME: 值` 且 `NAME` 含 `TOKEN`/`SECRET`/`PASSWORD`/`PASSWD`/`API_KEY`/`APIKEY`/`PRIVATE_KEY`/`CREDENTIAL` 的赋值；
5. GitHub 式前缀 token（`ghp_`/`gho_`/`ghs_`/`ghu_`/`ghr_`/`github_pat_`）；
6. PEM 私钥块（`-----BEGIN … PRIVATE KEY-----` 到 `-----END … PRIVATE KEY-----` 整块）。

### 5.3 刻意不掩什么，以及为什么

**不掩裸的 40 位十六进制串。** 它与 commit SHA 完全同形，而 SHA 恰恰是 CI 日志里最有用的东西之一。掩掉它会让这个操作在排查「CI 上跑的是哪个 commit」时变成废的——用一个必然的功能损失，换一个假想的收益。Gitea 的 token 若以裸 40-hex 出现在日志里，由 5.2 第 1 条（精确匹配本次凭据）与第 2、4 条（出现位置几乎必然是 header 或赋值）覆盖。

这条边界写在这里，是为了让它是一个**被记录的裁决**，而不是一个实现时的疏忽。

### 5.4 脱敏不静默

返回里带 `redactions: <次数>`。掩掉了东西却不说，与静默截断是同一类错误：读者会以为自己看到了原文。

## 6. 裁决五：截断策略

- 返回上限 **64 KiB**，取**尾部**——失败步骤的报错打印在最后，头部截断会正好丢掉要看的东西；
- 返回里带 `truncated`（bool）、`original_bytes`、`returned_bytes`；`truncated` 为真时正文前置一行 `[truncated: 前 N 字节已省略]`；
- 64 KiB 与 `verifier.py` 既有的输出截断上限一致，不引入第二个数字。

### 6.1 一个诚实的边界

截断发生在**读完整个响应体之后**：`_default_transport` 用 `urlopen(...).read()` 一次读完，broker 没有流式读取层。因此 64 KiB 限制的是**进入 agent 上下文**的体量，不是 broker 进程的峰值内存。为一个只读诊断操作引入流式传输层不划算，但这个边界必须写明，而不是让人以为它也保护了内存。

## 7. 裁决六：project-scoped 与不做写操作

- 两个操作的 URL 都由 `project.repository` 拼出，与所有其它 `gitea.*` 操作同构。另一个仓库的 job id 打到本项目的 URL 上会得到 HTTP 404 → `HTTP_404`，读不到别的项目的运行；
- `identity_route` 为 `project-agent`，`mutating: false`；
- **刻意不做** `rerun` / `rerun-failed-jobs` / `dispatches` / workflow 的 `enable`/`disable`。理由同 `gitea.labels.*` 与 `gitea.issue.comments.read` 那两条注释：触发或重跑 CI 是人的决定，typed 化等于给出一条可自动化的路径。加测试钉住这一点。

## 8. Acceptance criteria

- [ ] 核实并记录 Gitea 1.26.4 上实际可用的 Actions 只读端点，spec 写明被否决的候选形状与理由（§2、§2.1）；
- [ ] 新增的 typed 操作是只读的（`mutating: false`）且 project-scoped——不能读到本项目仓库以外的运行；
- [ ] 能从一个 commit SHA 出发拿到该 SHA 对应运行的步骤级结论（步骤名 + 状态/结论 + 耗时）；
- [ ] 截断策略显式，被截断时返回里有明确标记，不静默丢内容；
- [ ] 脱敏方案有书面裁决（§5），并有负向验证：日志里放一个可识别的假凭据，确认返回中它不以明文出现；
- [ ] 负向验证：不存在的 SHA / 无运行的 SHA 返回可判读的空结果，与「读取失败」区分开；缩写 SHA 走 `ARGUMENT_INVALID` 而不是假成功；
- [ ] `bash codex/tests/smoke.sh` 全过，操作计数枚举点同步更新（27 → 29）；
- [ ] 用真实数据验证一次：对 `admin/LocalWMS` 的 run 493 取出步骤级结论，据此回答「那 8 个步骤是否都执行了」。

## 9. 明确不做

- 不新增任何写操作（不触发、不取消、不重跑 workflow）；
- 不改 `gitea.commit.status.read` 的现有返回形状；
- 不碰任何目标仓的 `.gitea/workflows/`；
- 不为本变更新增 `runner.py` 便捷方法——Loop 运行时目前没有消费方，加了就是未使用代码（与 #138 的处理一致）；
- 不新增或放宽任何 token scope。

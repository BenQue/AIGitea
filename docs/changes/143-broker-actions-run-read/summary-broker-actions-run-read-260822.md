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
pr_url:
created: 2026-08-22
updated: 2026-08-22
reason: 变更 host-access broker 的 typed 操作面，属 Agent/治理类别，强制 complex；新增读操作会把 runner 日志带进 agent 上下文，另命中 security 维度
required_docs:
  - summary
  - spec
  - plan
  - verification
override_reason: ''
documents:
  summary: summary-broker-actions-run-read-260822.md
  spec: spec-broker-actions-run-read-260822.md
  plan: plan-broker-actions-run-read-260822.md
  verification: verification-broker-actions-run-read-260822.md
---

## 问题/需求总结

broker 的 27 个 typed 操作里**没有任何一个能读 Gitea Actions 的运行或步骤信息**。CI 证据只能停在 `gitea.commit.status.read`，它返回 `context` / `status` / `description` / `target_url` 四项，其中 `target_url` 是一个 Web UI 路径，broker 没有任何操作能顺着它取到内容。

两个方向的代价都是真实的：

- **绿了读不懂**：`admin/LocalWMS` 连续三次交付（#5、#11、#16）在 verification 里留下同一条「未能进一步核实」——报告时长与 job 的工作量对不上，但没有任何手段去核实某个步骤到底执行了没有。
- **红了更读不懂**：一次 CI 失败，agent 能拿到的只有 `status = failure`——没有失败步骤名、没有报错输出。唯一排查路径是本地复现，而 runner 是 host 模式、走本机 Verdaccio、用 PGDG 装的 PostgreSQL 17，本地环境与它并不等价。凡是「只在 CI 上失败」的问题，现在没有可走的诊断路径。

## 影响范围

- `codex/config/host-access-broker.json`：新增两个只读 typed 操作（27 → 29）；
- `codex/runtime/aisoft_host_access/{contract,broker,cli}.py`：操作表、参数校验、执行器、`--job` 入参；
- `codex/runtime/tests/test_host_access.py`、`codex/tests/test-host-access-broker.sh`：操作表与计数枚举点；
- `06-运维踩坑与经验总结.md`：记录新能力与安装前置。

不新增任何写操作，不改 `gitea.commit.status.read` 的返回形状，不碰任何目标仓的 `.gitea/workflows/`。

## 初步方案与建议

新增两个只读操作：

1. `gitea.actions.run.read --sha <40 位 SHA>`：顺着 SHA 拿到对应运行的 **job 与 step 级结论**（步骤名、状态、结论、耗时）。这一条就能回答 Issue 的原始疑问，且完全不涉及日志正文。
2. `gitea.actions.job.logs.read --job <id>`：拿一个 job 的日志，尾部截断且截断有显式标记，broker 侧再做一层脱敏。

端点形状先在本机 Gitea 1.26.4 的 `/swagger.v1.json` 上核实，不照抄上游文档。

## 风险

- **敏感信息**：这是本变更唯一的实质风险。开一个能把 runner 日志吐进 agent 上下文的读操作，必须先回答脱敏问题，而不是留到实现阶段。裁决与其边界见 spec §5。
- **上下文体量**：CI 日志可以很大，返回要走进 agent 上下文。截断策略必须显式，且截断本身要在返回里标明——静默截断会让读者以为自己看到了全部。
- **合并 ≠ 可用**：broker 是 root-owned 的安装期快照，本变更合并后必须在 Mac 与 gitea-ci VM **两台**重装才生效，Mac 那台需要人输密码。未重装时新操作会返回 `REQUEST_DENIED`，读起来像权限问题。

## AI 判级

```yaml
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
```

强制规则命中：改动 broker 的 typed 操作面（Agent/治理维度）；新增的读操作把 runner 输出带进 agent 上下文（安全维度）。→ 需 summary + spec + plan + verification。

## 证据

- 本机 Gitea `GET /api/v1/version` → `{"version":"1.26.4"}`；`/swagger.v1.json` 匿名可读（不涉及凭据），其中 `ActionWorkflowJob.steps` 为 `ActionWorkflowStep{name,number,status,conclusion,started_at,completed_at}` 数组，`/actions/runs` 支持 `head_sha` 查询参数；
- `codex/runtime/aisoft_host_access/contract.py:EXPECTED_OPERATIONS` 现有 27 项，无 Actions 相关项；
- Issue #143 正文记录了 LocalWMS #5/#11/#16 三次 verification 的同一条「未能进一步核实」。

## 缺失验收标准

- 无；Issue 正文的验收标准逐条可测，spec §8 给出映射。其中「用 run 493 的真实数据给出结论」依赖 broker 重装（人工前置），verification 如实记录其状态。

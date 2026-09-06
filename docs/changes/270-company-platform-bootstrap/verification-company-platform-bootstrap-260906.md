---
issue: 270
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/270
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - platform-governance
  - deployment
depends_on:
  - 268
status: approved
branch: change/270-company-platform-bootstrap
created: 2026-09-06
updated: 2026-09-06
---

# 验证与最终 PR 候选

## Exact context 与范围裁定

- Issue：#270（A1）；branch：`change/270-company-platform-bootstrap`。
- worktree：`/private/tmp/issue-270-company-platform-bootstrap`。
- base：`2a012bd`（#268 PR #269 已合并）；依赖 #268 broker 读回 `closed + completed`。
- clean implementation pin：`4caf73f9c140a01ba7afd425c9e1fd949a1a63a0`。下方 bundle、negative、dry-run 使用此 pin；最终证据提交只改本 Issue 文档，不改 package/runtime/tests。
- 用户已确认启动；调度任务 `01a0762f-10f7-7543-8936-d90ec3907706` 在本次 T03 明确裁定：A1 只要求完整动作协议 source；不要求实现/绑定现场 executor；非 dry-run 的 `SITE_EXECUTOR_NOT_BOUND` 是应通过的安全负向。不得为此新增现场 adapter、连接现场或 push/PR。

## 分层结论

| 层 | 结果 | 范围 |
|---|---|---|
| source | PASS | 严格 schemas、独立 builder/verifier、采用分流、七类动作协议、双轴修复及复核 |
| local targeted | PASS | 35 项目标测试；85 项原 company-delivery 兼容回归；真实 clean source 两次构建及负向/dry-run |
| local controlled locale | PASS | host `LC_ALL=C bash codex/tests/smoke.sh` exit 0；包含完整 734 个 Python tests（78.048s）、ShellCheck/static/shell fixture gates |
| local default locale | GAP / external to #270 | host `LC_ALL=C.UTF-8` 的完整 smoke 在 #268 F8 registry 负向中失败：expected exit 1 / actual 0；属于 A2，未修改相关文件 |
| installed | NOT RUN | 没有真实工具安装、profile/服务/权限调整；smoke 中 installer 只写临时 fixture，不是 installed acceptance |
| company live | NOT RUN | 无公司连接、环境探测、凭据、仓库创建、Runner/timer 启用、部署或恢复操作 |
| remote PR/CI/merge | NOT RUN | 最终 PR 提交确认尚未取得；未 push/建 PR/merge |

C locale 的 PASS 不替代默认 locale GAP，也不表示 Gate A/B 已完成。调度任务明确允许在此真实分层下完成 A1 source/local 并停在最终 PR 确认。

## 本地测试命令与结果

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=codex/runtime \
  python3 -m unittest discover -s codex/runtime/tests -p test_platform_bootstrap.py -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=codex/runtime \
  python3 -m unittest discover -s codex/runtime/tests -p test_company_delivery.py -q
LC_ALL=C bash codex/tests/smoke.sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=codex/runtime \
  python3 -m aisoft_loop.cli check-change-documents --repo .
git diff --check
```

- 目标回归：35/35 PASS；新增 fsmonitor 不执行、工作树并发变化不进入 pinned archive、无仓库虚构保护/CI 拒绝、每动作负向权限必需、action exact 参数/hash 绑定、staging/contexts 冲突与路径穿越拒绝。
- application 回归：85/85 PASS（18.461s）；未修改 `company-delivery/` 或 `aisoft_company_delivery`。
- 初始实现独立全量 Python：727/727 PASS（56.151s）；修复后完整 `LC_ALL=C` smoke 全量：734/734 PASS（78.048s）。后者覆盖前者与新增回归。
- 文档/PR URL 门禁：124 个 change，PASS 2、GAP 0；四角色 resolver 与 exact tuple 一致。最终文档提交前再次执行。
- 本 Issue 没有新增/修改 shell 脚本；入口是 Python。完整 smoke 自带既有 `bash -n`/ShellCheck 门禁，未额外扩大脚本范围。
- 两次 sandbox smoke 都在临时 `127.0.0.1` socket bind 被 sandbox 拒绝（`PermissionError: Operation not permitted`），均未完成；host 路径越过该限制。该状态为执行路径 BLOCKED，不是公司网络/ACL 故障。没有运行 diagnostics、写 credential 或修服务。
- host 默认 locale 失败日志：`registry-preflight test: 停掉 registry 之后：期望退出 1，实际 0`。其文件保持原样，不把这个结果改写为 PASS。

## 实际 clean source 双构建与故意失败

使用与仓库工具相同的公开 CLI，source pin 为上文完整 SHA；本地测试批准引用为 `approval/issue-270-local-validation`。
输入 asset/transport/package-set/approval 值均为明确的 local fixture，不声称公司已经批准或具备真实资产。
两份输出目录 mode 0700，位于 worktree 外部，以保持 builder 的 clean-source 门。

| 对象 | 真实结果 |
|---|---|
| archive A/B | byte-identical，`5aa2036b3a332f2dd0107c1c1e3e0baabc36073e2d3ecb83ae3961e0196e9b5e` |
| handoff A/B | byte-identical，`8cacdf62bfc01a029fb675b856115749081d2a0f819ee8c02ced0e6706b3691a` |
| verify-handoff A/B | PASS；`target_facts=NOT_READ`、`execution=NOT RUN` |
| 故意改 archive 最后一个 byte | exit 2，`CHECKSUM_MISMATCH`；拒绝后未解包/执行 |
| 故意使用错误完整 source SHA | exit 2，`IDENTITY_MISMATCH`；输出目录保持空 |
| inventory/adoption-plan | schema PASS；`first-install / PLANNED`，精确绑定 uninstalled 回退身份 |
| apply --dry-run / rollback --dry-run | `DRY_RUN`、`execution=NOT RUN`，只生成 exact repo-bootstrap 请求 |
| apply 不带 --dry-run | exit 2，`SITE_EXECUTOR_NOT_BOUND`；未创建输出，无 fallback |
| 全部七类动作、adopt no-op、恢复 observation | 由 35 项目标回归验证；只证明 local protocol 行为 |

完整本地 evidence 目录：
`/private/tmp/issue-270-bootstrap-evidence/4caf73f9c140a01ba7afd425c9e1fd949a1a63a0/`。
其中 `acceptance.json`、`build-a.json`/`build-b.json`、两份 `*-verified.json`、`checksum-failure.json`、
`identity-failure.json`、`adoption-plan.json`、`apply-request.json`、`rollback-request.json` 和
`unbound-executor.json` 分别保存结果。归档位于 `build-a/` 与 `build-b/`，不提交生成制品。
证据索引和日志 hash 见同目录 `evidence-index.json`；可按 runbook 在任意受信开发侧重新构建/验证。

## 双轴审查与修复

使用 vendored `code-review`，分别派发 Standards/Spec 只读审查（Sol/high）。首次比较 `2a012bd...3177d30`，复核 `3177d30..4caf73f`。

| 轴 | 首轮实际发现 | 修复/复核 |
|---|---|---|
| Standards | approved SHA/工作树 TOCTOU、无仓库虚构 protection/CI no-op、required-ci 缺 negative、Git fsmonitor/config 外部执行、manifest 相对 path 不严格 | 五项均 CLOSED；无剩余 actionable finding |
| Spec | action-specific 参数未纳入请求、Git TOCTOU、required-ci 缺 negative；verification 尚未写入为 T03 已知待办 | 三项代码 finding 均 CLOSED；本记录补齐实际证据；无 scope creep |

修复后直接读取 approved tree/blob 并在发布前复核 clean；target/plan/request 用逐动作 closed schema 固定 exact 输入，
前驱列表与明确 unbound executor 一起进入请求；所有 PASS 均要求 negative-permission。
reviewer 未冒充运行测试，其结论为代码复核；测试由本任务外层命令实际运行。

## 分类投影、triage 与最终闸门

- `apply-classification-labels.sh` 已完成 dry-run → apply → verify，最终读回 `result=projected`、`type/platform`、`complexity/complex`。
- 已确认合同的生命周期投影为 `approved` 并读回。合并策略为 `manual`，未创建额外 policy 标签。
- 本地 triage 已完成 enhancement/ready-for-agent 判断和 Agent brief（summary/spec/plan）。live 的 `triage/needs-triage` 仍存在：当前 broker 没有 triage 维度 typed writer；没有绕过 broker 或擅自安装工具修标签。此处保留真实差异，不把本地判断当 live projection。
- 持久状态：`AWAITING_PR_CONFIRMATION`。T01/T02/T03 source/local 工作完成；最终 PR 提交确认未取得。
- 下一步仅在用户确认 exact Issue #270、`change/270-company-platform-bootstrap`、manual 后，才允许 Controller push/创建唯一最终 PR 并修复范围内 CI；required CI 通过后停在 `READY_FOR_REVIEW`，由人合并。merge 不授予部署权限。

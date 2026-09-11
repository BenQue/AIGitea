---
issue: 290
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/290
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - security
  - deployment
status: approved
branch: change/290-scm-test-deploy
created: 2026-09-11
updated: 2026-09-11
---

# 分阶段验证

## 基线与授权读回

- 工作树：`/private/tmp/issue-290-scm-test-deploy`，branch `change/290-scm-test-deploy`。
- T01：`75906433a77edbac6f6db603b5760a6a117100a8`，仅 6 个合同文档，原任务已停止。
- 本地 `origin/main` 基线：`64f1cda0de9735f8782e64a5b07af2ce8460e4c3`；本轮未 fresh-fetch，
  不将这个本地 ref 当作当前远端 main 的证明。
- 2026-09-11 新任务完整读取适用 AGENTS、aisoft-platform 技能与映射的 4 份语义文档。
- broker `gitea.issue.read --number 290` 现场读回 open，标签为 approved、type/platform、
  complexity/complex，正文 AC-1–5 与本地已批准 spec 一致，无评论。
  sandbox 路径最初 TRANSPORT_ERROR，同一只读操作在获准宿主路径成功；不是公司主机访问。
- broker `gitea.pulls.read --state open` 返回 `[]`，当前无已开放 PR；没有创建重复对象。

## 实现与 AC 证据

runtime 仅修改 `runner._host_role_preflight`：已识别 action 且 protected profile 为
`host_role=scm-ci`、`environment=test` 时加入允许集合。hostname 仍先验证；未知 role/environment
仍由既有严格 profile parser 拒绝；未知 action 不进入例外。未改变 schema、stage grant、
Docker adapter、artifact/architecture/capability 校验或部署状态机。

| AC | 本地验证 | 结果 |
|---|---|---|
| AC-1、AC-3 | 3 roles × 2 environments × 8 actions = 48 格表驱动预检；两种 scm-ci 环境的 verify/verify-target 无 mutation、无状态创建 | PASS |
| AC-2 | 六个 production 动作逐一走公开入口，零 Docker events，未创建 state root；已有 state 的拒绝路径保持原字节 | PASS |
| AC-2 | 未知 role/environment、hostname 漂移覆盖 8 个公开入口；未知 action 覆盖两条内部验证链路，全部在 Docker/状态前拒绝 | PASS |
| AC-3、AC-4 | scm-ci/test 复用既有部署顺序、重复 healthy-noop、迁移只跑一次、迁移失败禁止自动重试、健康失败与 identity 漂移回滚、显式 rollback、status 测试 | PASS |
| AC-3、AC-4 | scm-ci/test 独立 stage/migrate/activate 流程，缺 staging/migration receipt 仍拒绝；migrate 只迁移、activate 只启动 | PASS |
| AC-4 | 全部 release tests，包括既有 profile/artifact/compatibility/action gate 回归 | PASS，107 tests |
| AC-5 | README 与 docker-release README 区分 source/local、installed/live，保留独立 Compose project、目录、数据库、端口要求 | PASS（文档） |

命令在上述工作树执行：

```text
PYTHONPATH=codex/runtime:. python3 -B -m unittest discover -s codex/runtime/tests -p 'test_release*.py'
Ran 107 tests in 0.881s
OK

PYTHONPATH=codex/runtime python3 -B -m aisoft_loop.cli check-change-documents --repo /private/tmp/issue-290-scm-test-deploy
PASS: change-documents
PASS: change-pr-url
result: changes=132 pass=2 gap=0

bash codex/tools/apply-classification-labels.sh --verify 290 --repo /private/tmp/issue-290-scm-test-deploy
result=projected; change_type=platform; complexity=complex; applied=false

git diff --check
exit 0，无输出
```

## 交付边界与恢复

- source/local：PASS；测试使用 task-local fixtures 和 FakeDocker，未调用真实 Docker。
- T02 runtime 与测试已本地提交为 `b2cc0a3`；T03 验证与说明独立本地提交，尚未 push。
  适用 AGENTS.md 第 29 行明确允许 Agent 在 exact change 分支按 plan frontier 本地原子 commit。
  原交接中“Git/Gitea 写操作必须走 typed broker”是概括，创建者已澄清并非用户额外禁止本地 commit；
  已修正由此产生的阻塞判断。远程 Git/Gitea 仍使用 typed broker，最终 PR 确认未被替代。
  本次收尾仅改文档并提交此前已验证的代码，未无理由重跑 107 项 release tests。
- 唯一 manual PR：AWAITING_PR_CONFIRMATION；required CI：NOT RUN。
- installed/runtime byte parity：NOT RUN；company live / NewEMaint 测试部署：NOT RUN。
- 未访问公司主机、安装部署、重启服务、修改 UFW、读取秘密、迁移或恢复实际数据库。
  现场必须由用户手工拷贝离线文件并按项目独立授权执行；应用隔离资源不得覆盖 Gitea。
- 无 shell 修改，shell smoke/bash -n/ShellCheck 本轮 NOT RUN，按 plan 不增加 shell 专项。
- source 恢复可撤销本 Issue 的 runtime commit `b2cc0a3`，恢复原 scm-ci 部署拒绝规则；
  不自动停用现有容器或恢复数据库，现场回滚属于项目独立授权范围。

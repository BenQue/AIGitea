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
status: pr-open
branch: change/290-scm-test-deploy
created: 2026-09-11
updated: 2026-09-11
---

# 分阶段验证

## 基线与授权读回

- 工作树：`/private/tmp/issue-290-scm-test-deploy`，branch `change/290-scm-test-deploy`。
- T01：`75906433a77edbac6f6db603b5760a6a117100a8`，仅 6 个合同文档，原任务已停止。
- 实现时本地 `origin/main` 基线：`64f1cda0de9735f8782e64a5b07af2ce8460e4c3`。
  后续 typed broker 推送已 fresh-fetch 并通过 ancestry gate；CI 的 merge preview 也记录同一 base。
- 2026-09-11 新任务完整读取适用 AGENTS、aisoft-platform 技能与映射的 4 份语义文档。
- broker `gitea.issue.read --number 290` 现场读回 open，标签为 approved、type/platform、
  complexity/complex，正文 AC-1–5 与本地已批准 spec 一致，无评论。
  sandbox 路径最初 TRANSPORT_ERROR，同一只读操作在获准宿主路径成功；不是公司主机访问。
- 创建前 broker `gitea.pulls.read --state open` 返回 `[]`。用户确认后已创建唯一 manual PR #291；
  当前 head 为 `27fa30d55e35ae2f56072cddef7d9f37d55046d1`，不是仍等待 PR 创建确认。

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
- T02 runtime 与测试提交为 `b2cc0a3`；T03 文档为 `ba01de9`；PR 回填为 `27fa30d`，均已 push。
  适用 AGENTS.md 第 29 行明确允许 Agent 在 exact change 分支按 plan frontier 本地原子 commit。
  原交接中“Git/Gitea 写操作必须走 typed broker”是概括，创建者已澄清并非用户额外禁止本地 commit；
  已修正由此产生的阻塞判断。远程 Git/Gitea 仍使用 typed broker，最终 PR 确认未被替代。
  本次收尾仅改文档并提交此前已验证的代码，未无理由重跑 107 项 release tests。
- 唯一 manual PR：#291 已开放且未合并。required CI：FAIL；用户已批准方案 B 的合同增补，
  当前 T04 治理合同阶段，fresh run 待实施 T05/T06，不重复请求 push/创建 PR。
- installed/runtime byte parity：NOT RUN；company live / NewEMaint 测试部署：NOT RUN。
- 未访问公司主机、安装部署、重启服务、修改 UFW、读取秘密、迁移或恢复实际数据库。
  现场必须由用户手工拷贝离线文件并按项目独立授权执行；应用隔离资源不得覆盖 Gitea。
- 本地未修改 shell，bash -n/ShellCheck 未额外运行。远端 full smoke 已运行并失败，见下节。
- source 恢复可撤销本 Issue 的 runtime commit `b2cc0a3`，恢复原 scm-ci 部署拒绝规则；
  不自动停用现有容器或恢复数据库，现场回滚属于项目独立授权范围。

## PR / CI 真实状态及后续本地分析

- PR #291，policy manual；exact head `27fa30d55e35ae2f56072cddef7d9f37d55046d1`。
- Required context `CI / verify (pull_request)`：FAIL；run/job #1271，Platform smoke suite 失败。
- CI merge preview 确认 base `64f1cda0de9735f8782e64a5b07af2ce8460e4c3` 是 head 祖先。
- 原因：历史 #65 harness 要求相对其 delivery base 的 runtime 变更文件仅为 transport.py；
  当前另有 #290 已批准的 runner.py，故拒绝。执行前、执行后均有检查，不能只修改一处。
- 本地 107 release tests PASS 与远端 full smoke FAIL 分开记录，未声称 READY_FOR_REVIEW。
- 后续受托本地分析逐文件核对 runtime 的 12 个文件：相对 #290 前基线只有 runner.py 差异，
  当前 runner 精确为原文件加六行测试例外，无额外字节或路径。该只读对比不是已实现的新闸门。
- #65 immutable evidence 与基线字节相同，SHA-256 为
  `b58bb7b57d53a104f922e66c7dc1342bc1b5b133038f60fa8f2ace8d8dbdeb89`。
- 已准备本地待审批方案：固定历史 fake/static regression 与当前精确源码/行为验证分开。
  尚未修改原 #65 gate、smoke 调用、旧 evidence 或 compatibility matrix，未运行真实 Docker。
- 前述分析阶段的状态修正仅留本地；用户随后明确“同意方案 B”。T04 将 spec/plan/summary 与
  本 verification 纳入独立治理提交；公开 PR 保持精简摘要，T05/T06 fresh run 再实施已批准范围。

## T04 方案 B 授权与治理步骤

- 授权来源：用户在本任务直接回复“同意方案 B”，范围按此前完整提案及 spec AC-6/AC-7 固定。
- 当前只修改 4 份本 Change 语义文档，不修改 checker、runtime、smoke、旧 #65 evidence 或 matrix。
- 不新增 disposable E2E 要求；current real/installed/company-live 均保持 NOT RUN。
- T04 提交后停止；后续 fresh run 重读合同执行 T05/T06。本轮不无理由重跑既有 107 项测试。

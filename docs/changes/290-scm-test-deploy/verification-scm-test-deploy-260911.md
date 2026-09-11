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

## 当前结论

T05/T06 的本地 source 验收通过。唯一 manual PR #291 保持开放；以下本地结果不能替代最终
head 的 required CI，也不代表真实 Docker、安装或公司现场已验证。远端结果随推送后回读。

## 基线、授权与提交

- 工作树 `/private/tmp/issue-290-scm-test-deploy`，分支 `change/290-scm-test-deploy`。
- 固定 #290 前基线：`64f1cda0de9735f8782e64a5b07af2ce8460e4c3`。
- T01 独立治理合同 `75906433a77edbac6f6db603b5760a6a117100a8`；T02 runtime/tests
  `b2cc0a3f7c0aa3487e2de9db58335a43736b9373`；T03 文档 `ba01de9`；PR 回填 `27fa30d`。
- 用户已确认推送和提交唯一 manual PR，并明确“同意方案 B”。T04 独立合同增补
  `aba17f75665479c4219da8e9a1aa4c03f513d2c2` 提交后停止；2026-09-11 fresh run 重读
  AGENTS、spec/plan 后实施 T05/T06，沿用既有授权。
- T05 实现提交 `f13402e`，仅新增检查器/测试、补 offline 回归及 smoke 接入四文件。
- Agent 按适用 AGENTS 在 exact 分支本地原子提交；远程 Git/Gitea 使用 typed broker。
  历史上将交接概括误读为禁止本地 commit 的判断已纠正，不再作为阻塞。

## 验收覆盖

runtime 仅在 `_host_role_preflight` 的已识别 action、`scm-ci`、`test` 三个条件同时满足时
加入允许集合，共六行。hostname 先验证；未知 role/environment 由严格 profile parser 拒绝；
未修改 schema、grant、Docker adapter、artifact/architecture/capability gate 或部署状态机。

| AC | 当前本地证据 | 结果 |
|---|---|---|
| AC-1、AC-3 | 3 roles × 2 environments × 8 actions 的 48 格矩阵；scm-ci 两种环境的 verify/verify-target 无 mutation/状态创建 | PASS |
| AC-2 | 六个 production 动作公开入口均零 Docker events，无新 state，已有 state 原字节不变；未知 role/environment/action 与 hostname 漂移拒绝 | PASS |
| AC-3、AC-4 | Registry 部署顺序、幂等、迁移仅一次、迁移失败不重试、健康/identity 失败回滚、显式 rollback、status；独立 stage/migrate/activate receipt 拒绝路径 | PASS |
| AC-3、AC-4 | scm-ci/test offline-bundle 使用 load 而无 pull；重复部署 healthy-noop；新 release 健康失败恢复旧 release 与 state | PASS |
| AC-5 | README 区分 source/local 与 installed/live，保留独立 Compose project、数据库、目录和端口 | PASS（文档） |
| AC-6 | 固定 baseline、runner 六行与 hash、其它受控文件/index/磁盘原字节与模式；历史 fake 回归独立临时 clone；旧 evidence 原字节 | PASS |
| AC-6、AC-7 | 16 项检查器正反例覆盖字节/生产/未知动作扩权、未知/ignored/pyc/删除/改名/执行位/symlink、index 漂移、缺 baseline、错误 hash、子回归失败与执行中漂移 | PASS |
| AC-7 | 124 项 release tests、完整 smoke 中 890 项 Python tests 与其余平台硬门 | PASS |

检查器拒绝 caller override，不 fetch、不访问远端、不复制当前 runtime 到历史树；临时 clone
只运行原 fake harness，结束自动删除。当前范围在每个子回归前后绑定身份；任一部分失败则
整体退出非零，无 fallback。smoke 禁止写 bytecode；额外缓存文件仍拒绝，不作豁免或自动清理。

## 执行记录

在上述工作树执行：

```text
PYTHONPATH=codex/runtime:. python3 -B -m unittest discover -s codex/runtime/tests -p 'test_release*.py'
124 tests，OK

python3 -B codex/tests/check-release-evidence-boundary.py
current_source_conformance: PASS
current_release_regression: PASS
historical_evidence_binding: PASS
historical_harness_fake_regression: PASS
两条子回归命令 exit_code=0

LC_ALL=C bash codex/tests/smoke.sh
Ran 890 tests in 97.834s
OK
Codex platform static smoke checks passed.
exit 0

PYTHONPATH=codex/runtime python3 -B -m aisoft_loop.cli check-change-documents --repo /private/tmp/issue-290-scm-test-deploy
PASS: change-documents; PASS: change-pr-url; changes=132 pass=2 gap=0

bash -n codex/tests/smoke.sh
shellcheck codex/tests/smoke.sh
git diff --check
均 exit 0
```

完整 smoke 首次在 sandbox 的既有 fake registry 绑定回环端口时遇到 EPERM；宿主重跑随后
定位到 macOS Bash 在 UTF-8 locale 下把变量后中文标点误解析为变量名。该既有测试未修改，
同一测试在 `LC_ALL=C` 下通过，再用该 locale 重跑未删减完整 smoke 得到上述 PASS。
不以之前失败为 PASS，也没有绕过测试。

## 历史证据与远端 CI

- 旧 head `27fa30d55e35ae2f56072cddef7d9f37d55046d1` 的 required context
  `CI / verify (pull_request)` 曾 FAIL（run/job #1271）：历史 #65 harness 的 runtime gate
  仅接受 transport.py 变更，而 #290 新增 runner.py 修订。该旧结果保留，不代表新 head。
- 用户批准方案 B 后，当前 smoke 以固定历史 fake 回归加当前严格范围/行为验收取代原直接调用。
  原真实 harness 前后 source/authorization 检查完全不变；它在当前 runtime 上仍拒绝执行。
- 旧 #65 immutable evidence SHA-256：
  `b58bb7b57d53a104f922e66c7dc1342bc1b5b133038f60fa8f2ace8d8dbdeb89`，本轮复核一致。
- 当前 runner SHA-256：
  `95092fbd6deab1a536d53371444c9b9c708b538cff3bc1ac4ebbd7dae3bff195`，其余 release runtime
  与固定 baseline 一致。旧 evidence、real/fake harness、fixtures、matrix 均未改动。
- 新 head 推送后的 required CI 尚待回读，不能提前写 READY_FOR_REVIEW。

## 交付边界与回退

- source/local：PASS；FakeDocker/临时 fixtures 测试，不调用真实 Docker。
- current real E2E、installed/runtime byte parity、company live/NewEMaint 测试部署：NOT RUN。
- 未访问公司主机、安装部署、重启服务、修改 UFW、读取 Secret、迁移或恢复实际数据库。
- 唯一 PR #291，policy manual；最终 required CI 通过后由人合并，合并不传递部署授权。
- 撤销 T05 可恢复原 smoke gate 对当前 runner 的拒绝；撤销 runtime commit `b2cc0a3` 可恢复
  原 scm-ci 部署拒绝规则。旧 evidence 不变，源码回退不操作容器、服务或数据库。

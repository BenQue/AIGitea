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

# 允许 scm-ci 测试部署

## 目标

基于现有TargetProfile.environment增加精确例外：scm-ci + test允许测试部署，scm-ci + production仍拒绝。不新增字段/角色，不重新实现部署流程。

## AC

1. scm-ci/test允许stage、migrate、activate、deploy、status、rollback；verify/verify-target维持原行为。
2. scm-ci/production上述动作全部拒绝；未知动作/角色/环境、错误hostname不得被例外放行，拒绝发生在Docker调用或状态写入前。
3. appserver-test/appserver-prod既有行为保持；profile文件保护、制品/兼容性校验、action grant不变。
4. 表驱动矩阵覆盖角色/环境/动作；scm-ci/test使用fake adapter验证部署、重复no-op及失败回滚；production拒绝零Docker事件；既有release tests通过。
5. 文档明确source/local、installed、company live分层，项目需独立Compose项目/目录/数据库/端口，不能覆盖SCM资源。
6. 方案 B：当前 #290 源码验收与历史 #65 evidence 绑定分开验证。旧 evidence/source/plan/version/hash
   与真实执行约束不可改写。当前 runtime 只接受下述固定基线加已批准 runner 六行插入；其它
   runtime 字节、模式、路径未知变化一律 fail closed。当前检查与当前测试属于 required smoke，
   不得仅验证历史副本或给 runner.py 添加宽泛豁免。
7. 当前 Registry/offline fake lifecycle、生产/未知值拒绝、证据漂移负例、full smoke、语义文档及
   diff 检查通过后可交付本次 source 变更。本轮不强制重跑 #65 disposable real E2E，不新增真实
   Docker 兼容性或现场部署证明；当前 real/installed/company-live 保持 NOT RUN。

## 明确授权的修改范围

治理阶段：README.md、docker-release/README.md、本Change语义文档；不修改AGENTS或全局skills。
下一轮runtime阶段：codex/runtime/aisoft_release/runner.py及相关release tests；只按既有environment精确判断，不改schema、不绕过guard。
若发现其它实际运行保护阻塞，先据实际调用链定位，不关闭全局guard或扩大生产权限。

## 方案 B 合同增补（2026-09-11 用户已批准）

用户明确回复“同意方案 B”。本节是独立治理合同步骤 T04；提交后停止，fresh run 重新读取后
执行 T05/T06。既有 push/唯一 manual PR 授权继续有效，不重复确认；人工合并与部署边界不变。

### 固定当前源码范围

- baseline 固定 `64f1cda0de9735f8782e64a5b07af2ce8460e4c3`；该值是 #290 前的已合并源码与
  旧 harness 回归快照，不是 #65 原 real-run source，不把其整个 runtime 归为旧 real evidence。
- 新检查器不接受调用者传 baseline、allowlist、expected hash 或 skip 参数；从固定 Git object
  读取原树，核对当前 index 与磁盘的文件路径、模式和字节，只接受普通文件。
- `codex/runtime/aisoft_release/` 的 12 个文件集合保持；runner.py 精确等于旧文件在唯一
  `roles = allowed.get(action)` 后插入以下六行，其它 11 个文件与 baseline byte-identical，
  包括 transport.py。拒绝新增、删除、改名、symlink、执行位变化、未跟踪及 ignored 文件；
  不用 whitespace-ignore、AST 近似或整文件路径豁免。

```python
    if (
        roles is not None
        and profile.host_role == "scm-ci"
        and profile.environment == "test"
    ):
        roles = roles | {"scm-ci"}
```

| 固定对象 | SHA-256 |
|---|---|
| baseline runner.py | `2d9e9e9db8ec6f3dead2c490f4135473f12b9de80b905bbfb04257703dab9a0e` |
| #290 runner.py | `95092fbd6deab1a536d53371444c9b9c708b538cff3bc1ac4ebbd7dae3bff195` |
| baseline/current transport.py | `26be1c6efa2d05628a613b7134899196e5004e5126e0a5b592f4966857158f21` |
| #65 immutable evidence | `b58bb7b57d53a104f922e66c7dc1342bc1b5b133038f60fa8f2ace8d8dbdeb89` |

- `docker-release/` 保留 README/install.sh 既有非发布语义例外，其余文件集合、模式、字节与
  baseline 一致；matrix 不变，未知新路径拒绝。两个例外仍受文档与 installer 回归约束。
- 旧 real/fake harness、driver、fixtures、其 architecture 输入与 #65 evidence/matrix 与
  baseline 一致；不能跑历史副本却忽略这些文件在当前树中的漂移。
- 当前范围检查在历史子进程/当前行为测试前后执行，检测运行期间漂移。smoke 入口禁止写 Python
  bytecode；验收使用 `python3 -B`。额外 .pyc 同样拒绝，不自动清理或设置缓存豁免。

### 分开验证历史与当前

检查器只从当前已验证仓库的本地 Git object 创建 task-local temporary clone，detached checkout
固定 baseline；不 fetch、不用网络/凭据、不新增工作分支或 worktree，不复制当前改动进历史树。
只在快照运行原 `codex/tests/test-docker-release-v2-lifecycle-e2e-harness.sh`，使用其 task-local
fake docker。输出为 `historical_harness_fake_regression`，结束只清理该临时 clone。

#65 immutable evidence 的 source/tree/runtime/approval-plan/fixture/version/cleanup identity
保持原字节，不重写日期/hash，也不在其目录生成新 PASS evidence。旧真实 harness 的 source SHA、
delivery base、authorization marker、execute 与前后检查全不变；它在当前 #290 runtime 上仍拒绝。

当前 checkout 继续执行 full Python suite，并补充 scm-ci/test 的 offline-bundle 部署、重复
no-op、失败回滚，覆盖 Registry 与离线路径。原角色矩阵、生产/未知值零副作用及其它安全验证保持。
CI 记录本次实际 current SHA/tree、runner hash、baseline、历史 evidence hash、命令和退出码，
分别输出 current_source_conformance、current_release_regression、historical_evidence_binding；
current_real_e2e、installed、company_live 明确 NOT RUN。任何一部分失败，整体非零退出。

### T05/T06 精确授权文件

- `codex/tests/check-release-evidence-boundary.py`：新增专用固定范围检查与历史 clone 的 fake 回归
  编排，不设计通用豁免平台。
- `codex/runtime/tests/test_release_evidence_boundary.py`：新增小型 task-local Git fixtures 正反例；
  不从测试递归调用完整回归。
- `codex/tests/smoke.sh`：替换原历史 fake harness 调用为新检查器，并在入口禁止写 bytecode；
  保留其它硬门、full Python suite、原 real harness 默认 NOT RUN 检查，不改 workflow/context。
- `codex/runtime/tests/test_release_runner.py`：补充 scm-ci/test offline-bundle 生命周期覆盖。
- `docker-release/README.md` 与本 Change 的 summary/verification：同步真实分层结果。

不继续修改 runner.py、其它 release runtime、旧 #65 文档/evidence、旧 real/fake harness、
driver/fixture、compatibility matrix、AGENTS、provider/global skills、workflow 或现场配置。
若要宣称真实 scm-ci/test 共置验收，仍须项目单独授权的现场或 disposable 部署/重复/失败回滚回执；
本 source 验收不能替代。扩 Docker/transport/migration 等语义或兼容范围不在此增补内。

### 回退

撤销新增检查器、smoke 调用与本增补的独立提交即可恢复旧 gate 在当前树上拒绝 runner 变化的行为；
旧 evidence 全程不变。源码回退不触发服务、容器或数据库操作。

## 非目标

无现场执行、安装、Secret操作、数据库迁移/恢复、服务重启、生产部署；不修改现有SCM服务资源。
允许工具路径不等于授权执行migrate；现场仍按项目批准的固定操作实施。

---
issue: 223
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/223
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
reason: 给共享治理工具 aisoft-project-check.sh 增加两条平台级只读检查并新增 CI workflow 参考模板，同时改动平台仓自身的 required CI 运行方式，属于 CI 与平台治理变更
risk_flags:
  - ci-change
  - shared-core
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-ci-merge-preview-gate-260905.md
  spec: spec-ci-merge-preview-gate-260905.md
  plan: plan-ci-merge-preview-gate-260905.md
  verification: verification-ci-merge-preview-gate-260905.md
confidence: high
override_reason: ''
depends_on: []
status: approved
branch: change/223-ci-merge-preview-gate
pr_url:
created: 2026-09-05
updated: 2026-09-05
---

## 问题/需求总结

`pull_request` 事件上的 CI 跑的是 PR 分支自己的 head，不是 head 与 base 的合并结果。
两个 PR 各自诚实地绿，合并后主干红——2026-08-29 在 LocalWMS 上真实发生过一次
（`actual: 76, expected: 75`，阻塞了所有后续 PR）。

Issue 评论订正了立案时的前提：**只堵这一个缺口不够**。即使 CI 跑的是合并预览，那次预览
也是在 T1 算的，而合并发生在 T3；T2 别人合并进 base 之后没有任何东西让它重跑，
`block_on_outdated_branch: false` 让那个过期的绿仍然可以合并。两个缺口必须一起处理。

平台已于 2026-09-05 在 Issue 上裁定：

- 缺口①走路径 2——`codex/tools/aisoft-project-check.sh` 增加只读检查，
  `templates/project/` 增补 CI workflow 参考；平台不代改项目仓文件。
- 缺口②——`aisoft-platform` 与 `gitea-governance.json` 里 `classification=internal-application`
  的全部仓库打开 `block_on_outdated_branch`。broker 没有 `protection.set`，开关由人在 Gitea
  界面操作；本会话负责加上对应的只读检查，并在 `06` 记录串行化代价。

## 影响范围

- `codex/tools/aisoft-project-check.sh`：新增两条检查项。共享治理工具，所有接入项目都会读到新结论。
- `codex/tests/test-project-check.sh`、`codex/tests/smoke.sh`：新增检查项的正反用例与静态闸门。
- `templates/project/ci/`：新增 CI workflow 与合并预览脚本参考。新目录。
- `.gitea/workflows/ci.yml`：平台仓自身的 required CI 运行方式（见 spec 的显式授权）。
- `06-运维手册与踩坑集.md`：记录并行 PR 串行化的代价与处置。
- 7 个仓库的 `main` 分支保护需要人在 Gitea 界面打开 `block_on_outdated_branch`；
  本次变更**不做**这一项，只把它写成交接项并让检查器能读回。

## 初步方案与建议

检查器识别的是**机制**而不是某一种写法。2026-09-05 的取证发现 LocalWMS 已经把缺口①修完
（Issue #193 已 closed），而它**刻意避开** `refs/pull/N/merge`——该 ref 由 Gitea 后台在计算
可合并性时刷新，新鲜度不由本次 CI 运行决定，检出它可能得到一个对着旧 base 的合并结果，
恰好就是要消灭的静默假绿。LocalWMS 改成在运行那一刻现取 base 尖端、现场做三方合并，
合不上就明确报错退出。

因此检查器接受两种形态，任一满足即 PASS；只认 `ref:` 一种写法会把唯一一个真正修对了的
仓库判成 GAP。

## 风险

- 检查器判据过窄会产生假 GAP，把已经修对的仓库判错——用 LocalWMS 合并后的真实 ci.yml
  做 fixture 直接压住。
- 改平台仓自身的 required CI 有自伤风险：合并预览步骤若在本平台 runner 上跑不通，
  本 PR 自己会红。缓解是它只在本 PR 的分支上生效，红了就回退这一处 hunk，
  检查器与模板照常落地。
- 打开 `block_on_outdated_branch` 会把并行 PR 串行化，本轮同时有 3 条 PR 在跑，代价是真实的。
  该开关不在本次变更内，由人操作。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
reason: 给共享治理工具 aisoft-project-check.sh 增加两条平台级只读检查并新增 CI workflow 参考模板，同时改动平台仓自身的 required CI 运行方式，属于 CI 与平台治理变更
risk_flags:
  - ci-change
  - shared-core
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
```

### 判级证据

- `change_type: platform` 属于 `FORCED_COMPLEX_TYPES`，`codex/runtime/aisoft_loop/classification.py:53`。
- `risk_flags` 的 `ci-change`、`shared-core`、`platform-governance` 三项都在 `FORCED_COMPLEX_RISKS` 内，同文件 55-74 行。
- `contract_effect: add`：检查器新增 GAP 条件，等于给所有接入项目加了一条新的平台合同要求。
- 声明 `verification` 的依据是 `03` §3 的证据来源判据：`block_on_outdated_branch` 的改动前基线、
  跨 8 个仓库的 broker 回读、本 PR 上合并预览的一次性运行观测，required CI 都不重放。

### 缺失的 acceptance criteria 或决策

- 无。Issue 正文、订正评论与 2026-09-05 平台裁定合起来已给出完整合同；
  平台仓自身 `.gitea/workflows/ci.yml` 是否同改由本 change 的 spec 显式授权。

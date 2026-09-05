---
issue: 227
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/227
change_type: bugfix
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
reason: 恢复 CI 硬门脚本在对端缺席时有界失败的既有意图，但改动落在 required CI 的 smoke 套件内，命中 ci-change 强制复杂规则
risk_flags:
  - ci-change
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-bootstrap-test-bounded-wait-260905.md
  spec: spec-bootstrap-test-bounded-wait-260905.md
  plan: plan-bootstrap-test-bounded-wait-260905.md
  verification: verification-bootstrap-test-bounded-wait-260905.md
confidence: high
override_reason: ''
depends_on: []
status: pr-open
branch: change/227-bootstrap-test-bounded-wait
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/255
created: 2026-09-05
updated: 2026-09-05
---

## 问题/需求总结

2026-08-29，`admin/aisoft-platform` 的 CI task 821 在
`codex/tests/test-bootstrap-gitea-service-account.sh` 上永久挂起 4h19m，内核栈为
`wait_for_partner → fifo_open`。gitea-ci 是实例级 runner 且 `maxParallel=1`，队头一挂
导致全平台 CI 停摆约 5 小时，LocalWMS 的 PR 197 与 198 的必需检查零进展。

本次要解决的是：该脚本存在**无界等待点**，在对端不出现时会无限期阻塞而不是有界失败。

## 影响范围

- `codex/tests/test-bootstrap-gitea-service-account.sh`：required CI `CI / verify` 经
  `codex/tests/smoke.sh` 调用的测试脚本。
- 不改 `codex/tools/bootstrap-gitea-service-account.sh`，不改 `smoke.sh`，不改 `.gitea/workflows/ci.yml`。
- runner 级 per-job timeout 与停滞检测属于另一条 Issue，不在本次范围。

## 初步方案与建议

1. 消除 mock `curl` 的 glob fall-through：按精确 endpoint 分派，未知 URL 立即 fail closed。
2. 需要读取 Authorization 头的分支改为有界读取，缺少对端时打印可搜索标记并退出。
3. 为整脚本加一层有界看门狗兜底，超时打印可搜索标记并终止自身与后代进程。
4. 盘点并记录脚本内其余等待点。

## 风险

- 改的是 required CI 硬门内的脚本，回归会阻塞全平台 PR。缓解：只改测试脚本，
  保持既有断言不变，本地与容器内多次重跑。
- 看门狗本身引入后台进程，设计不当会制造新的不稳定。缓解：默认不参与断言路径，
  以自检用例证明它按预期触发且不误触发。

## AI 判级

```yaml
change_type: bugfix
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
reason: 恢复 CI 硬门脚本在对端缺席时有界失败的既有意图，但改动落在 required CI 的 smoke 套件内，命中 ci-change 强制复杂规则
risk_flags:
  - ci-change
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
```

### 判级证据

- `contract_effect=restore`：脚本的外部行为契约不变，恢复的是「失败要有界」的既有意图；
  不新增功能，不改被测工具的接口。
- 强制复杂：改动对象由 `.gitea/workflows/ci.yml` 的 `Platform smoke suite` 步骤经
  `codex/tests/smoke.sh:193` 直接执行，属于 required 检查 `CI / verify` 的组成部分，
  命中 `classification.py` 的 `FORCED_COMPLEX_RISKS` 中的 `ci-change`。
- 需要 `verification`：验收证据含只能在 Linux 容器内一次性观测的内核栈实验与多次重跑，
  required CI 与 diff review 无法复现，落在 `03` §3 判据表第二行。

### 缺失的 acceptance criteria 或决策

- 无。Issue 正文已给出五条可测验收标准，本次逐条承接。

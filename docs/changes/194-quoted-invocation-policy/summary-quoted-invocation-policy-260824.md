---
issue: 194
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/194
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
reason: _skill_front_matter 相邻两行对引号给出两套取值规则，引号包裹的 disable-model-invocation 被判成非法值并让整个 snapshot fail-closed；修法是在该函数内统一成一个取值点，改动落在 aisoft_loop 治理运行时这一共享核心且该函数是 vendored skill 的完整性闸门，属平台治理变更，强制 complex
risk_flags:
  - platform-governance
  - shared-core
required_docs:
  - summary
  - spec
  - plan
documents:
  summary: summary-quoted-invocation-policy-260824.md
  spec: spec-quoted-invocation-policy-260824.md
  plan: plan-quoted-invocation-policy-260824.md
confidence: high
override_reason: ''
depends_on: []
status: approved
branch: change/194-quoted-invocation-policy
pr_url:
created: 2026-08-24
updated: 2026-08-24
---

## 问题/需求总结

`matt_snapshot._skill_front_matter` 相邻两行对引号的态度不一致：

```python
name = line.split(":", 1)[1].strip().strip("'\"")   # 剥引号
value = line.split(":", 1)[1].strip().lower()       # 不剥引号
```

于是合法 YAML `disable-model-invocation: 'true'` 落到 `{"true", "false"}` 之外，整个
snapshot 以 `invalid invocation policy` 失败；错误文本指向「这个 skill 的策略值不对」，
不指向真正的原因「这个取值点不认引号」。

复现时还发现分歧的另一半：`name: 'demo-skill`（未闭合引号）被 `.strip("'\"")`
**静默修复**成 `demo-skill` 并通过下游正则。也就是说 `name` 一行不只是「更宽松」，
而是在一个 fail-closed 完整性闸门里静默修复了畸形 YAML。

## 影响范围

- `codex/runtime/aisoft_loop/matt_snapshot.py` 的 `_skill_front_matter`：唯一的缺陷
  位置，取 `name` 与 `disable-model-invocation` 的两行。
- 经它转发的 `build_manifest` / `verify_snapshot`，以及三个调用方
  `codex/install-skills.sh`（两处）与 `codex/tests/smoke.sh`——都只是调用方，不需要
  各自改。
- `codex/runtime/tests/test_matt_snapshot.py`：新增覆盖。

不影响 `codex/vendor/mattpocock/v1.2.2/` 快照内容、不影响 manifest、不影响
`classify_update` 的判据。

## 初步方案与建议

在 `_skill_front_matter` 内部收敛成**一个**取值点：一个私有 helper 负责「一行 front
matter 的值是什么」，两行都经过它。引号规则采用成对剥离（与
`contract._safe_scalar` 同形），未闭合/不配对的引号 fail-closed 而不是静默修复。

不引入 `contract` 依赖——理由见 spec §2：`matt_snapshot` 是全包唯一零 intra-package
import 的模块，且它治理的是上游第三方内容，不该被平台自撰文档的 YAML 方言约束。

## 风险

- 误伤 `name` 一行的既有行为：约束是「引号与裸写都接受」逐字节不变，只有畸形引号
  从静默修复转为 fail-closed。这是一次有意的收紧，spec §4 与 PR 正文都显式声明。
- 误伤现存快照：`codex/vendor/mattpocock/v1.2.2/` 下 20+ 个 `disable-model-invocation`
  与全部 `name` 都是裸写，由 smoke.sh 里既有的 `matt_snapshot verify` 真实快照校验钉死。
- 回滚为单 commit `git revert`，无迁移、无状态残留。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
reason: _skill_front_matter 相邻两行对引号给出两套取值规则，引号包裹的 disable-model-invocation 被判成非法值并让整个 snapshot fail-closed；修法是在该函数内统一成一个取值点，改动落在 aisoft_loop 治理运行时这一共享核心且该函数是 vendored skill 的完整性闸门，属平台治理变更，强制 complex
risk_flags:
  - platform-governance
  - shared-core
required_docs:
  - summary
  - spec
  - plan
confidence: high
override_reason: ''
```

### 判级证据

- `contract_effect: restore`：修复既有缺陷，恢复 `_skill_front_matter` 本就声明的合同
  （合法 YAML 的策略值被正确解析），不新增也不改变任何外部行为。
- 但 `contract_effect` 只决定 small **候选**资格。触点是
  `codex/runtime/aisoft_loop/`——Loop、Controller 与全部治理 CLI 共用的运行时共享核心；
  且 `_skill_front_matter` 产出的 `disable_model_invocation` 是 vendored Matt skills 的
  完整性 manifest 字段，`codex/install-skills.sh` 在**第一次文件系统写入之前**用它做闸门。
  属 Agent 与平台治理变更，按 `AGENTS.md` 强制 complex 规则一律按 complex 处理。
  与 #186 / #189 同源同判。
- 缺陷可稳定复现：在 merged main `eda2aeb` 上，`disable-model-invocation: 'true'` 与
  `"false"` 均抛 `SnapshotError: invalid invocation policy`，而同文件的
  `name: 'demo-skill'` 正常解析。
- `required_docs` 不含 `verification`：验收证据全部由 diff review 与 required CI
  （`bash codex/tests/smoke.sh` 内的 unittest 与真实快照校验）复现，无部署与迁移影响。

### 缺失的 acceptance criteria 或决策

- 无。Issue #194 正文已给出 AC-1..AC-5 与范围外项；正文点名要 spec 决定的修法选择由
  spec §2 作答。

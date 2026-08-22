---
issue: 142
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/142
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - agent-governance
  - platform-governance
depends_on: []
status: pr-open
branch: change/142-loop-pr-url-backfill
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/144
created: 2026-08-22
updated: 2026-08-22
reason: 新增交付链路上共享工具的子命令与确定性检查，并改动 change 文档 front matter 合同，属 Agent/治理类别，强制 complex
required_docs:
  - summary
  - spec
  - plan
  - verification
override_reason: ''
documents:
  summary: summary-loop-pr-url-backfill-260822.md
  spec: spec-loop-pr-url-backfill-260822.md
  plan: plan-loop-pr-url-backfill-260822.md
  verification: verification-loop-pr-url-backfill-260822.md
---

## 问题/需求总结

`pr_url` 是 change 文档 front matter 里唯一一个建文档时无法确定的字段——它要等 PR 真的建出来。平台从未有任何代码往它里面写过值：全仓库唯一的非测试引用是 `analysis.py:144` 渲染 summary 骨架时写下的**空键**。回填因此是一次纯手工的 commit + push，靠人记得；漏做完全静默。

同根因的相邻缺陷：`resolve-documents` 对每份映射文档调用 `parse_front_matter`，因此任何一份 spec/plan/verification 缺 front matter 都会让解析整体抛错——而平台合同要求「解析用 `resolve-documents`，不要 glob 猜」。这条要求没有任何闸门保障，坏掉的变更能一路合并进 `main`。

两者合起来是同一句话：**change 文档的 front matter 契约只有约定、没有闸门。**

## 影响范围

- `codex/runtime/aisoft_loop/`：新增 `pr_url` 回填与 change 文档巡检两条能力，以及 `contract.py` 的一个公开访问器；
- `codex/tools/aisoft-project-check.sh`：新增两个 PASS/GAP 检查项；
- `codex/tests/smoke.sh`：把巡检作用在平台仓自身；
- `templates/docs/changes/_template/`：spec/plan/verification 三份去掉 `pr_url`；
- `03-Issue-Spec-Plan与单闸门开发流程.md` 与 `skill-for-claude/SKILL.md`、`skill-for-codex/SKILL.md`：同步 front matter 合同与流程步骤。

不改语义命名合同，不追溯修补已合并的历史文档，不引入新的运行时依赖。

## 初步方案与建议

1. **裁决 `pr_url` 只写在 summary**，并据此修改模板与书面合同（论证见 spec §2）；
2. 新增 `aisoft-loop backfill-pr-url N --repo <checkout> --pr-url <url>`，与 `publish-spec`/`publish-plan` 同构：只写文件、幂等、冲突 fail-closed；
3. 新增 `aisoft-loop check-change-documents --repo <checkout>`，对仓库里每个 change 目录断言 `resolve-documents` 成功，并断言处于「PR 必然已存在」生命周期的 summary 不留空 `pr_url`；
4. 把 3 接进 `aisoft-project-check.sh`（目标仓）与 `smoke.sh`（平台仓自身）。

## 风险

- 模板改动会让所有已接入仓的 `change-templates` 检查转 GAP，直到各仓自行同步——这是既有漂移检测器的正常工作方式，代价与处置写在 spec §6；
- 巡检加进 `smoke.sh` 后，平台仓自身任何一个历史 change 目录解析失败都会让 smoke 变红。这是想要的效果，但需要在合并前确认当前 `main` 是干净的（verification 记录实测）。

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
```

强制规则命中：改动交付链路上的共享工具与 Agent/平台治理合同（front matter 契约、模板、skill 流程步骤）。→ 需 summary + spec + plan + verification。

## 证据

- `codex/runtime/aisoft_loop/analysis.py:144` 写下空 `pr_url:` 键，13 个子命令无一回填；
- `codex/runtime/aisoft_loop/contract.py:411` 对每份映射文档解析 front matter，是 §2 缺陷的直接成因；
- `codex/runtime/aisoft_loop/contract.py:474` 的 `_validate_complex_document_front_matter` 只读 `issue`/`branch`/`effective_complexity`，`_resolve_documents` 只额外读 `created`——**非 summary 文档里的 `pr_url` 没有任何代码消费者**；
- Issue #142 正文与其后补的评论记录了 `admin/LocalWMS` 九个 change 目录的三种 front matter 形状，以及最近四个变更一致收敛到「只有 summary 带 `pr_url`」。

## 缺失验收标准

- 无；Issue 正文的验收标准逐条可测，spec §7 给出映射。

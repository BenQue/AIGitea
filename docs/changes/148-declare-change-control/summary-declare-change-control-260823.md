---
issue: 148
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/148
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - platform-governance
depends_on:
  - 134
status: pr-open
branch: change/148-declare-change-control
pr_url: ''
created: 2026-08-23
updated: 2026-08-23
reason: 改动 gitea-governance.json 的仓库条目并改变该仓库的判级输出，属平台治理类别，强制 complex
required_docs:
  - summary
  - spec
  - plan
  - verification
override_reason: ''
documents:
  summary: summary-declare-change-control-260823.md
  spec: spec-declare-change-control-260823.md
  plan: plan-declare-change-control-260823.md
  verification: verification-declare-change-control-260823.md
---

## 问题/需求总结

Issue #134 实现了 `change_control`（`aisoft_loop/change_control.py` + `classification.route()`，
测试齐全，PR #135 已合并，Issue 已 `completed`）。但 `codex/config/gitea-governance.json` 里
**十个仓库无一声明该字段**，全部走 `resolve_change_control()` 的兜底值 `production`。

机制造好了，配置那一步从来没做。**#134 的收益至今为零。**

这不是新发现——`docs/changes/136-broker-force-with-lease/` 与
`docs/changes/139-push-lease-doc-sync/` 的 summary 都顺带记过一笔「`aisoft-platform` 未声明
`change_control`」。被注意到至少两次，但没有任何一次变成配置动作。

## 代价：来自 LocalWMS 的实测

LocalWMS 尚未做过任何生产部署（部署属其路线图 M3），却一直按 `production` 付四份文档的成本。
截至 `admin/LocalWMS` main = `eac50d1`（14 个已合并 PR，2026-08-18 → 08-23）：

| 类别 | 行数 |
|---|---|
| 生产代码 `src/` + `packages/` | 3054 |
| 测试与闸门 `test/` + `scripts/` + CI | 4750 |
| 合同制品 `docs/contracts/` | 493 |
| **变更流程文档 `docs/changes/`** | **8376** |

流程文档是生产代码的 **2.7 倍**；14 个 PR 里 5 个零代码改动。最极端的一例是 PR #32
（合同缺省值澄清）：实质 8 行 YAML，配 651 行变更文档，其中 `spec` 227 行、`plan` 130 行——
**80 : 1**。

## 结论要点

本次只做一件事：**给 LocalWMS 声明 `change_control: "development"`**。

其效果由 `classification.py:route()` 决定——强制 complex 的 `required_docs` 由
`summary + spec + plan + verification` 降为 `summary + verification`。判级本身、生命周期标签、
`verification` 的条件都不变（#134 的 AC6 已经把这几条钉住，本次一字未动）。

### 两条测试挡在路上，都是「把当时的快照写成了断言」

| 测试 | 原断言 | 问题 | 改法 |
|---|---|---|---|
| `test_every_shipped_repository_defaults_to_production` | manifest 里**每个**仓库都是 `production` | 把「当时无人声明」写死了 | 改为只遍历**未声明**的仓库，并加一条防空转断言 |
| `test_declared_development_is_parsed` | 声明一个仓后，**其余都是** `production` | 同上 | 改为逐仓比对各自在 manifest 里的声明值 |

两条的**意图**都保留了（AC2 的兜底语义、声明不污染其它仓），只是不再依赖「所有仓都未声明」
这个正在被本 Issue 改变的事实。详见 [spec](spec-declare-change-control-260823.md) §3。

## 变更范围

| 文件 | 变更 |
|---|---|
| `codex/config/gitea-governance.json` | LocalWMS 条目新增 `"change_control": "development"`（1 行） |
| `codex/runtime/tests/test_change_control.py` | 上表两条测试改写；新增一条钉住 LocalWMS 已降档 |

`change_control` 的**机制本身一字未改**：`change_control.py`、`classification.py`、
`contract.py`、`controller.py` 全部未触碰。

## 合并之后还有一步，不能省

`resolve_change_control()` 默认读的是 **`/usr/local/share/aisoft/gitea-governance.json`**
（root:wheel，由 `codex/install-host-access-broker.sh` 安装），不是仓内文件。
**合并 PR 不等于生效**——必须重装一次 manifest。该步骤需要 root，Agent 无法执行。
见 [verification](verification-declare-change-control-260823.md) §4。

## 其余九个仓库

本次**不声明**，理由不是遗漏而是两条实质考虑，见 [spec](spec-declare-change-control-260823.md) §4：
显式写 `production` 不改变任何行为，且会让 AC2 的兜底断言失去可遍历的样本。
九个仓库的逐条裁决记录同样写在 spec §4。

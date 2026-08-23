---
issue: 148
branch: change/148-declare-change-control
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/149
status: pr-open
created: 2026-08-23
updated: 2026-08-23
---

# Spec · 为 manifest 里的项目声明 change_control

| 项目 | 值 |
|---|---|
| Issue | [#148](http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/148) |
| 分支 | `change/148-declare-change-control` |
| 判级 | complex · `contract_effect: change` |
| 依赖 | [#134](http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/134)（机制，PR #135 已合并） |
| 基线 | `origin/main` = `e03d912` |
| 日期 | 2026-08-23 |

## 1. 问题：造好的开关从没打开过

`resolve_change_control()` 的实现是对的，兜底也是对的：

```python
phase = entry.get("change_control", PRODUCTION)
return phase if phase in PHASES else PRODUCTION
```

「读不到 manifest、查不到仓库、或取值非法时一律回落 production」——缺省取更严的一档，
这条设计不动。但它有一个未被预期的后果：**「从没有人声明过」和「声明为 production」在系统里
长得一模一样**，因此没有任何东西会提醒「这个仓其实可以降档」。

十个仓库全部落在兜底值上。#134 的 `required_docs` 分级能力自 2026-08-21 合并以来一直是死代码。

## 2. 范围：只降 LocalWMS

```json
{
  "name": "LocalWMS",
  "classification": "internal-application",
  "change_control": "development",
  ...
}
```

依据：LocalWMS 从未做过任何生产部署，其路线图把平台完整接入排在 M3，部署本身还没开始。
`development` 的定义（#134）正是「尚未首次生产部署的项目」。

生效路径全部是既有代码，本次没有新逻辑：

```
gitea-governance.json
  └─ resolve_change_control("LocalWMS") → "development"
       └─ Classification.route(change_control="development")
            └─ required_docs: (summary, spec, plan, verification) → (summary, verification)
```

`classification.py:190-200` 的分支早就写好了，包括「`verification` 的条件不随阶段改变」
这条——因为 `required_docs` 含 `verification` 同时承载着「该变更要部署、终态是 `deployed`
而非 `completed`」的既有语义（`mark-completed-issues.sh`）。本次一字未改。

## 3. 两条挡路的测试：把快照写成了断言

改 manifest 会让 `tests/test_change_control.py` 的两条断言变红。**它们不是缺陷发现，
是断言写得比意图更具体**——把「当时没有任何仓库声明过」这个偶然事实固化了。

### 3.1 `test_every_shipped_repository_defaults_to_production`

原文遍历**全部**仓库断言 `production`。AC2 的意图是「未声明的既有仓库必须默认 production，
行为逐字段不变」——主语是**未声明的**仓库。改为：

```python
declared = {e["name"] for e in raw["repositories"] if "change_control" in e}
...
for repository in contract.repositories:
    if repository.name in declared:
        continue
    ...
self.assertGreater(checked, 0, "没有未声明的仓库，AC2 的兜底断言已空转")
```

最后那条防空转断言是新增的，针对一个真实的将来风险：等所有仓库都显式声明的那天，
上面的循环会一个都不跑而测试仍然「通过」，兜底行为就没有任何东西守着了。
到那时必须补一个合成 fixture——断言会明说这一点，而不是静默地绿。

### 3.2 `test_declared_development_is_parsed`

原文把 `repositories[1]` 设为 `development` 后，断言**其余全部**是 `production`。
真正要证的是「声明一个仓不会污染其它仓」。改为逐仓比对各自在 manifest 里的声明值：

```python
expected = {e["name"]: e.get("change_control", "production") for e in raw["repositories"]}
...
self.assertEqual(other.change_control, expected[other.name])
```

意图不变，且不再依赖任何一份特定的 manifest 快照。

### 3.3 新增一条钉住新事实

`test_localwms_is_declared_development`：LocalWMS 一旦被改回去，判级会**静默**恢复四份文档——
没有任何现有断言会发现。这条补上那个缺口。

## 4. 为什么其余九个仓库不在本次声明

这是一条显式裁决，不是遗漏。两条实质理由：

1. **显式写 `production` 不改变任何行为。** 它们当前就解析为 `production`，写下来只是把
   兜底值抄进 manifest，多九行 JSON 而系统行为完全相同。
2. **会让 §3.1 的兜底断言失去可遍历的样本。** AC2 的守护依赖「存在未声明的仓库」；
   把十个仓全部声明掉，那条断言当场空转（新加的 `assertGreater` 会让它红，届时必须改成
   合成 fixture——为了记录九个不变的值而付这个代价并不划算）。

九个仓库的逐条裁决：

| 仓库 | 本次裁决 | 理由 |
|---|---|---|
| `aisoft-platform` | 保持 `production`（未声明） | 平台自身即生产系统，broker/manifest 已安装在主机上 |
| `NewEMaint` | 保持 `production`（未声明） | 有 VM profile 与 `aisoft-agent@emaintenance.timer`，且是 docker-release/v2 的参照实现；部署状态需其项目会话确认 |
| `SFMDigitalBoard` | 保持 `production`（未声明） | 有 VM profile 与 `aisoft-agent@sfm.timer` |
| `rsdesign-new` | 保持 `production`（未声明） | 有 VM profile |
| `HSDB` | 保持 `production`（未声明） | 部署状态未确认 |
| `WMPDA` | 保持 `production`（未声明） | 部署状态未确认 |
| `SapTableMigrate` | 保持 `production`（未声明） | 部署状态未确认 |
| `myapp` | 保持 `production`（未声明） | 部署状态未确认 |
| `smoke-test` | 保持 `production`（未声明） | 平台冒烟仓，几乎不产生变更文档，降档收益为零 |

**部署状态是项目事实，不是本 Issue 能从 manifest 推断出来的。** 凡未确认者取更严一档——
这与 `resolve_change_control()` 的兜底原则一致。任一项目认为自己该降档时，改一行即可，
成本极低。

## 5. 明确不做

- **不改 `change_control` 的机制**：`change_control.py`、`classification.py`、`contract.py`、
  `controller.py` 全部未触碰。#134 的实现是对的，缺的只是配置。
- **不动默认值**：未声明仍回落 `production`。
- **不砍任何自动闸门**。drift gate、case gate、error-code registry、audit gate 与本 Issue 无关。
  它们是一次性投入换持续自动检查；随变更数线性增长的是**手抄的散文**，不是机器检查。
- **不改 `verification` 的条件**：它承载「该变更要部署」的既有语义，#134 的 AC6 已钉住。
- **不代替其它项目裁决部署状态**（§4）。

## 6. 验收标准

- [ ] `gitea-governance.json` 中 `LocalWMS` 声明 `change_control: "development"`；
- [ ] `load_contract(MANIFEST)` 解析出的 LocalWMS 为 `development` 且 `in_development` 为真；
- [ ] 未声明的九个仓库仍解析为 `production`，且 AC2 断言仍有可遍历的样本（不空转）；
- [ ] `Classification.route(change_control="development")` 的 `required_docs` 为
      `(summary, verification)`——既有断言，不得改动；
- [ ] `bash codex/tests/smoke.sh` 全绿；
- [ ] 机制文件（`change_control.py`/`classification.py`/`contract.py`/`controller.py`）零改动；
- [ ] 文档写明：合并后仍须重装 manifest 才生效，且该步骤需要 root。

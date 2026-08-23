---
issue: 148
branch: change/148-declare-change-control
pr_url: ''
status: pr-open
created: 2026-08-23
updated: 2026-08-23
---

# Verification · 为 manifest 里的项目声明 change_control

- Issue：[#148](http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/148)
- 分支：`change/148-declare-change-control`，基线 `origin/main` = `e03d912`
- 环境：macOS + Python 3.14
- 日期：2026-08-23

## 1. 前提核对：机制在，配置没做（plan T01）

`resolve_change_control()` 与 `Classification.route(change_control=...)` 均存在且有测试
（`tests/test_change_control.py` 14 条）。改动前的十仓状态：

```
aisoft-platform        (未声明→production)
HSDB                   (未声明→production)
LocalWMS               (未声明→production)
myapp                  (未声明→production)
NewEMaint              (未声明→production)
rsdesign-new           (未声明→production)
SapTableMigrate        (未声明→production)
SFMDigitalBoard        (未声明→production)
smoke-test             (未声明→production)
WMPDA                  (未声明→production)
```

十个全部未声明，Issue 的前提成立。

## 2. 改动后

```
aisoft-platform        (未声明→production)
HSDB                   (未声明→production)
LocalWMS               development
myapp                  (未声明→production)
NewEMaint              (未声明→production)
rsdesign-new           (未声明→production)
SapTableMigrate        (未声明→production)
SFMDigitalBoard        (未声明→production)
smoke-test             (未声明→production)
WMPDA                  (未声明→production)
```

`gitea-governance.json` 的 diff 是**一行**——用文本插入而非 `json.dump` 重写，
避免把一行改动变成全文件格式 diff。

## 3. 两条测试：先看着它红，再修（plan T03）

改完 manifest 后先跑一次，确认它们确实钉住了正在改变的事实：

```
FAIL: test_declared_development_is_parsed
  self.assertEqual(other.change_control, "production")
AssertionError: 'development' != 'production'
```

`test_every_shipped_repository_defaults_to_production` 同样因 LocalWMS 而红。
两条都属「断言写得比意图更具体」——把「当时无人声明」这个偶然事实固化了，
不是发现了缺陷。按 spec §3 改写后：

```
$ PYTHONPATH=. python3 -m unittest tests.test_change_control
..............
Ran 14 tests in 0.006s
OK
```

其中新增的防空转断言 `assertGreater(checked, 0, "没有未声明的仓库，AC2 的兜底断言已空转")`
针对一个真实的将来风险：等所有仓库都显式声明的那天，AC2 的循环会一个都不跑而测试仍然绿。

既有的行为断言**一条未改**，仍然通过：`test_development_keeps_only_summary_and_verification`
（`required_docs == ("summary", "verification")`）、`test_production_keeps_four_documents`、
`test_verification_stays_conditional_in_development`、
`test_phase_does_not_change_complexity_or_lifecycle`。

## 4. 全量 smoke（plan T04）

CI 的唯一入口就是这一条：

```
$ bash codex/tests/smoke.sh
...
Ran 507 tests in 28.764s
OK
Codex platform static smoke checks passed.
exit=0
```

## 5. 合并之后还有一步，Agent 做不了

`resolve_change_control()` 默认读的是 **`/usr/local/share/aisoft/gitea-governance.json`**：

```python
DEFAULT_MANIFEST = Path("/usr/local/share/aisoft/gitea-governance.json")
```

该文件属 `root:wheel`，由 `codex/install-host-access-broker.sh:50-51` 安装。
**合并 PR 不会更新它。** 在重装之前，Loop 与 Claude 会话读到的仍是旧 manifest，
LocalWMS 仍按 `production` 判级——四份文档照旧。

```bash
sudo bash codex/install-host-access-broker.sh
```

这一步需要 root，Agent 无法执行。**验收的最后一环在人手里。** 重装后可验证：

```bash
python3 -c "
import sys; sys.path.insert(0, 'codex/runtime')
from aisoft_loop.change_control import resolve_change_control
print(resolve_change_control('LocalWMS'))
"   # 期望 development
```

（不传 `manifest` 参数时它读的就是已安装的那份，因此这条命令能真正区分「改了仓」与「装上了」。）

## 6. 变更范围

```
 codex/config/gitea-governance.json           |  1 +
 codex/runtime/tests/test_change_control.py   | 修改 2 条 + 新增 1 条
 docs/changes/148-declare-change-control/     | 四份文档
```

`change_control` 的机制文件**零改动**：`aisoft_loop/change_control.py`、
`aisoft_loop/classification.py`、`aisoft_gitea_governance/contract.py`、
`aisoft_loop/controller.py` 全部未触碰。

## 7. 验收标准逐条

- [x] `gitea-governance.json` 中 LocalWMS 声明 `change_control: "development"`；
- [x] 解析结果为 `development` 且 `in_development` 为真（`test_localwms_is_declared_development`）；
- [x] 未声明的九个仓仍解析为 `production`，且 AC2 断言仍有样本可遍历（`assertGreater`）；
- [x] `route(change_control="development")` 的 `required_docs` 为 `(summary, verification)`——既有断言未改动；
- [x] `bash codex/tests/smoke.sh` 全绿，507 条；
- [x] 机制文件零改动；
- [x] 文档写明合并后仍须重装 manifest，且该步骤需要 root（§5）。

## 8. 本次不做、已记录的事

其余九个仓库保持未声明，逐条裁决记录见 spec §4。部署状态是项目事实，不是从 manifest 能推断的；
凡未确认者取更严一档，与 `resolve_change_control()` 的兜底原则一致。

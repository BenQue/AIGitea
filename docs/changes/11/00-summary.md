---
issue: 11
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/11
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 为并行 Issue 增加结构化依赖合同并改变共享 controller 的 review-ready 判定
risk_flags:
  - platform-governance
  - shared-core-component
  - external-contract
depends_on: []
required_docs:
  - 00-summary.md
  - 01-spec.md
  - 02-plan.md
confidence: high
override_reason: ''
status: implemented
branch: change/11
pr_url:
created: 2026-07-24
updated: 2026-07-24
---

## 问题/需求总结

并行推进多个 Issue 时，依赖关系目前只存在于仓库外计划、会话记忆或自然语言中，最终 PR 页面没有稳定、可机械读取的依赖信号。Gitea 官方文档确认 `pull_request` Actions 使用 `refs/pull/<N>/head`，不是预览合并提交，因此现有 PR CI 只验证 head，不能依靠与最新 `main` 的合并结果自动暴露依赖缺失。

## 影响范围

- `templates/docs/changes/_template/`：为 change 文档增加可选 `depends_on` 列表。
- `codex/runtime/aisoft_loop/contract.py`：读取并验证依赖编号，保持旧文档缺省为空的兼容性。
- `codex/runtime/aisoft_loop/controller.py`：把依赖写入最终 PR 正文，并在依赖未完成时保持 `CONTINUE`，不得误报 `READY_FOR_REVIEW`。
- `codex/runtime/tests/test_contract.py`、`test_controller.py`：覆盖合法、非法、待依赖和依赖完成路径。
- `03-Issue-Spec-Plan与单闸门开发流程.md`、`04-Agent编排与定时任务.md`：说明依赖是 Gate C 的可见护栏，不是锁或自动合并权限。

## 初步方案与建议

以 `00-summary.md` front matter 的 `depends_on` 为机器事实源，值为去重后的正整数 Issue 编号列表；spec/plan 镜像该字段。controller 创建 PR 时生成依赖清单。PR CI 通过后，如果任一依赖 Issue 尚未同时满足 closed 与 `deployed`，controller 保存 `awaiting_dependencies` 状态并返回 `CONTINUE`；后续轮询只重新检查依赖和 CI，不重复执行 provider。全部依赖完成后才返回 `READY_FOR_REVIEW`。人的最终合并权不变。

## 风险

- `depends_on` 解析过宽可能接受自依赖、重复编号或非整数，造成永远等待。
- 依赖状态检查如果只看 closed 或只看标签，会把未部署或标签漂移误判为完成。
- 若等待依赖时重复调用 provider，会产生无意义提交或越界修改。
- 该变更影响所有使用共享 controller 的项目，必须保留旧文档无 `depends_on` 时的兼容性。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 为并行 Issue 增加结构化依赖合同并改变共享 controller 的 review-ready 判定
risk_flags:
  - platform-governance
  - shared-core-component
  - external-contract
required_docs:
  - 00-summary.md
  - 01-spec.md
  - 02-plan.md
confidence: high
override_reason: ''
```

### 判级证据

- `contract.py` 当前只验证 Issue、分类、分支、必需文档和 acceptance criteria，没有依赖字段。
- `controller.py::_pr_body` 当前只写 `Closes #N` 和 change 文档；CI success 直接进入 `READY_FOR_REVIEW`。
- Gitea Actions 官方 FAQ 明确 pull request ref 指向 head，不是 merge preview；现有 CI 不能替代依赖护栏。
- 修改共享 controller 和平台治理合同命中强制 complex 规则。

### 缺失的 acceptance criteria 或决策

- 无；Issue 已明确“不做锁”，并把目标限定为依赖可见和顺序护栏。

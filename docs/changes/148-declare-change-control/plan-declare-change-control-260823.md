---
issue: 148
branch: change/148-declare-change-control
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/149
status: pr-open
created: 2026-08-23
updated: 2026-08-23
---

# Plan · 为 manifest 里的项目声明 change_control

- Issue：[#148](http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/148)
- 分支：`change/148-declare-change-control`
- Spec：[spec-declare-change-control-260823.md](spec-declare-change-control-260823.md)

## 依赖图

```
T01 ── T02 ── T03 ── T04
```

严格线性。T02（改 manifest）会让 T03 要修的两条测试变红——**先红后修**是刻意的：
只有看到它们真的红了，才知道那两条断言确实钉住了正在改变的事实，而不是凭空改测试。

## 任务

### T01 · 确认机制已落地、配置未做

- `resolve_change_control()` 与 `classification.route()` 存在且有测试；
- `gitea-governance.json` 十个仓库逐个检查 `change_control` 是否声明。

出口：确认十个全部未声明（若已有声明，本 Issue 的前提就变了，停下重新裁决）。

### T02 · 给 LocalWMS 声明 development

`codex/config/gitea-governance.json` 的 LocalWMS 条目加一行。用文本插入而不是
`json.load` + `json.dump`——后者会重排整个文件的格式，把一行改动变成一份全文件 diff。

出口：`python3 -c "json.load(...)"` 可解析；十仓表里只有 LocalWMS 显示 `development`。

### T03 · 修两条把快照写成断言的测试

先跑一次确认它们真的红（`test_every_shipped_repository_defaults_to_production` 与
`test_declared_development_is_parsed`），再按 spec §3 改写：

- 前者只遍历**未声明**的仓库，并加防空转断言；
- 后者逐仓比对各自的声明值；
- 新增 `test_localwms_is_declared_development` 钉住新事实。

**不得**用「把 LocalWMS 从遍历里排除掉」这种写法绕过——那只是把一个快照换成另一个快照。

出口：`PYTHONPATH=. python3 -m unittest tests.test_change_control` 14 条全过。

### T04 · 全量与文档

- `bash codex/tests/smoke.sh`（CI 的唯一入口）；
- 四份文档，写明合并后仍须重装 manifest（需要 root，Agent 不能做）。

出口：smoke 全绿 exit 0；commit → broker push → broker 开 PR → 回填 `pr_url` 再推一次。

## 风险

| 风险 | 处置 |
|---|---|
| 改 manifest 触发别处的隐式断言 | T04 跑全量 smoke（507 条），不只跑 change_control 那一支 |
| 修测试时把意图一起改掉 | T03 明令禁止「排除 LocalWMS」式改法；两条都保留原意图，只去掉对快照的依赖 |
| 全仓声明后 AC2 断言空转 | 新增 `assertGreater(checked, 0)`，届时会红并要求补合成 fixture |
| 合并后以为已生效 | manifest 要装到 `/usr/local/share/aisoft/` 才对 Loop 生效；写进 summary 与 verification |
| 替其它项目裁决部署状态 | 不做。九个仓保持未声明，逐条理由记在 spec §4 |

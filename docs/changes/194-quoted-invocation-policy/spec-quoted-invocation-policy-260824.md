---
issue: 194
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/194
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
confidence: high
risk_flags:
  - platform-governance
  - shared-core
depends_on: []
status: approved
branch: change/194-quoted-invocation-policy
created: 2026-08-24
updated: 2026-08-24
---

# Spec · matt-snapshot front matter 的取值规则

## 1. 目标与原因

`_skill_front_matter`（`codex/runtime/aisoft_loop/matt_snapshot.py:193`）在同一个 for
循环里读两个字段，对引号给出两套答案：

```python
if line.startswith("name:"):
    name = line.split(":", 1)[1].strip().strip("'\"")
if line.startswith("disable-model-invocation:"):
    value = line.split(":", 1)[1].strip().lower()
    if value not in {"true", "false"}:
        raise SnapshotError(f"invalid invocation policy: {skill_file}")
```

合法 YAML `disable-model-invocation: 'true'` 因此被判成非法值，`build_manifest` 与
`verify_snapshot` 整体 fail-closed，而报错文本把读者引向「策略值写错了」——离真正的原因
（这个取值点不认引号）有一步之遥。`codex/install-skills.sh` 在第一次文件系统写入之前就
调用它，所以这一步失败会直接挡住 skills 安装。

目标是让这个函数对「一行 front matter 的值是什么」只有一个答案。

## 2. 为什么是「函数内统一取值点」而不是复用 `contract._safe_scalar`

Issue 正文点名要 spec 在两条路里选一条并说明理由。选**函数内统一**，理由如下。

`contract._safe_scalar`（`contract.py:568`）确实是平台自撰文档的读侧权威规则，
#186 / #189 也确实是「统一到读侧唯一权威解析」。但那两次的前提在这里不成立：它们修的是
**同一份文档**在同一条代码路径上被读了两遍，函数里现成就躺着 `resolve_summary` 已解析
好的 front matter。`_skill_front_matter` 没有这个前提——它自己按行扫，且扫的不是平台
自撰文档。把 `_safe_scalar` 引进来要付三笔代价：

1. **方言错配。** `_safe_scalar` 捆了两条规则：拒绝 YAML 标记 `& * ! { } [ ]`，以及剥
   一对引号。第一条存在的理由是「平台自撰文档由 agent 写，不得携带 YAML 锚点/别名」。
   `codex/vendor/mattpocock/**/SKILL.md` 是**上游第三方内容**，平台不撰写也不控制它。
   用平台自撰文档的安全方言去约束上游快照，是把一条与该内容无关的规则强加上去。
2. **闸门的依赖面。** `matt_snapshot` 是 `aisoft_loop` 里唯一零 intra-package import 的
   模块（只用 stdlib）。这不是巧合：`codex/install-skills.sh` 把
   `python3 -m aisoft_loop.matt_snapshot verify` 放在 `install -d` 之前当完整性闸门。
   引入 `contract` 会顺带拖进 `classification`、`aisoft_change_name` 与 `subprocess`。
   为一条剥引号规则换来这么大的 blast radius，对一个完整性闸门是坏交易。
3. **错误契约不兼容。** `_safe_scalar` 抛 `ContractError` 且要一个 `line_number`；
   `matt_snapshot` 的对外契约是 `SnapshotError(f"...: {skill_file}")`，file-scoped 而非
   line-scoped。要么让外来异常从 `build_manifest` 漏出去（打破所有 `except SnapshotError`
   的调用方），要么逐处包装——包装代码比规则本身还长。

而「让两行一致」如果只是给策略那行也补一个 `.strip("'\"")`，就会把**更差的**那条规则
定为共同规则。复现证据：`name: 'demo-skill`（未闭合引号）今天被 `.strip("'\"")` 静默
修复成 `demo-skill` 并通过下游正则。在一个存在意义就是「检测 vendored skill 是否被篡改」
的 fail-closed 模块里静默修复畸形 YAML 已经不对，把它扩散到一个决定 skill 能否被模型
调用的策略字段上更不对。

所以：**在 `_skill_front_matter` 自己的作用域里收敛出一个私有取值 helper，两行都经过
它，引号规则用成对剥离**。规则形状与 `_safe_scalar` 的引号处理相同，但用 `matt_snapshot`
自己的措辞和错误类型表达。这不违反 #186 / #189 的原则：那条原则禁止的是**同一个字段集合
在同一个函数里有两套答案**，不是禁止两个不同权威的文档各有自己的方言。

## 3. Acceptance criteria

- [ ] **AC-1** `disable-model-invocation: 'true'` / `"true"` / `'false'` / `"false"` 被
      解析成对应布尔值，不抛 `SnapshotError`。
- [ ] **AC-2** 裸写形式 `true` / `false` 行为完全不变，含大小写变体（`TRUE` 仍按 `true`
      处理）。
- [ ] **AC-3** 真正非法的值（`yes`、`1`、空值、`''`）仍 fail-closed 抛 `SnapshotError`，
      报错文本仍为 `invalid invocation policy: <file>`，不弱化。
- [ ] **AC-4** `name` 一行「引号与裸写都接受」的既有行为不变：`name: demo-skill`、
      `name: 'demo-skill'`、`name: "demo-skill"` 都解析成 `demo-skill`。
- [ ] **AC-5** `bash codex/tests/smoke.sh` 全绿，新增用例覆盖引号包裹的合法值与非法值
      两类。

## 4. 接口、数据与兼容性影响

- 无接口变化：`build_manifest(...)`、`verify_snapshot(...)`、`classify_update(...)` 的
  签名、返回结构与异常类型 `SnapshotError` 都不变；`python3 -m aisoft_loop.matt_snapshot
  verify` 的参数与退出码不变。
- 无 manifest schema 变化：`disable_model_invocation` 仍是布尔字段，
  `codex/vendor/mattpocock/v1.2.2/manifest.json` 一个字节都不改（现存快照全是裸写，
  解析结果逐字节相同）。
- 行为变化只发生在两类此前必然失败或本就畸形的输入上：
  - 引号包裹的合法策略值：从 `SnapshotError` 变为正确解析。此前没有能成功的路径可被打破。
  - **`name` 的畸形引号（未闭合或不配对，如 `name: 'demo-skill`）：从静默修复转为
    fail-closed 抛 `invalid skill name: <file>`。** 这是一次有意的收紧，不是 AC-4 所说的
    「引号与裸写都接受」；受影响的输入是不合法的 YAML，仓库现存快照与本仓库自建 skill
    里没有任何一处命中。此处显式记录，供合并闸门审阅。
- 上游快照内容不动，历史 manifest 不做批量改写。

## 5. 风险与回滚约束

- 主要风险是把策略校验改松。约束：校验式仍为「剥引号后的值必须属于 `{"true","false"}`，
  否则抛 `invalid invocation policy`」，只把「值是什么」换成统一取值点；AC-2 / AC-3 用
  新增与既有用例双向钉死。
- 次要风险是误伤真实快照。约束：smoke.sh 内既有的
  `matt_snapshot verify codex/vendor/mattpocock/v1.2.2` 对 35 个 skill 做真实校验，
  加上 `test_vendored_release_is_complete_and_matches_manifest` 断言 manifest 逐项一致，
  任何解析漂移都会红。
- 回滚：单文件、单函数内的局部改动，`git revert` 该 commit 即可，无迁移、无状态残留。

## 6. 非目标

- 不引入 `contract` 依赖，不把 `_safe_scalar` 提升为公共 API，不新建 util/yaml 模块
  （理由见 §2）。
- 不批量给 `codex/vendor/mattpocock/`、`codex/skills/`、`skill-for-codex/` 下现存的
  front matter 加或去引号。
- 不改 `codex/vendor/mattpocock/v1.2.2/` 下的上游快照内容与 manifest。
- 不重构 `_skill_front_matter` 的整体解析方式：仍是按行扫描 + 前缀匹配，不改成通用
  YAML 解析，不新增支持的字段。
- 不改 `_control_hash` / `_directory_hash` / `classify_update`。

## 7. 未决问题

- 无。

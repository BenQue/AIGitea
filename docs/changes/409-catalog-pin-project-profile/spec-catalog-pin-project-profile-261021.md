---
issue: 409
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/409
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - shared-core
  - external-contract
  - artifact
  - platform-governance
depends_on:
  - 402
status: analyzed
branch: change/409-catalog-pin-project-profile
created: 2026-10-21
updated: 2026-10-21
git_scope:
  - architecture/README.md
  - architecture/install.sh
  - architecture/catalog-releases/2026.08.3/catalog.json
  - architecture/catalog-releases/2026.08.3/profiles/linux-node-postgres-v1.json
  - architecture/catalog-releases/2026.08.3/profiles/linux-node-systemd-postgres-v1.json
  - architecture/catalog-releases/2026.08.3/profiles/small-embedded-sqlite-v1.json
  - architecture/catalog-releases/2026.08.3/profiles/windows-dotnet-postgres-v1.json
  - architecture/fixtures/project-profile/architecture.json
  - architecture/fixtures/project-profile/profiles/example-node-react-postgres-pm2-v1.json
  - codex/runtime/aisoft_architecture/cli.py
  - codex/runtime/aisoft_architecture/lockfile.py
  - codex/runtime/aisoft_architecture/validator.py
  - codex/runtime/aisoft_loop/change_audit.py
  - codex/runtime/aisoft_loop/cli.py
  - codex/runtime/tests/test_architecture_cli.py
  - codex/runtime/tests/test_architecture_pin.py
  - codex/runtime/tests/test_change_audit.py
  - codex/tools/aisoft-project-check.sh
  - codex/tools/usage-bundle.py
  - codex/tests/test-architecture-install.sh
  - codex/tests/test-project-check.sh
  - codex/tests/test-usage-bundle.sh
  - codex/tests/smoke.sh
  - codex/tests/smoke-pin-baseline.json
  - usage/CONTRACT.md
  - usage/bundle.json
  - docs/adr/0001-platform-boundary.md
  - docs/changes/409-catalog-pin-project-profile/summary-catalog-pin-project-profile-261021.md
  - docs/changes/409-catalog-pin-project-profile/spec-catalog-pin-project-profile-261021.md
  - docs/changes/409-catalog-pin-project-profile/plan-catalog-pin-project-profile-261021.md
  - docs/changes/409-catalog-pin-project-profile/verification-catalog-pin-project-profile-261021.md
---

# R12 存量项目可对齐：LEGACY 登记、catalog 按 revision pin、项目自带 profile

## 目标与原因

有历史的项目要能在 `aisoft project-check` 上全 PASS，而不必改写历史文档或在每次 catalog 发版后被迫重 lock；
项目技术栈不在平台 5 个 profile 里时，项目自己声明 profile（ADR 0001 D5 收口）。

## 设计

### 1. change-documents 的 LEGACY 登记

- `.aisoft/platform-usage.lock.json` 增加**可选**键 `legacy_changes_before`（正整数）。项目手写；usage-bundle
  的 lock 读取接受「三键」或「三键 + 该键」两种形状，其它键仍「格式不受支持」；`--adopt`、升级写 lock 时保留
  已有值。
- 一个 change 目录属于 legacy，当且仅当声明了阈值 N，且目录编号 < N。编号取法：能解析为 change 名元组的取
  issue 号；解析不了但目录名形如 `<数字>` 或 `<数字>-<任意>`（含零填充 `0001-…`）的取该数字；其它目录名没有
  编号，永远不是 legacy。
- legacy 目录在 `change-documents` 与 `change-pr-url` 两项的问题改记为 LEGACY 登记，不计 GAP；阈值以上目录
  照旧。全部问题都是 legacy 时该项 PASS，并另出一行 `LEGACY: <检查名> — 登记 K 个目录：…`。
- porcelain 输出新增 `<检查名>\tLEGACY\t<细节>` 行；`aisoft-project-check.sh` 像 NOTE 一样打印它，不进
  pass/gap/skip 计数（`result:` 行格式不变）。
- 判定不读 spec/plan 的 `status`，不改 summary schema 与 `contract.py`（与 R15 #408 无交集）。
- 平台仓自身没有 usage lock，行为不变。

### 2. catalog 按 revision pin

- 新增 `architecture/catalog-releases/<revision>/catalog.json` 与 `profiles/*.json`：每个已被替换的 revision
  一份，内容取自该 revision 在 git 中的最后一次提交，原样复制，之后不可变（发布包成员摘要钉住）。当前 revision
  仍在 `architecture/catalog.json` 与 `architecture/profiles/`。本次只补 2026.08.3（NewEMaint 在用；其余历史
  revision 没有已知 lock，用到时由新 Issue 补）。
- CLI 新增可选 `--catalog-releases DIR`。declaration 的 `catalog_revision` 等于当前 catalog 时行为不变；不等时
  先校验 revision 格式，再取 `DIR/<revision>/`，不存在或比当前新 → `CATALOG_REVISION_UNKNOWN`。命中快照时
  用快照的 catalog 与 profiles 走原有全部校验（`PROJECT_CATALOG_MISMATCH` 仍对**所选** catalog 生效）。
- pin 快照的 catalog/source `review_by` 过期不再 fail，改在结果里报 `review_overdue`；EOL、prohibited、
  exception 过期、digest、checksum、lock drift 照旧按当天 fail closed。
- 成功结果在落后时多出 `catalog_behind: {"pinned": …, "current": …}`（以及可能的 `review_overdue: true`）。
- `aisoft-project-check.sh` 传 `--catalog-releases`；落后时 `PASS: architecture-lock` 加一行
  `NOTE: architecture-lock — catalog pin <旧>，平台当前 <新>，升级走项目 Issue`。
- 失败时 GAP 文案带诊断码：`architecture-lock — <CODE>：<message>`。
- `architecture/install.sh` 一并安装 `catalog-releases/`；发布包把快照纳入成员。

### 3. 项目自带 profile

- `--profiles-dir` 可重复；按给出顺序找 `<profile_id>.json`，先找到者胜。`profile_id` 先过 schema 的
  `^[a-z0-9][a-z0-9-]+$` 再拼路径（`PROFILE_ID_INVALID`），都找不到 → `PROFILE_UNKNOWN`。
- 检查器在 `$repo/.aisoft/profiles/` 存在时把它放在第一位，平台目录（当前或快照）在后。项目 profile 与平台
  同名时以项目的为准，检查器多出一行 NOTE 说明。
- 平台对项目 profile 只做 `profile-v1.schema.json` + 既有 `validate_profile` 语义（引用的 component 必须在所选
  catalog 中且为 preferred，transition 规则不变）。lock 的 `profile_sha256` 照旧覆盖其内容。
- 平台 5 个 profile 保留原位，定位改为「示例与存量兼容」（README 与 ADR D5 写明）；不迁目录，避免存量 lock
  与发布包路径失效。
- 新增合成夹具 `architecture/fixtures/project-profile/`（中立名称，Node + React + PostgreSQL + PM2），测试
  覆盖 validate 与 lock。ADR D5 的 `architecture/` 行补一句：#358 结论——HSDB 这类技术栈由项目自记 profile。

### 4. 文档与发布

- `architecture/README.md`：pin 快照、`--catalog-releases`、项目 profile、review 过期降级。
- `usage/CONTRACT.md`：`legacy_changes_before` 写法与「先采用新版本再写键」。
- 发布包 `usage-bundle.sh --release <下一个空闲版本> --compatibility minor`（当前为 1.9.0；R15 先合并则顺延）。
- 不做可选的 legacy summary backfill 工具（LEGACY 登记已能让存量全 PASS，backfill 留给需要的项目 Issue）。

## 验收标准

1. NewEMaint 真实检出（只读；声明放在临时副本里）：加 `legacy_changes_before` 后 `change-documents`、
   `change-pr-url` 由 GAP 变为 PASS + LEGACY 登记；`architecture-lock` 不再报 `PROJECT_CATALOG_MISMATCH`，
   catalog 落后以 NOTE 出现。
2. SFM 真实检出（同上）：`change-documents` 由 GAP 变为 PASS + LEGACY 登记。
3. 两个项目的 `DOCKERFILE_DECLARATION_REQUIRED` 按确认点 1 的裁决处理（默认：保持 GAP，文案带诊断码）。
4. HSDB 技术栈写一份项目自带 profile（放临时副本），`aisoft-architecture validate` 与 `lock` 均成功，且
   `validate --lock` 对生成的 lock PASS。
5. 反向证明：阈值以上的坏目录仍 GAP；快照被改一字节 → NewEMaint lock `LOCK_DRIFT`；未知 revision →
   `CATALOG_REVISION_UNKNOWN`；pin 快照中 EOL 仍 fail；带未知键的 usage lock 仍「格式不受支持」。
6. `bash codex/tests/smoke.sh` 全绿；Codex 只读审查 PASS。

## 风险与回滚约束

- 回滚 = revert 本 PR；已写 `legacy_changes_before` 的项目会在旧工具下得到「格式不受支持」，所以使用合同要求
  采用新版本后再写。已发布的发布包版本不可变，回滚要发新版本。
- 快照与历史不一致会让存量 lock 漂移；以 NewEMaint 已提交 lock 做逐字节回归。

## 非目标

不改 catalog 内容；不替任何项目写 lock、声明或 profile；不改 `templates/docs/changes/_template/`；不改 summary/
approval schema；不给 #288 Dockerfile 规则做按 revision 的豁免（除非确认点 1 另有裁决）。

## 未决问题

- `DOCKERFILE_DECLARATION_REQUIRED`：默认保持 GAP（真实缺口，项目补 `dockerfiles` 后重 lock）；另一选项是 lock
  早于 #288 时降为 NOTE。请负责人在确认点 1 裁决。

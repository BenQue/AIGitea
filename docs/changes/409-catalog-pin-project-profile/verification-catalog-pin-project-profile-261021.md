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
status: pending
branch: change/409-catalog-pin-project-profile
created: 2026-10-21
updated: 2026-10-21
---

# R12 验证记录

## 基线与范围

- 基线：`origin/main` = `38ddc920`（R11 PR 405 合并后）。
- 2026-10-21 基线 project-check（平台源码检查器，项目本地检出只读）：NewEMaint `change-documents` GAP 16 条、
  `architecture-lock` GAP（`PROJECT_CATALOG_MISMATCH`）；SFM `change-documents` GAP 54 条、`architecture-lock`
  GAP（`DOCKERFILE_DECLARATION_REQUIRED`）；HSDB 无 `.aisoft/architecture.json`。
- 预研：以 git 中 2026.08.3 的 catalog 与 profile 重建 NewEMaint lock（跳过 Dockerfile 规则），与其已提交 lock
  逐字段相等；SFM 在当前 catalog 下同样相等。两者剩余唯一失败是 `DOCKERFILE_DECLARATION_REQUIRED`。

## 实现中的集成

- 实现中 #406（PR 407）合并，`origin/main` 前进到 `cee42949`；本分支未推送过，按平台规则本地 rebase 到它。
- 发布包 1.9.0（`compatibility: minor`）在本分支发布；合并前若有别的版本先占用 1.9.0，按顺延规则改发下一个空闲版本。

## 结果

### 单元与工具测试（本机 `/bin/bash` 3.2.57，Python 3）

| 命令 | 结果 |
|---|---|
| `python3 -m unittest tests.test_change_audit tests.test_required_documents` | PASS（LEGACY 新增 6 条） |
| `python3 -m unittest tests.test_architecture_pin` | PASS（13 条） |
| `python3 -m unittest discover -s tests -p 'test_architecture*.py'` | PASS（既有 85 条不变） |
| `bash codex/tests/test-usage-bundle.sh` | PASS（lock 可选键 6 例、`--adopt` 保留阈值） |
| `bash codex/tests/test-project-check.sh` | PASS（70 cases，新增 LEGACY、pin NOTE、未发布 revision、项目 profile 覆盖） |
| `bash codex/tests/test-architecture-install.sh` | PASS（安装后的快照能解析 pin） |
| `shellcheck` / `bash -n`：`aisoft-project-check.sh`、`architecture/install.sh`、`test-architecture-install.sh` | PASS |
| `bash codex/tests/test-installed-drift.sh` | PASS（45 条，新增快照被篡改/缺失即 GAP） |
| `bash codex/tests/smoke.sh`（head `7eabd660`） | PASS（`Codex platform static smoke checks passed.`，exit 0） |

### 反向证明

- 检查器把 `LEGACY)` 分支改坏 → `test-project-check.sh` case 32 红；去掉 `--catalog-releases` 传参 → case 12 红
  （在一次性 worktree 里改坏并临时重发 1.9.0，跑完即删）。
- `test_architecture_pin.py` 内含：快照改一个字节 → 已生成 lock `LOCK_DRIFT`；未知/更新/格式错误的 revision →
  `CATALOG_REVISION_UNKNOWN` 且诊断不回显输入；pin 快照中组件 EOL → `COMPONENT_EOL`；当前 catalog review 过期仍
  `CATALOG_REVIEW_OVERDUE`；不传 `--catalog-releases` 时仍 `PROJECT_CATALOG_MISMATCH`；`profile_id` 带 `../` →
  `PROFILE_ID_INVALID`；项目 profile 引用 sunset 组件 → `PROFILE_COMPONENT_STATE`。
- usage lock：阈值为 `0`、`true`、`"57"`、`1.5` 或带其它未知键 → `platform-pin` 格式不受支持；change 审计对同样的
  坏阈值报 GAP 而不是静默登记。

### 真实检出验收（只读）

经 broker `git.fetch.main` 取各项目 main（NewEMaint `b1087023`、SFM `799bf12`、HSDB `673cadb`），在 scratch 目录建
本地副本；声明、profile 与 lock 只写在副本里，没有写入任何项目仓。

| AC | 项目 | 之前（main 检查器） | 之后（本分支检查器） |
|---|---|---|---|
| 1 | NewEMaint，副本加 `legacy_changes_before: 98` | `change-documents` GAP 16 条；`architecture-lock` GAP（无诊断码，实为 `PROJECT_CATALOG_MISMATCH`）；`pass=6 gap=3` | `PASS: change-documents` + `LEGACY: 登记 16 项`；`architecture-lock` 不再报 catalog 不一致，剩 `DOCKERFILE_DECLARATION_REQUIRED`；`pass=7 gap=2` |
| 2 | SFM，副本加 `legacy_changes_before: 107` | `change-documents` GAP 53 条；`pass=5 gap=5` | `PASS: change-documents` + `LEGACY: 登记 53 项`；`pass=6 gap=4` |
| 3 | NewEMaint、SFM | — | `GAP: architecture-lock — DOCKERFILE_DECLARATION_REQUIRED：容器交付必须声明全部 Dockerfile。`（按裁决保持 GAP） |
| 4 | HSDB，副本自带 `hsdb-node-hono-postgres-pm2-v1` | 无 `.aisoft/architecture.json` | `validate`、`lock`、`validate --lock` 均 `valid`，`profile_source: project`；副本 project-check `PASS: architecture-lock`，`pass=10 gap=0` |

NewEMaint 的 catalog 落后 NOTE 在真实检出上被 Dockerfile GAP 挡在前面，没有出现在 project-check 输出里。另用 CLI 隔离
Dockerfile 规则跑它的已提交 V1 lock：对 2026.08.3 快照 `valid: true`，`catalog_behind: {pinned 2026.08.3, current
2026.09.0}`，即快照与它当年的 catalog 逐值一致（`catalog_sha256` 均为 `00df8323…`）。NOTE 这一路径本身由
`test-project-check.sh` 的 pinned 用例覆盖。

### 未执行

- 安装层：两台主机重装 broker 与技能、`check-installed-drift` 读回，合并后由负责人执行（NOT RUN）。
- 各项目真实写入 `legacy_changes_before`、补 `dockerfiles`、HSDB 提交自带 profile：属于各项目自己的 Issue（非目标）。

## 交叉审查

- 第 1 轮（Codex `codex exec -s read-only`，head `b0278a04`）：FAIL。2 MAJOR：改 `architecture/install.sh` 未同步
  `check-installed-drift.py` 的 installer 哈希钉子与安装面（smoke 红）；检查器 GAP 文案改为诊断码后
  `test_architecture_dockerfile.py` 的旧断言失败。2 MINOR：快照不可变测试未钉 profile 内容；spec 写
  `review_overdue` 而实现是 `catalog_review_overdue`。Codex 另核实快照与 `87b3aa4a` 逐字节一致、1.0.0–1.8.0
  发布记录未变、pin 快照上 EOL/prohibited/例外过期/digest/checksum/drift 仍 fail。
- 修复：`ab48f91f`（漂移检查映射 `catalog-releases/` 并重钉 installer 哈希）、`86a64551`（快照文件摘要全钉、
  漂移反向测试、诊断码断言、spec 字段名）。smoke 另红在 ADR D3 项目名守卫：快照原样保留当年 catalog 的 3 处项目名
  （与当前 `catalog.json` 同样 3 处，已在基线中），`7eabd660` 在 `project-leak-baseline.json` 为快照登记同样的 3 处。
- 第 2 轮：ROUND2

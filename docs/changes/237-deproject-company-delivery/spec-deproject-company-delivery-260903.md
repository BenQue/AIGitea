---
issue: 237
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/237
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - platform-governance
  - ci-guard
depends_on:
  - 233
status: approved
branch: change/237-deproject-company-delivery
created: 2026-09-03
updated: 2026-09-03
---

# Spec · 去项目化收尾：07 §5.1 措辞与 company-delivery/ 归属判定

## 目标与原因

按「项目相关内容由项目自身决定、平台只给环境级指导」（2026-09-02 定案）处置 #233 收尾盘点出的两处
项目专属残留：`07` §5.1 把一种交付形态写成「新项目默认」；`company-delivery/` 把 NewEmaint pilot 的
拓扑、target ID、Stage 进度与叙事写进 operator bundle 文档。本 spec 先给出 `company-delivery/` 逐文件
归属判定表（Issue 验收第 2 条要求），再定义可观察的验收结果。Issue 正文是合同源，本文不扩张。
行号以 `origin/main` = `c98b2e5`（Merge PR #236，#233）为准。

## 术语

- **通用**：与具体项目无关的交付合同——inventory/handoff/evidence/gitea-transition schema、CLI、Stage 框架、
  不变量与 evidence 规则。处置 = 保留并去项目名。
- **专属**：只对 NewEmaint pilot 成立的事实——两台公司 VM 的物理放置、`newemaint-prod` fixed target ID、
  compatibility matrix、operator 1.0.1→1.2.0 演进与 Stage 进度、#120/#124 叙事。处置 = 迁项目仓（平台侧改
  指针）或迁 `archive/`（保留原路径链接兼容说明）。
- **runtime 绑定标识符**：`codex/runtime/aisoft_company_delivery/` 以常量绑定的项目名字符串——
  `bundle.py:33` `COMPATIBILITY_PATH = "operator/compatibility/newemaint-company-pilot-v1.json"`、
  `contract.py:49/357` 与 `collector.py:350` 的 `aisoft-inbound-sync@newemaint.timer`。runtime 是 Issue 非目标，
  这些标识符在 `company-delivery/` 中的对应文件只能保留。
- **历史证据标注**：Markdown 用「历史证据（#120–#130 pilot，见 archive）」措辞；JSON schema 用 `$comment`
  键（JSON Schema 标准注释键；runtime 用自有 Python validator，不读 schema 文件，`test_company_delivery.py:734`
  只读结构分支）。
- **承接 Issue**：在 NewEmaint 仓（broker project `newemaint`，`admin/NewEMaint`）新开的 Issue，承接判定为
  迁项目仓的内容；本 Issue 不改该仓任何文件。

## 逐文件归属判定表（Issue 验收第 2 条）

| # | 文件 | NewEmaint 计数 | 判定 | 处置 |
|---|---|---|---|---|
| D-01 | `README.md` | 9 | 通用 | 去项目名改写：`:3–5` 定位句改为「公司两 VM 离线 handoff 的 operator 参考实现；pilot 历史见 archive」；`:12–14` 拓扑表改为 role 描述（「应用 runtime」「本地 OrbStack DockerLab」）；`:25` compatibility 行改为指针（pilot matrix，归属项目仓，平台副本因 builder 1.2.0 绑定路径保留）；`:65` 示例路径 `/approved/<project>/releases`；`:72` 「真实 release bytes」；`:93–95` #124 段改为历史证据措辞并指向 archive。改写后计数 0 |
| D-02 | `VERSION` | 0 | 通用 | 保留 `1.2.0`：operator 合同语义不变；bundle 字节变化由新 source SHA 重新生成 handoff 承接（runbook §2 既有规则） |
| D-03 | `bin/aisoft-company-delivery` | 0 | 通用 | 不改 |
| D-04 | `compatibility/newemaint-company-pilot-v1.json` | 1 | 专属 | 迁项目仓：内容归属由承接 Issue 承接；平台侧字节与路径不改（runtime 绑定标识符），`README.md:25` 改为指针；删除平台副本随衍生平台 Issue（runtime 参数化）处置 |
| D-05 | `runbook.md` | 8 | 通用框架 + 专属事实 | 框架去项目名：`:1` 标题「公司两 VM 确定性交付 operator runbook」；`:13`、`:34–35` 改 role 描述；`:17` `#120` 改「本次交付的 Issue/Change 编号」；`:216`、`:219`、`:234` `newemaint-prod` 改 `<fixed-target-id>`（同步 `test_company_delivery.py:2926` 钉住短语）；`:259–261` §2 改为历史证据措辞（保留 #120/#124 编号）。专属事实（两台公司 VM 物理放置、operator 演进、Stage 进度）迁 archive + 承接 Issue。改写后计数 0 |
| D-06 | `schema/inventory-v1.schema.json` | 2 | 通用 | 保留；enum/const `aisoft-inbound-sync@newemaint.timer` 是 runtime 绑定标识符，加顶层 `$comment` 标注为 pilot 历史证据；随衍生平台 Issue 参数化。计数 2→3（含标注） |
| D-07 | `schema/inventory-v2.schema.json` | 1 | 通用 | 同 D-06。计数 1→2 |
| D-08 | `schema/inventory-v3.schema.json` | 1 | 通用 | 同 D-06。计数 1→2 |
| D-09 | `schema/evidence-v1.schema.json` | 0 | 通用 | 不改 |
| D-10 | `schema/gitea-transition-v1.schema.json` | 0 | 通用 | 不改 |
| D-11 | `schema/gitea-transition-v2.schema.json` | 0 | 通用 | 不改 |
| D-12 | `schema/handoff-v1.schema.json` | 0 | 通用 | 不改 |
| D-13 | `templates/handoff-manifest.example.json` | 1 | 通用 | 保留；`matrix_path` 必须等于 runtime `COMPATIBILITY_PATH`（`load_handoff` 校验示例可解析），随 D-04 衍生 Issue 处置。计数 1 |
| D-14 | `templates/inventory.example.json` | 0 | 通用 | 不改 |
| D-15 | `templates/gitea-transition.example.json` | 0 | 通用 | 不改 |
| D-16 | `templates/evidence.pass.example.json` | 0 | 通用 | 不改 |
| D-17 | `templates/evidence.fail.example.json` | 0 | 通用 | 不改 |
| D-18 | `templates/evidence.blocked.example.json` | 0 | 通用 | 不改 |
| D-19 | `templates/evidence.not-run.example.json` | 0 | 通用 | 不改 |

合计 19 个文件，基线计数 23（与 Issue 正文一致）。改写后预期计数：Markdown 0；JSON 9（D-04 1、D-06 3、
D-07 2、D-08 2、D-13 1）——全部是 runtime 绑定标识符或其 `$comment` 标注，不再作为默认值、主机名、路径
或阶段清单出现在通用 Markdown 中。

### 平台仓其他文件的处置（Issue 验收第 1、5 条）

| # | 文件:行 | 现状 | 处置 |
|---|---|---|---|
| P-01 | `07:141` | `### 5.1 Linux 新项目默认与既有试点` | 改「### 5.1 Linux 容器化交付参考与既有试点」 |
| P-02 | `07:143` | 「新 Linux 项目采用 Docker-first、项目无关的 release contract：」 | 改「Linux 容器化项目可选用 `docker-release/` 的 Docker-first、项目无关 release contract 作为参考实现（交付形态由项目 `AGENTS.md`「项目事实」与 architecture 声明，平台不设默认，见 runbook §4）；其要点：」bullets 原样保留 |
| P-03 | `07:170–184` | 两段 NewEmaint pilot 物理放置例外与 operator 1.2.0 greenfield 叙事 | 迁 archive；原位改为一段指针：「某项目采用两台公司 VM + 本地非生产 role 的物理放置属项目级例外，不改变三 role capability；通用 operator 合同见 `company-delivery/runbook.md`，pilot 的拓扑、operator 版本与 Stage 进度由项目仓记录（历史见 archive）」 |
| P-04 | `07:88–90` | 「NewEmaint 的 `appserver-test` 只存在于本地…见 runbook」 | 改为通用：「采用两台公司 VM 路径的项目，其非生产 role 位于本地 DockerLab；通用 operator runbook、schema 与 `NOT RUN` 边界见 `company-delivery/runbook.md`」 |
| P-05 | `07:219–223` | 「NewEmaint pilot 改走 runbook 的 Stage 00–110…公司侧全部阶段当前为 NOT RUN」 | 改为通用：「两台公司 VM 路径改走 `company-delivery/runbook.md` 的 Stage 00–110…；各项目公司侧进度由项目仓记录」 |
| P-06 | `07:256` | 「NewEmaint 两台公司 VM 人工 operator workflow」 | 改「公司两 VM 人工 operator workflow（参考实现）」 |
| P-07 | `README.md:22` | 🟡 NewEmaint 公司交付 pilot（Issue #120）状态条目 | 迁 archive（追加到 `archive/company-delivery-pilot-历史-20260903.md`）；原位改为「🟡 公司两 VM 离线交付 operator 参考实现（`company-delivery/`）：真实 handoff 与公司侧阶段由采用该路径的项目仓记录」 |
| P-08 | `README.md:74–79` | NewEmaint pilot 物理部署段 | 改为通用：「采用两台公司 VM + 本地 DockerLab 的项目：公司只消费本地已验证的 exact bytes…执行合同见 runbook；本仓库或 PR 状态不代表公司已执行」 |
| P-09 | `README.md:158` | `[NewEmaint 公司交付 runbook]` 主表行 | 改「[公司两 VM 离线交付 operator runbook（参考实现）]」，描述去项目名；保持在 §5 主表原位（不改 `AGENTS.md` 目录段，避免触碰治理文件） |
| P-10 | `README.md:183` | 「NewEmaint pilot 固定为本地 OrbStack DockerLab，历史 `gitea-ci:8091`…」 | 改「由目标项目的 `appserver-test` profile 指定；历史 `gitea-ci:8091` 已在 Issue #21 收口，不得作为当前入口」 |
| P-11 | `12`、`13` | 4 处 `company-delivery/runbook.md` 引用 | 不改：链接目标不变，句子描述的仍是 runbook 定义的两台公司 VM 路径；#233 F 组已判定 12/13 正文保留为参考记录 |
| P-12 | `archive/README.md` | 索引 | 新增一行指向 `company-delivery-pilot-历史-20260903.md` |
| P-13 | `archive/company-delivery-pilot-历史-20260903.md` | 不存在 | 新建：逐字收录 P-03、P-07、D-01 `:3–5`/`:93–95`、D-05 `:259–261` 迁出的 pilot 叙事，记录 compatibility matrix `stage_map` 快照与 operator 1.0.1→1.2.0 演进（#120/#124/#126/#128/#130），并写明「原路径 `company-delivery/` 不变，通用合同仍在原位；本文件只是历史证据」 |

## Acceptance criteria

- [ ] **AC-1 07 §5.1 措辞**：`grep -n '新项目默认' 07-*.md` 为空；§5.1 标题与首句按 P-01/P-02 改写，
  bullets（`docker-release` contract 要点）diff 为空；`grep -c '平台不设默认' 07-*.md` = 1。
- [ ] **AC-2 判定表覆盖与去项目名**：判定表 D-01～D-19 覆盖 `find company-delivery -type f` 的全部 19 个文件
  （verification 逐行记录处置结果）；`grep -rci NewEmaint company-delivery/` 对 `README.md`、`runbook.md` 为 0，
  全目录合计 = 9 且只落在 D-04/D-06/D-07/D-08/D-13（runtime 绑定标识符及其 `$comment` 标注）；
  `grep -rn -i 'newemaint' company-delivery/schema/` 每处命中所在文件顶层含 `$comment` 且其文本含「历史证据」。
- [ ] **AC-3 专属内容归属**：承接 Issue 已在 NewEmaint 仓创建（编号写进 verification 与
  `archive/company-delivery-pilot-历史-20260903.md`），正文列出承接的内容清单（D-04 matrix、D-05 pilot 事实、
  P-03/P-07/P-08 叙事）；`git diff --stat origin/main...HEAD` 只含平台仓路径；`archive/` 新文件含「原路径
  `company-delivery/` 不变」的链接兼容说明；`archive/README.md` 新增 1 行索引。
- [ ] **AC-4 测试与守卫**：`smoke.sh` 新增独立守卫块，对 `company-delivery/README.md` 与 `runbook.md` 执行
  #231 AC-1 项目名 pattern（`rg -ni 'NewEMaint|SFMDigitalBoard|HSDB|WMPDA|SapTable|rsdesign|myapp|smoke-test|LocalWMS'`），
  命中即退出；反向证明：向副本追加 `参照 NewEMaint` 后单独执行守卫块报红并退出 1，真实树静默；
  `test_company_delivery.py:2926` 钉住短语改为 `aisoft-docker-release-gate <action> <fixed-target-id> <full-sha>`，
  其余断言不变；`test-company-delivery-real-release-harness.sh` 与 integration 测试 diff 为空；
  `bash codex/tests/smoke.sh` 全绿（含 651 unittest）；integration `--execute` 记 NOT RUN；
  `git diff --stat origin/main...HEAD -- codex/runtime/aisoft_company_delivery` 为空。
- [ ] **AC-5 引用一致**：`README.md`、`07`、`12`、`13` 中 `company-delivery/` 的每个链接目标存在（脚本逐链接
  检查 `links=N broken=0`，基线已知的 3 条 `skill-for-claude/aisoft-platform/SKILL.md -> references/*` install-time
  断链除外）；P-04～P-10 改写后 `README.md` 与 `07` 中不再把 runbook 描述为某项目的 runbook
  （`grep -n 'NewEmaint 公司交付 runbook\|NewEmaint 两台公司 VM 人工' README.md 07-*.md` 为空）。
- [ ] **AC-6 非目标守卫**：`git diff --stat origin/main...HEAD -- docker-release/ architecture/
  codex/runtime/aisoft_company_delivery codex/runtime/aisoft_loop codex/config codex/tools templates AGENTS.md
  skill-for-codex skill-for-claude codex/skills 12-*.md 13-*.md` 为空。

## 接口、数据与兼容性影响

- **operator bundle 字节**：`bundle.py:37` 把整个 `company-delivery/` 复制为 `operator/`，README/runbook/schema
  的改写会改变 bundle 内容；`VERSION` 保持 `1.2.0`（合同语义不变），按 runbook §2 既有规则任何正式搬运包都
  从 protected `main` exact SHA 重新生成并重新批准，不存在需要兼容的已发布 bundle。
- **runtime**：`codex/runtime/aisoft_company_delivery/` 零 diff。`COMPATIBILITY_PATH` 与 timer unit 名继续指向
  现有文件与字符串；D-04/D-06～D-08/D-13 因此保留。
- **runtime tests**：只改 `test_company_delivery.py:2926` 一条钉住文档短语的字面量；结构断言、schema 分支断言、
  模板可解析断言不变。
- **smoke.sh**：新增守卫只读 `company-delivery/README.md` 与 `runbook.md`；既有 JSON/Secret 扫描、harness 调用与
  #231/#233 守卫不变。`$comment` 键不触发 Secret 扫描 pattern（不含 `token|secret|password` 等赋值形态）。
- **下游 NewEmaint 仓**：只新开 Issue；不改任何文件、不部署。
- **`03` §3 verification 判据**：判定表处置结果、grep 计数、承接 Issue 编号、守卫反向证明与基线观测都是一次性
  证据，声明 `verification`。

## 风险与回滚约束

- 回滚 = revert 本 Issue 的唯一 PR；承接 Issue 与衍生 Issue 作为普通 Issue 关闭即可。
- 本 spec 即修改 `codex/tests/smoke.sh`（CI 守卫）与 `codex/runtime/tests/test_company_delivery.py`（单条字面量）
  的授权，范围以 AC-4 为限；不改任何 `AGENTS.md`、两侧技能源与 `codex/skills/`。

## 非目标

- 不改 `docker-release/`（#65 冻结）、`architecture/`、`codex/runtime/aisoft_company_delivery/`、broker、标签
  manifest、`templates/`。
- 不在本 Issue 内执行任何公司环境或 NewEmaint 部署动作；不改 NewEmaint 仓文件。
- 不全面清除 `07`、`12`、`13` 正文中其余项目名（`07` §1 第 9 条、组件图、`12`/`13` 的 pilot 说明）：#233 F 组
  已判定这些分册保留为参考记录；本 Issue 只处置 §5.1 与 `company-delivery/` 引用句。
- 不改 `AGENTS.md` 目录段（`company-delivery/` 从未列入，保持不列入）。
- 不 bump operator `VERSION`；不参数化 runtime（衍生平台 Issue）。

## 未决问题

无。上表与 AC 中的 4 项解读（runtime 绑定标识符保留并标注、测试字面量同步、README pilot 状态条目纳入、
承接 Issue 经 broker 创建）已于 2026-09-03 确认点 1 由人认可。

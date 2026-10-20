# 平台整改路线

- 依据：[ADR 0001 平台边界与两层分离](../adr/0001-platform-boundary.md)、2026-10-17 平台全面评审
- 建立：2026-10-17（Issue #364）
- 用法：这是活文档。每批开工时只在这里更新状态和 Issue 号；批次内的合同、授权与证据写在该 Issue 的 `docs/changes/` 目录。

## 总规则

1. **NewEMaint 优先。** NewEMaint 最小部署链（构建 → 发布制品 → 部署到 test → 健康检查 → 回滚演练）在 NewEMaint 仓推进，优先于本路线。本路线只做不阻塞它、也不改变它当前依赖的事项。
2. **NewEMaint 当前依赖、清理时不得改变的平台能力**（2026-10-17 读 NewEMaint `gitea/main` 确认）：docker-release 合同字节（`.aisoft/docker-release-contract.bytes.json`）、architecture 声明与 lock（`.aisoft/architecture*.json`）、routine merger 与 pilot 闸门（2026-10-19 负责人裁决退出，#385 撤下声明）、broker typed 操作、CI workflow 模板。任何批次要动这些，先在发起线程说明并等负责人裁决。
3. **少开 Issue。** 每批一个 Issue，衍生项先并入进行中的批次。
4. **删除清单。** 每个删除、移动或归档文件的 PR，正文列出完整路径清单与去向（`archive/` 或项目仓），并说明为什么不影响 NewEMaint。
5. **治理文件单独应用。** 修改 `AGENTS.md`、技能、controller、CI 或 broker 的批次，先由只改治理合同的受控步骤应用并停止，fresh run 重读后再改 runtime。
6. **交叉审核。** complex 批次的最终 PR，由未参与实现的另一方提供者独立审查（ADR D6）。

## 批次

| 批次 | 内容 | 评审条目 | 依赖 | 涉及 NewEMaint | 状态 |
|---|---|---|---|---|---|
| R0 | 平台边界 ADR 与本路线 | A1、A2、D1（决定部分） | 无 | 否 | #364 已完成 |
| R1 | 治理合同瘦身：修复 macOS 上 `/var` 符号链接导致的 #360 canonical 测试失败；`AGENTS.md` ≤ 5 KB 只留维护层规则；#327 单票合同移出 `AGENTS.md`、两份 `aisoft-platform` SKILL.md 与 `docs/agents/issue-tracker.md`；triage 规则加入 ADR D4 准入问题 | A2、B1 | R0 | 否 | #366 已完成 |
| R2 | 渗入守卫：smoke 从 manifest 读取已注册项目名，按 ADR D3 白名单报错；以棘轮落地：现存命中记入 `codex/config/project-leak-baseline.json`，基线外新增即失败，R3/R4 清理时收紧基线 | A3 | R0 | 否 | #368 已完成 |
| R3 | 模板与通用文档去项目化：`templates/project/ci` 的 registry 改占位并标“Node 栈示例”；summary 模板、两份 `issue-session-flow`、`private-gitea-access.md` 的依赖边改为指向 manifest；`03`、`04`、`08`、`README.md` 去掉项目事故与已退出项目的 as-built 叙述；代码注释里的项目轶事；`09` 归档；技能里的站点路径收进 site profile 引用；测试改钉结构 | 2.2、2.3、B3 | R1 | 否（只动文字，不动 CI 模板的已发布行为） | #371 已完成；summary 模板的依赖边因下游 vendored 移到 R6 |
| R4 | broker 与 governance 去项目化：#340 application target 改 manifest 数据，preflight 只留采集引擎；#213 routine pilot 写死项改为 manifest 自洽校验，评估退役 pilot 闸门并归档 `rollback-gitea-routine-pilot.sh`；#358 triage 时按扩展点处理（profile 由项目仓自带，平台只给 schema 与校验器） | A4 | R1 | **是**：routine merger、architecture lock | #373 已完成（PR 374，`c3d49ed`）：预检接口退役，pilot 保留但改 manifest 自洽校验；#358 在自身 Issue 重新 triage；summary 模板依赖边移到 R6 |
| R5 | 技能更新：superpowers 7.0.0 按 `08` §5 适配清单核对后两侧升级；核实 Codex 侧实际生效版本；重装 `aisoft-platform` 消除 project-align 漂移（负责人本人执行 installer）；只读版本核对脚本；CLI 升级后跑 provider 验收矩阵 | C1–C4 | 无 | 否 | #375 已完成（PR 376，`bcf2fd7`）：superpowers 7.0.0 适配核对、只读版本核对脚本；Codex 侧 superpowers 未生效，是否启用由负责人定 |
| R6 | 两层分离与发布包：起草并定稿“平台使用合同”与项目指针模板，由 project-align 下发；版本化发布包与项目 pin；`08` 验证矩阵拆成两层 | D1、D2、D4 | R1 | 否（平台侧只新增发布包；NewEMaint 改为 pin 发布包是 NewEMaint 仓的 Issue） | #377 进行中（负责人 2026-10-18 决定提前开工）：`usage/CONTRACT.md`、`usage/bundle.json` 发布 1.0.0、project-check 按 pin 核对、`08` §7 两层、summary 模板依赖边已清 |
| R6b | 测试夹具解耦：进 smoke 的测试改读自带夹具 manifest，不再断言真实 manifest 中某个项目的条目；`rollback-gitea-routine-pilot.sh` 改为按 manifest 中任意 pilot 工作的通用工具，或在 pilot 退役后归档 | A3、A4（残留） | R6 | 否（负责人 2026-10-18 裁决 pilot 退役） | #380 已完成（PR 382，`a395f7a`）：测试改读 `codex/tests/fixtures/manifests/` 合成夹具，smoke 守卫禁止测试读真实 manifest；回滚脚本归档、installer 删除已装副本；通用 pilot schema 与真实 manifest 声明保留 |
| R7 | 技能单一来源与 Cursor：一份 SKILL.md 由安装器生成三种落点；收编本机不受管的 Cursor 技能；`.cursor/rules` 只做薄指针；交叉审核写入维护层固定步骤 | D3、D5、D6 | R6 | 否 | #379 已完成（PR 381，`80a38dc`）：`skills/` 单一来源与 `skills.manifest`，两对技能合并为中文单份，两侧安装器与漂移检查改读它；发布包 1.1.0 导出 `.claude`、`.agents`、`.cursor` 三种项目级落点与 Cursor 薄指针；Cursor 的 Matt 与 superpowers 纳入只读版本核对；交叉审核写入 `03` §7 与 `08` §7.1 |
| R8 | 参考实现迁出：`docker-release`、`company-delivery`、`aisoft_release`、`aisoft_company_*` 移出 smoke 硬门，迁到项目仓或归档 | A1（裁决部分） | R6，NewEMaint 公司内网路线定案 | **是**（只删平台 main；NewEMaint 按 commit pin 取文件） | #383 已完成（PR 384）：六块互为依赖，同一 PR 迁出（含 `architecture/reference/newemaint` 与发布证据闸门），installer 8→7，发布包 1.2.0；负责人 2026-10-19 确认提交，NewEMaint 公司路线改用自有副本或按 commit 引用 |
| — | 证据精简（B2）不单独立批：从 R1 起每批按 ADR D9 执行 | B2 | R0 | 否 | 随各批 |
| — | 项目范围以本地 Gitea 注册为准 | E | — | — | 已定（ADR D10） |

## 推荐顺序

R0 → R1 → R2 与 R3 → R4。R5 与 R1 并行。负责人 2026-10-18 决定提前开 R6，紧接 R6b；R7 依赖 R6；R8 由 #383 在 R7 之后完成。

第一轮 R0–R8 已全部合并（R8 之后 #385 退出 routine pilot 声明、#387 停用失败的 VM 定时器，`main` = `77ad607`）。仍未达成的是「平台如何被使用」与「平台如何运维自己」两类：使用层技能仍依赖平台检出、四个应用项目只有一个 pin 了发布包、自动化路径与站点值仍钉在内核、安装面漂移没有棘轮。这些由第二轮处理。

## 第二轮（2026-10-20 起）

- 依据：[ADR 0002 确定性开发流程](../adr/0002-deterministic-development-flow.md)、项目库 `platform-remediation-plan-261020-final.md`（D1–D8 已于 2026-10-20 由负责人裁决，各批任务书在其 §4）
- 用法与总规则同第一轮；另加两条：合并前用 `apply-classification-labels.sh --verify N` 读回 `projected`；改过 broker、runtime 或技能的批次合并后由负责人两台重装并读回。

| 批次 | 内容 | 依赖 | 状态 |
|---|---|---|---|
| R9 | ADR 0002（路由合同与执行引擎分离）、第二轮路线、[平台级 E2E 验收表](platform-e2e-acceptance.md) | 无 | #389 进行中 |
| #370 | CI 下载缓存：runner 不再依赖每次访问 GitHub 与 Go 代理；由 Codex 实现、Claude 只读审查（D7，反向审查首例） | 无 | 未开工 |
| R10a | 自动化引擎退出：按 ADR 0002 D2 迁出 Development Loop、routine merge、VM profile 操作与 `install-vm`，broker 操作 39 → 34、installer 7 → 6；清理 VM 旧单元与 LocalWMS routine merger | R9 | #391 进行中 |
| R10b | 路由卡：路由表进 `aisoft-platform` 技能（只钉必用与禁用），summary `route:` 块，确认点 1 与派单任务书展示，`08` §7 模型档位表；发布包升版 | R9；Codex 侧验收依赖 R10c | 未开工 |
| R10c | 外部技能包三端一致：superpowers vendor pin 作三端核对基准，Claude/Codex 仍走官方 marketplace，发布包导出 Cursor 项目级落点（#392 确认点 1 修正） | R9 | #392 进行中 |
| R11 | 使用层可独立消费：随发布包交付 `aisoft` 工具入口，技能去平台检出依赖，tool-provenance 检查，三个项目批量采用（D4），发布说明（1.4.0） | R10a、R10b、R10c | 未开工 |
| R12 | 存量项目可对齐与架构扩展点：检查器 LEGACY 级、catalog 按 lock pin、profile 由项目自带（ADR 0001 D5 收口） | R11 | 未开工 |
| R13 | 站点外置与守卫补齐：manifest `site` 段（D5），内核改结构校验，泄漏守卫覆盖站点值与全部注册仓库名 | R10a | 未开工 |
| R14 | 文档现行态：分册改现行合同体，README 状态表机器生成，smoke 文档钉子棘轮 | R10a、R10b、R13 | 未开工 |
| R15 | 对等能力集与审查证据：三端能力集读回，审查证据索引与轮换规则，Cursor 使用层首次验收 | R11、R10c | 未开工 |
| R16 | 运维闭环第二步：漂移棘轮与 `applies_to`、重装进收尾、判级投影闸门、周清扫、PAT 周期、部署通知模板 | R10a | 未开工 |

推荐顺序：R9 →（#370 ∥ R10a ∥ R10c）→ R10b → R11 →（R12 ∥ R13）→ R14 → R15 → R16。项目侧的部署链演练与发布包采用不等平台，结果记入 E2E 验收表。

### 第二轮退出条件

1. [平台级 E2E 验收表](platform-e2e-acceptance.md) 至少一行是当前发布包版本（构建 → 发布 → test 部署 → 健康 SHA → 同版本 noop → 回滚）。
2. 四个应用项目中至少三个 `platform-pin` PASS，且会话工具来自发布包而不是平台检出。
3. Mac 与 VM `check-installed-drift` 在 `applies_to` 语义下 `RESULT PASS`；readiness 全 PASS。
4. Codex 再做一次总验收，ADR 0001 十项无 PARTIAL（或每个 PARTIAL 项各有承载 Issue）。

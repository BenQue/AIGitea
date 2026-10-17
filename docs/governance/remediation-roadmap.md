# 平台整改路线

- 依据：[ADR 0001 平台边界与两层分离](../adr/0001-platform-boundary.md)、2026-10-17 平台全面评审
- 建立：2026-10-17（Issue #364）
- 用法：这是活文档。每批开工时只在这里更新状态和 Issue 号；批次内的合同、授权与证据写在该 Issue 的 `docs/changes/` 目录。

## 总规则

1. **NewEMaint 优先。** NewEMaint 最小部署链（构建 → 发布制品 → 部署到 test → 健康检查 → 回滚演练）在 NewEMaint 仓推进，优先于本路线。本路线只做不阻塞它、也不改变它当前依赖的事项。
2. **NewEMaint 当前依赖、清理时不得改变的平台能力**（2026-10-17 读 NewEMaint `gitea/main` 确认）：docker-release 合同字节（`.aisoft/docker-release-contract.bytes.json`）、architecture 声明与 lock（`.aisoft/architecture*.json`）、routine merger 与 pilot 闸门、broker typed 操作、CI workflow 模板。任何批次要动这些，先在发起线程说明并等负责人裁决。
3. **少开 Issue。** 每批一个 Issue，衍生项先并入进行中的批次。
4. **删除清单。** 每个删除、移动或归档文件的 PR，正文列出完整路径清单与去向（`archive/` 或项目仓），并说明为什么不影响 NewEMaint。
5. **治理文件单独应用。** 修改 `AGENTS.md`、技能、controller、CI 或 broker 的批次，先由只改治理合同的受控步骤应用并停止，fresh run 重读后再改 runtime。
6. **交叉审核。** complex 批次的最终 PR，由未参与实现的另一方提供者独立审查（ADR D6）。

## 批次

| 批次 | 内容 | 评审条目 | 依赖 | 涉及 NewEMaint | 状态 |
|---|---|---|---|---|---|
| R0 | 平台边界 ADR 与本路线 | A1、A2、D1（决定部分） | 无 | 否 | #364 进行中 |
| R1 | 治理合同瘦身：`AGENTS.md` ≤ 5 KB 只留维护层规则；#327 单票合同移出 `AGENTS.md`、两份 `aisoft-platform` SKILL.md 与 `docs/agents/issue-tracker.md`；triage 规则加入 ADR D4 准入问题；起草“平台使用合同”初稿与项目指针模板 | A2、B1、D1 | R0 | 否 | 未开始 |
| R2 | 渗入守卫：smoke 从 manifest 读取已注册项目名，按 ADR D3 白名单报错；先以报告模式落地并列出现存命中，随 R3/R4 清零后转为硬门 | A3 | R0 | 否 | 未开始 |
| R3 | 模板与通用文档去项目化：`templates/project/ci` 的 registry 改占位并标“Node 栈示例”；summary 模板、两份 `issue-session-flow`、`private-gitea-access.md` 的依赖边改为指向 manifest；`03`、`04`、`08`、`README.md` 去掉项目事故与已退出项目的 as-built 叙述；代码注释里的项目轶事；`09` 归档；技能里的站点路径收进 site profile 引用；测试改钉结构 | 2.2、2.3、B3 | R1 | 否（只动文字，不动 CI 模板的已发布行为） | 未开始 |
| R4 | broker 与 governance 去项目化：#340 application target 改 manifest 数据，preflight 只留采集引擎；#213 routine pilot 写死项改为 manifest 自洽校验，评估退役 pilot 闸门并归档 `rollback-gitea-routine-pilot.sh`；#358 triage 时按扩展点处理（profile 由项目仓自带，平台只给 schema 与校验器） | A4 | R1 | **是**：routine merger、architecture lock | 未开始；开工前与 NewEMaint 线程核对 |
| R5 | 技能更新：superpowers 7.0.0 按 `08` §5 适配清单核对后两侧升级；核实 Codex 侧实际生效版本；重装 `aisoft-platform` 消除 project-align 漂移（负责人本人执行 installer）；只读版本核对脚本；CLI 升级后跑 provider 验收矩阵 | C1–C4 | 无 | 否 | 未开始；可与 R1 并行 |
| R6 | 两层分离与发布包：“平台使用合同”定稿并由 project-align 下发；版本化发布包与项目 pin；`08` 验证矩阵拆成两层 | D1、D2、D4 | R1 | **是**：NewEMaint 将从 pin 合同字节改为 pin 发布包 | 未开始；NewEMaint 部署链跑通后 |
| R7 | 技能单一来源与 Cursor：一份 SKILL.md 由安装器生成三种落点；收编本机不受管的 Cursor 技能；`.cursor/rules` 只做薄指针；交叉审核写入维护层固定步骤 | D3、D5、D6 | R6 | 否 | 未开始 |
| R8 | 参考实现迁出：`docker-release`、`company-delivery`、`aisoft_release`、`aisoft_company_*` 移出 smoke 硬门，迁到项目仓或归档 | A1（裁决部分） | R6，NewEMaint 公司内网路线定案 | **是** | 延期 |
| — | 证据精简（B2）不单独立批：从 R1 起每批按 ADR D9 执行 | B2 | R0 | 否 | 随各批 |
| — | 项目范围以本地 Gitea 注册为准 | E | — | — | 已定（ADR D10） |

## 推荐顺序

R0 → R1 → R2 与 R3 → R4。R5 与 R1 并行。R6、R7、R8 等 NewEMaint 部署链跑通后再开。

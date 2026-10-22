---
issue: 416
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/416
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - agent-governance
  - platform-governance
depends_on: []
branch: change/416-round2-partial-closeout
created: 2026-10-22
updated: 2026-10-22
git_scope:
  - 01-基础设施-VM-Gitea-Runner.md
  - 06-运维手册与踩坑集.md
  - 07-内网与生产平移路线.md
  - 12-Windows平台自动部署方案.md
  - 13-项目结果迁移与内网切换实施手册.md
  - 14-Windows部署与迁移验收清单.md
  - 15-VMware-Fusion-Windows-ARM原型实施手册.md
  - README.md
  - codex/config/project-leak-baseline.json
  - codex/runtime/tests/test_project_leak.py
  - codex/tests/check-project-leak.py
  - codex/tests/smoke-pin-baseline.json
  - codex/tests/smoke.sh
  - codex/tests/test-bootstrap-gitea-service-account.sh
  - codex/tests/test-gitea-readonly.sh
  - codex/tests/test-platform-readiness.sh
  - codex/tools/aisoft-platform-readiness.sh
  - codex/tools/bootstrap-gitea-service-account.sh
  - codex/tools/gitea-pat-helper/README.md
  - codex/tools/gitea-readonly.sh
  - codex/tools/rotate-gitea-service-account.md
  - docs/adr/0001-platform-boundary.md
  - docs/changes/416-round2-partial-closeout/plan-round2-partial-closeout-261022.md
  - docs/changes/416-round2-partial-closeout/spec-round2-partial-closeout-261022.md
  - docs/changes/416-round2-partial-closeout/summary-round2-partial-closeout-261022.md
  - docs/changes/416-round2-partial-closeout/verification-round2-partial-closeout-261022.md
  - docs/governance/remediation-roadmap.md
  - docs/governance/review-evidence-index.md
  - skills/issue-session-flow/SKILL.md
  - usage/bundle.json
---

# 第二轮总验收平台侧 PARTIAL 收口

## 目标与原因

把总验收报告里归平台仓的 PARTIAL 逐条关掉，或登记成负责人接受的例外，使第二轮退出条件 4 按括号读法收口。

## D3 残留逐条处置

基线（PIN `0bcc3cd8`）：项目名 10 文件 41 处，站点值 10 文件 37 处。

| 文件 | 命中 | 处置 | 理由 |
|---|---|---|---|
| `01-基础设施-VM-Gitea-Runner.md` | 项目名 1 | 清除 | 端口表一行写历史演示应用，改为不带名字的描述 |
| `07`、`12`、`13`、`14`、`15` 分册 | 项目名 28 | 清除 | `MyApp` 是通用示例名，碰巧与已注册测试仓同名；改为 `ExampleApp` / `example-app` |
| `codex/tools/bootstrap-gitea-service-account.sh` | 站点 1 | 清除 | 凭据根默认值改读 manifest `site.credential_root_vm`（源 checkout 优先，否则已装 manifest），`AISOFT_CREDENTIAL_ROOT` 照旧覆盖 |
| `codex/tools/gitea-readonly.sh` | 站点 2 | 清除 | 默认凭据文件改为 `$HOME/<site.orbstack_machine>-credentials.txt`，从同仓 manifest 读，`GITEA_CREDENTIAL_FILE` 照旧覆盖 |
| `codex/tools/rotate-gitea-service-account.md` | 站点 5 | 清除 | 路径、机器与账号改写成 `site.*` 键名 |
| `architecture/catalog-releases/2026.08.3/catalog.json` | 项目名 3 | 例外 | 已发布快照不可变 |
| `architecture/catalog.json` | 项目名 3 | 例外 | 兼容性说明记录的是观测证据；改字节就要升 catalog revision，牵动 profile、fixture 与各项目 lock，属于 NewEMaint 依赖的 architecture 合同（路线图总规则 2） |
| `architecture/evidence/inventory.json`、`official-sources.md` | 项目名 6，站点 22 | 例外 | 观测证据记录，性质同 `docs/changes/` |
| `architecture/decisions/0005`–`0007` | 站点各 1 | 例外 | 决策记录的关联链接，性质同 `docs/adr/`；该目录由 `architecture/install.sh` 装到 target 主机，改字节要第三台重装 |
| `codex/tools/gitea-pat-helper/README.md` | 站点 2 | 例外 | helper 构建输入树的一部分，任何字节变化都让 VM 漂移报 `helper-build-input-differ`（`check-installed-drift.py` 的 `same_tree_since`），需在 VM 重建 helper；T01 第 1 轮审查后由清除改为例外 |
| `codex/tools/ensure-gitea-collaborator.sh` | 站点 2 | 例外 | 已退役，只作历史兼容与回归证据（`06`），不再演进 |

另把守卫已放行、ADR 未写明的 `codex/vendor/`（上游技能包原样快照）补进 D3 允许位置。

## Acceptance criteria

- [ ] AC-1：路线图 R6 行写已完成（#377，PR 378，`8fa4458`，发布包 1.0.0）；#370 行写 Claude 实现、Codex 审查，与审查索引一致；
  「第二轮各批已全部合并」一句不再写死 `main` SHA 与发布包版本。`rg` 在路线图不再命中「#377 进行中」与「`main` = `1db191e`」。
  审查索引补 R9–R14、R16 各一行，取值来自各批 verification 或 PR 正文，查不到写「未记录」。
- [ ] AC-2：上表「清除」各项命中归零；ADR 0001 D3 新增「登记的例外」表，列出上表「例外」各文件与理由；
  `check-project-leak.py` 在基线里出现例外表未列的文件时失败（附反向测试）；守卫 PASS，基线文件数与命中数只减不增。
- [ ] AC-3：readiness 在非 macOS 主机上（`--render-readme` 除外）不读任何层，在仓库与 jq 检查之前打印 `HOST ERROR host-mismatch` 与在 Mac 运行的指引，
  退出码 2；VM 内经 `orb -m <site.orbstack_machine>` 实测如此；Mac 上运行六节 PASS、退出码 0。帮助文字、`06`、`issue-session-flow`
  收尾节与退出条件 3 统一为「两台各跑 drift，readiness 只在 Mac 跑」，收尾节写明技能只装在 Mac、broker 与 host-role 两台都装。
- [ ] AC-4：`AGENTS.md` 的整句 `grep -Fq` 钉子改为章节标题结构检查；钉子数低于 89 并下调 `smoke-pin-baseline.json`；
  `bash codex/tests/smoke.sh` 全量 exit 0。
- [ ] AC-5：路线图第二轮退出条件下登记 D6（单向审查，负责人 2026-10-20 取消反向审查）与 D9（#385、#389、#370、#406、#412 证据超预算，
  已合并不可改，往后由棘轮约束）两条接受的例外，各一行理由与决定日期；退出条件 4 写「已按括号读法收口」并链接 #416、#417、NewEMaint#324；
  本批路线图行与审查索引行在本 PR 写成合并后状态（`03` §7）。
- [ ] AC-6：AC-2 的例外核对与 AC-3 的主机拒绝各有反向证明（修复前红、修复后绿），记录在 verification。
- [ ] AC-7：使用发布包发 1.12.0（main 已占用则顺延），`usage-bundle.sh --verify` PASS。

## 接口、数据与兼容性影响

- readiness 新增退出码 2 的 `host-mismatch`，只在非 macOS 主机出现；Mac 上输出不变。
- 两个工具的默认凭据路径解析到与原来相同的值，环境变量覆盖不变。
- 已装 `bootstrap-gitea-service-account.sh` 需两台重装 broker；使用层项目升到 1.12.0 是各项目自己的事。

## 风险与回滚约束

- 回滚：revert 本 PR，两台重装 broker，再发下一个发布包版本。
- 例外表与基线靠守卫互相核对，例外表是人写的；新增例外仍要走 complex Issue。

## 非目标

- PAT 真实轮换（#417）、当前版本 E2E 与 NewEMaint 升包（NewEMaint#324）。
- 改写已发布 catalog 快照、升 catalog revision、补造历史交叉审查或重开反向审查。
- VM 侧任何改动；技能本来就不装在 VM。

## 未决问题

- 无。上表的清除/例外划分在确认点 1 由负责人确认或改格。

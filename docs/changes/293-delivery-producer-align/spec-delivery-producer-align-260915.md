---
issue: 293
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/293
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - platform-governance
  - agent-governance
  - external-contract
depends_on: []
status: contract-drafting
branch: change/293-delivery-producer-align
created: 2026-09-15
updated: 2026-09-15
---

# Spec · 对齐本机构建-离线交付合同（12-Windows §2、07 §1、runbook §4）

## 目标与原因

2026-09-15 用户决定：现阶段所有项目采用「本机（Mac）构建 → 本地 OrbStack 测试 → 发布包以 GitHub
Release 资产中转 → 公司内网 Gitea 只做核验与独立授权部署」；GitHub Actions 构建只作候选，一个项目只能
选一种 producer；公司内网不能联网构建。平台三份参考文档对「权威源、构建位置、GitHub 角色」的表述
互相矛盾或缺位（Issue #293 正文 5 项），下游项目无法从 runbook 与 AGENTS.md 模板得到一致的声明位。本
spec 把 Issue 正文的范围落成逐条可核清单。行号以 `origin/main` = `a2f8854`（PR #291 merge）为准。

## 术语

- **producer**：生成不可变 release 制品的构建位置。`release_producer: local` = 开发侧本机以钉版本 SDK
  容器构建并在本地测试；`release_producer: github` = GitHub Actions 构建（候选）。一个项目只能一种。
- **transport**：已测试发布包进入公司内网的介质。`github-release` = GitHub Release 资产；`offline-bundle`
  = checksum-pinned 离线包（company-delivery 路径）。介质不改变 release identity。
- **已测试的 versioned release bundle**：以完整 merge SHA 命名、带 `SHA256SUMS` 与 `release.json`
  或等价 manifest、已在本地 test 环境验收过的制品集合；校验和与 release SHA 经 handoff 证据带出，
  公司侧对照后才可消费。
- **源码同步关系**（NewEMaint #80 现行路线）：本机 Gitea 是唯一源码源，GitHub 私有仓是它的原生
  Push Mirror；公司侧从 GitHub 取源码走 12-Linux §8 入站合同，与本 spec 的制品传输是两条独立通道。
- **统一事实句**：三份文档对同一事实使用同一表述——本机 Gitea 是唯一源码源（开发权威）；构建位置在
  开发侧；GitHub 私有仓是原生 Push Mirror 与 Release 资产中转；公司内网 Gitea 是部署权威，只核验校验和
  与 release SHA 并独立授权部署；GitHub 不进入公司信任链。

## Acceptance criteria

- [ ] AC-1 12-Windows §2、07 §1、runbook §4 对同一事实（权威源、构建位置、GitHub 角色）表述一致，无
  互相矛盾的句子；「公司 Windows x64 Runner 构建」「唯一正式权威源」「与公司 Gitea 无关系」三句在
  12-Windows 中 rg 为 0 命中，或已改为带日期的历史注记。
- [ ] AC-2 07 §1 明确：已测试的 versioned release bundle（完整 merge SHA 命名 + SHA256SUMS +
  release.json/manifest）属于可迁移「结果」，GitHub Release 资产是允许的传输介质之一；校验和与 release
  SHA 经 handoff 证据带出、公司侧对照；「GitHub 不进入公司信任链」措辞保留。
- [ ] AC-3 runbook §4.4 新增不变量：producer 工具链钉版本（SDK 容器 + lock 文件 + locked-mode restore）；
  §4.2 注明 arm64 交叉构建方式与 emulated 测试证据标注；§4.5 新增 `release_producer`（local 或 github，
  一个项目只能一种）与 transport 声明要求，并说明 GitHub Actions 构建作为候选的适用条件（原生
  amd64/Windows runner、发布频繁、native 模块在模拟下失败）。
- [ ] AC-4 `templates/project/AGENTS.md`「项目事实」含 `release_producer` 与 `transport` 两个占位字段。
- [ ] AC-5 `codex/runtime/tests` 中钉住 README/07/12 短语的单测全部通过；`bash codex/tests/smoke.sh`
  全绿；`check-change-documents` PASS。
- [ ] AC-6 唯一最终 PR 为 manual，由人合并；不部署。

## 逐条清单

### A · `12-Windows平台自动部署方案.md`（AC-1）

| # | 位置 | 现状 | 改后 |
|---|---|---|---|
| A-01 | §2 表「正式代码源」行（L25） | 迁移后公司内网 Gitea 是唯一正式权威源 | 本机 Gitea 是唯一源码源（开发权威）；公司内网 Gitea 是部署权威，只核验与独立授权部署（07 §1，2026-08-11 定案） |
| A-02 | §2 表「GitHub」行（L26） | 只镜像本地 Gitea，与公司 Gitea 无关系 | 私有仓是本机 Gitea 的原生 Push Mirror（源码同步，NewEMaint #80 路线）；已测试发布包以 GitHub Release 资产中转到公司；GitHub 不进入公司信任链 |
| A-03 | §2 表「构建」行（L27） | 正式制品由公司 Windows x64 Runner 构建 | `release_producer: local`——正式 `win-x64` 制品在开发侧本机以钉版本 SDK 容器构建并本地测试；公司内网不联网构建。GitHub Actions windows runner 只作候选（runbook §4.5 适用条件），一个项目只能一种 producer |
| A-04 | §2 表新增「传输」行 | 无 | GitHub Release 资产（ZIP + SHA256 + manifest）→ 公司侧下载并对照 handoff 证据核验 → 公司 Gitea Generic Package / 部署控制端；介质不改变 release identity |
| A-05 | §2 表末尾新增历史注记 | 无 | 一行带日期注记：2026-09-15 起 §2 原「公司 Runner 构建 / 公司 Gitea 唯一权威 / GitHub 与公司无关」三项按 07 §1 与本次决定改写，不再作为决策（不复述原句） |
| A-06 | §3 mermaid（L37–47） | `G --> WR["Windows x64 Runner"] --> PKG` | `MAC` 增加「本机 producer 构建 + 本地测试」；`MAC -->|"Push Mirror"| GH["GitHub 私有仓"]`，`MAC -->|"Release 资产"| GHR["GitHub Release"]`，`GHR -->|"下载 + SHA256/manifest 核验"| CV["公司 scm-ci 核验"] --> PKG`；删除 `WR` 节点 |
| A-07 | §3 角色表「Windows Runner」行（L55） | 编译、测试、打包、上传制品 / 成为生产管理员 | 改为「本机 producer（Mac 钉版本 SDK 容器）」：允许 编译、测试、打包、发布 Release 资产；禁止 持有生产 Secret、直连公司环境。新增「GitHub Release」行：允许 中转已测试制品；禁止 进入公司信任链、触发公司部署 |
| A-08 | §5 构建顺序前导句（L103） | 「构建顺序：」 | 「构建顺序（在本机 producer 的钉版本 SDK 容器内执行；选 GitHub Actions 候选时同一顺序在 windows runner 执行）：」；`npm ci` 与 `dotnet restore` 行注明 lock 文件与 `--locked-mode` |
| A-09 | §5 末句（L117） | 锁定 .NET、Node、npm、PostgreSQL 客户端和 Gitea Runner 版本 | 锁定 .NET、Node、npm、PostgreSQL 客户端与 producer 容器镜像 digest（候选 GitHub runner 时锁定 runner 镜像）版本 |
| A-10 | §8 L186 与 L189 | 防火墙只允许 Runner 或指定部署机；流程首行 `Runner` | 防火墙只允许指定部署执行端；流程首行「部署执行端（本地测试为本机，公司测试为部署控制端）」 |
| A-11 | §13 非目标列表 | 无 | 新增一条：在公司内网联网构建，或让公司 Gitea/Runner 成为正式制品 producer |

### B · `07-内网与生产平移路线.md`（AC-1、AC-2）

| # | 位置 | 现状 | 改后 |
|---|---|---|---|
| B-01 | §1 第 2 条末句（L12） | GitHub 是本地镜像与向公司内网的搬运中继 | GitHub 私有仓是本机 Gitea 的原生 Push Mirror（源码同步，NewEMaint #80 路线）与向公司内网的搬运中继；已测试发布包另以 GitHub Release 资产中转 |
| B-02 | §1 第 4 条之后新增一条 | 无 | 构建位置固定在开发侧：`release_producer: local` 时由本机以钉版本 SDK 容器构建并在本地 OrbStack 测试；公司内网不联网构建，公司 Gitea 只核验校验和与 release SHA 并独立授权部署；GitHub Actions 构建只作候选，一个项目只能一种 producer（runbook §4.5）。后续条目顺延编号 |
| B-03 | §1「结果」段（L31） | 「原型制品、Secret、Runner 注册和环境配置不作为结果迁移」 | 「结果」另含已测试的 versioned release bundle（完整 merge SHA 命名 + SHA256SUMS + release.json/manifest）；校验和与 release SHA 经 handoff 证据带出、公司侧对照后才可消费；GitHub Release 资产与 checksum-pinned offline bundle 都是允许的传输介质，介质不改变 release identity，GitHub 不进入公司信任链。未测试的原型制品、Secret、Runner 注册和环境配置仍不作为结果迁移 |
| B-04 | §2 mermaid `WR` 节点（L59、L65）**待确认点 1 认可** | `WR["Windows x64 Runner<br/>React + .NET 构建"]`，`CG --> WR --> PKG` | `CV["公司 scm-ci<br/>核验 Release 资产 SHA256/manifest"]`，`CG --> CV --> PKG`；LAB 子图 `MAC` 增加「本机 producer 构建」并新增 `MAC -->|"GitHub Release 资产"| CV` 边 |

不改 §1 第 9 条与 §5.1、§7、§8、§10、「GitHub 入站同步候选」段；`codex/runtime/tests` 与 `smoke.sh`
钉住的 07 短语全部保留。

### C · `skill-for-codex/references/onboarding-runbook.md`（AC-3）

| # | 位置 | 现状 | 改后 |
|---|---|---|---|
| C-01 | §4.2 列表末尾（L193 之后） | 无 arm64 说明 | 新增：producer 宿主为 arm64 Mac 而目标为 `linux/amd64` 时，用 `docker buildx build --platform linux/amd64`（或 OrbStack Rosetta）交叉构建；在本地 DockerLab 以模拟 amd64 运行时得到的测试证据必须标注 `emulated`，不得写成原生 amd64 证据；native 模块在模拟下失败是选择 GitHub Actions 候选 producer 的适用条件之一（§4.5） |
| C-02 | §4.4 列表「不可变制品」之后 | 无 | 新增不变量：producer 工具链钉版本——制品由固定版本的 SDK 容器（镜像 digest）构建，依赖 lock 文件进仓库，restore 使用 locked-mode（`npm ci`、`dotnet restore --locked-mode` 等），不接受浮动版本；构建位置在开发侧 `release_producer`，公司内网不联网构建 |
| C-03 | §4.5「声明」条 | 只要求交付形态与部署方案位置 | 追加：`release_producer`（`local` 本机构建 + 本地测试，或 `github` GitHub Actions 构建；一个项目只能一种）与 `transport`（已测试发布包进入公司的介质：`github-release`、`offline-bundle` 或其它）两个必填声明 |
| C-04 | §4.5 新增一条 | 无 | GitHub Actions 构建作为候选 producer 的适用条件：需要原生 amd64/Windows runner、发布频繁、native 模块在模拟下失败；选它不改变公司侧只核验校验和与 release SHA 并独立授权部署、GitHub 不进入公司信任链的边界，也不允许与 local 混用 |

`smoke.sh` 钉住的 `ensure-gitea-collaborator.sh`、`gitea-governance.json`、`gitea.labels.provision`
与 `test_architecture_governance.py` 钉住的「Architecture declaration onboarding」保留。

### D · `templates/project/AGENTS.md`（AC-4）

| # | 位置 | 现状 | 改后 |
|---|---|---|---|
| D-01 | 「项目事实」的「部署方案位置」bullet 之后 | 无 | 新增 bullet：`release_producer: <local 或 github>`（一个项目只能一种；local = 本机钉版本 SDK 容器构建 + 本地测试，github = GitHub Actions 构建候选，适用条件见 runbook §4.5） |
| D-02 | 同上 | 无 | 新增 bullet：`transport: <github-release 或 offline-bundle 或 其它>`（已测试发布包进入公司的介质；公司侧只核验校验和与 release SHA，GitHub 不进入公司信任链） |

两行都是独立 bullet，位于「交付形态」块之外，且不含 `docker-release/v2`、`PM2`、`Windows/IIS`，
`aisoft-project-check.sh` 的 delivery-profile 判定不受影响。

## 明确授权的修改范围

- 本 spec 显式授权修改两个治理文件：`skill-for-codex/references/onboarding-runbook.md` §4.2/§4.4/§4.5
  与 `templates/project/AGENTS.md`「项目事实」；只按上表增补，不改其它节。
- `README.md`、`06` 只在需要交叉引用时更新一行；本 spec 当前不要求。
- 不修改根 `AGENTS.md`、`codex/skills/*/SKILL.md`、`skill-for-claude/*/SKILL.md`、runtime、broker、CI、
  `docker-release/`、`company-delivery/`、`architecture/`、`sync/`、`13`、`14`、`15`、`12-Linux`。

## 接口、数据与兼容性影响

- 无代码接口、schema 或数据变化。
- 下游项目 `AGENTS.md` 新增两个声明位；已对齐项目在各自独立 Issue 中补填，本 PR 不改任何项目仓。
- onboarding-runbook 改后本机 Claude 侧 skill 立即 DRIFT；本 Issue 内用 `bash skill-for-claude/install.sh`
  重装并让 `check-drift.sh` 回 CLEAN。Codex 侧 `~/.agents/skills` 由人在 Codex 会话另行自查。

## 风险与回滚约束

- 纯文档与模板；回滚即 `git revert` 唯一 PR 的 merge commit。
- 守卫：`smoke.sh` 与 Python 单测钉住的短语只增不删；改动后跑全量。
- 措辞：AC-1 的三句在 12-Windows 中以 rg 自证 0 命中。

## 非目标

- 不实现任何构建脚本、GitHub Release 上传或公司侧下载核验流程。
- 不改变 company-delivery Stage 00–110、docker-release consumer 合同、`sync/` 入站合同。
- 不处理平台 #292（GitHub 出站 relay）；不改 NewEMaint 或任何项目仓。
- 不把 GitHub Actions 候选写成默认。

## 未决问题

进入 `approved` 前须由确认点 1 定下：

1. `change_type` 取 `platform`（本 spec 采用）还是 `docs`——两者路由结论一致（complex、manual）。
2. B-04：07 §2 拓扑图公司侧 Windows Runner 构建节点是否允许在本 PR 内最小改写——建议纳入，否则该图
   与改后 §1 直接矛盾；不纳入则记入 verification 并另开衍生 Issue。

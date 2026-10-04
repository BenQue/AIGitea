---
issue: 334
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/334
change_type: docs
requested_complexity: auto
assessed_complexity: small
effective_complexity: small
contract_effect: unchanged
confidence: high
risk_flags: []
depends_on: []
status: local-verified
branch: change/334-refresh-platform-docs
created: 2026-10-04
updated: 2026-10-04
---

# Verification：稳定文档全面核查

基线：`dc9aa468580f92a73dfa054c6f04ef5113f56694`；日期 2026-10-04（Asia/Shanghai）。
本票仅文档实施，source/local 和 Gitea 只读事实不代表 installed/live 或部署验收。

## 主要结论与处理

- 源码持续更新：本次 fresh `origin/main` 为 2026-10-03 的 `dc9aa46`；原根 checkout 尚在 `5c2cd72`。
  README 版本头停在 2026-09-07、§1 停在 2026-09-06；落后的是总览同步，不能据此认定源码停更。
- README 重新按领域列稳定能力、证据和采用边界；保留 v3.6 合同版本，不虚构新的 runtime release。
- #289/#288 的 source 已实现且合并，删去当前入口的“待实施/PR 未执行”措辞；原历史 Change 快照不改。
- #290 test-only 共置已合并；01/12-Linux 对已有规则的说明同步到当前合同，production 分离条件未变。
- 01 的九仓/九 Agent 是 #35 历史验收；current manifest 为六仓（三个内部业务仓 + 三个 public 仓），
  不把历史数量或退出解释成今日 ACL 修改。
- README §4 图恢复确认 → push/PR 的正确次序；只修正展示，与已存在 AGENTS、Controller 和 skill 一致。
- source guard 对 detached/no-upstream 等不能比较的情形只报告 staleness unchecked，不能当 fresh main 证明。
- #287 architecture CLI 默认 V2/接受 V1+V2，但 `aisoft_release.contract` 的
  `ARCHITECTURE_LOCK_SCHEMA_VERSION` 仍限定 V1；这是现行兼容边界，未改代码或 lock 来制造通过。
- #327 仍 open，不能写成稳定 FF 发布能力；#333 已有 approved 标签但仍 open，Issue 原正文还保留未 approved 的
  起点快照，本文以实际标签/状态读回为准。本次未读其另一会话工作树或现场证据，不宣称验收完成。

## 全面核查清单

下列 24 个主要入口逐项核对状态、用途、当前/历史边界和导航。另对全部 66 份当前受管 Markdown
（根指导、skills/references、templates、ADR、runbooks 等）进行本地路径与标题锚点扫描；
历史 Change、vendor、fixture 和 archive 不批量改写。archive/README 作为主要历史入口另行纳入。
外部 URL 的可达性、VM 服务健康、应用仓 adopted bytes 与公司现场未在本票核验。

| 入口 | 结论 / 处理 |
|---|---|
| README | 更新日期/exact stable pin、按领域状态、来源与现场边界；补基线/helper 导航；修流程图与 source guard 说明 |
| 01 | 同步 current 六仓与历史九仓区别、routine/manual 身份说明、#290 test 共置；#309/#311 实证记录保留 |
| 02 | 保留 PM2/SQLite as-built、非新项目默认；当前部署原则已有明确指针，无需改正文 |
| 03 | #289 resolver/terminal 已实现并合并的状态同步；治理规则正文未变 |
| 04 | 更新核对日期和稳定状态指针；#286/Controller source 边界保留 |
| 05 | Mailpit 演示与 SMTP 参考边界保留，未新验真实邮件投递 |
| 06 | #308/#316 现行细节已随源码更新；README 移除易漂移的踩坑数量并补导航 |
| 07 | 移除当前标题对业务项目“尚未开始”的未核实断言，保留项目归属、传输和 Windows 边界 |
| 08 | 更新 #298/#318/#320 同步日期，provider 真实矩阵/默认 none 保留 |
| 09 | 顶部指向最新状态；§0.2 routine 条目按逐项目证据表述，原规划日期/数量/历史正文保留 |
| 12-Linux | 保留历史参考性质；同步 #290 test 例外与 #296 精确兼容行的当前入口，生产拓扑不变 |
| 12-Windows | 设计参考、尚未实施和验收，保留 |
| 13 | 结果基线/持续权威分工与备选切换，保留；非 live 进度表 |
| 14 | 全部 NOT RUN 验收模板，保留 |
| 15 | Fusion/Windows ARM 快速原型参考，正式 x64/AD 验收未跑，保留 |
| architecture/README | 更新 #288 合并状态；V1/V2 与 release V1-only、target/current 边界保留 |
| architecture/reference/newemaint/README | target-only 历史参考；#52 跟踪不授权实施，原证据保留，不代表本次 live 项目盘点 |
| docker-release/README | #296/#305/#317 已有正文；目标 store 精确矩阵、state v3、数据库兼容 fail closed 保留 |
| company-delivery/README | 当前 operator 1.3.0；应用交付参考与现场阶段独立，保留 |
| company-delivery/runbook | versioned 人工 Stage 00–110 参考，保留，不声明公司已执行 |
| company-delivery/baseline/README | #274 v2/#278 collector/#280 diagnostics 的 source 与现场边界完整，保留 |
| platform-bootstrap/README | 独立 handoff/action contract，site executor unbound；公司现场未实施，保留 |
| codex/tools/gitea-pat-helper/README | 同步 #316 已合并和 T04 来源；现场验收由 #333 独立回执确认 |
| archive/README | 历史导航有效、非当前事实源，保留 |

清单计数以 [Markdown audit](evidence/markdown-audit.json) 的 `core_inventory` 为准。扫描中的三个 Claude `references/*.md` 引用是 installer
将共享 references 复制到安装目录的布局合同；对应 source 均存在，未修改安装布局或治理源。

## README 上次集中同步后的主线合并

范围：`61b0399..dc9aa46` 的 first-parent，共 33 次。完整 SHA/日期/原始标题见
[recent-merges.json](evidence/recent-merges.json)。下表为已合并事实，不把 source commit 当作 installed/live 证明。

| 日期 | Issue / 唯一 PR | merge SHA | 主题 |
|---|---|---|---|
| 2026-09-06 | #266 / [PR #267](http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/267) | `3fb6b60` | docs(readme): #266 §4 时序图消息文本的半角分号改全角，恢复 Mermaid 渲染 |
| 2026-09-06 | #268 / [PR #269](http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/269) | `2a012bd` | docs: #268 发布公司平台先行部署与 NewEMaint 闭环路线图 |
| 2026-09-06 | #271 / [PR #272](http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/272) | `1896b33` | feat(platform): #271 新增公司平台只读接管基线 |
| 2026-09-07 | #270 / [PR #273](http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/273) | `a2dc131` | feat(platform): 独立 platform-bootstrap/v1 公司平台交付包 (#270) |
| 2026-09-08 | #274 / [PR #277](http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/277) | `a3ae327` | feat(platform): support digest-bound baseline profiles |
| 2026-09-08 | #275 / [PR #276](http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/276) | `874e716` | platform: 重新接入 SFMDigitalBoard（A- 轻接入，#252 的部分回滚） |
| 2026-09-08 | #278 / [PR #279](http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/279) | `de4581e` | fix(baseline): 兼容现场探针并提供只读诊断包 (#278) |
| 2026-09-10 | #280 / [PR #281](http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/281) | `27b3f1e` | feat(diagnostics): 区分协议字段与探针失败原因 |
| 2026-09-10 | #282 / [PR #283](http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/283) | `1164318` | fix(diagnostics): 兼容 UFW 策略和长目标列格式 |
| 2026-09-11 | #284 / [PR #285](http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/285) | `64f1cda` | architecture: 新增 linux-node-sqlite-v1 profile 并裁决 delivery_contract、版本 drift 与 migration Issue 语义 |
| 2026-09-11 | #290 / [PR #291](http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/291) | `a2f8854` | feat(release): 允许 scm-ci 承载 test 环境部署 |
| 2026-09-16 | #292 / [PR #295](http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/295) | `f0e3296` | docs(sync): supersede relay by native push mirror |
| 2026-09-16 | #293 / [PR #294](http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/294) | `2b5ac93` | docs(delivery): 对齐本机构建-离线交付合同（12-Windows §2、07 §1、runbook §4） |
| 2026-09-16 | #296 / [PR #297](http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/297) | `9a2fa11` | feat(release): 支持已验证的 Docker 28.1.1 classic 部署目标 |
| 2026-09-16 | #298 / [PR #300](http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/300) | `f6e2e50` | feat(loop): change worktree 单写者归属与推送归属闸门 |
| 2026-09-16 | #299 / [PR #302](http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/302) | `2667c3f` | decide(governance): #299 block_on_outdated_branch 分仓裁决——internal-application 关闭、平台仓保留，检查器以合并预览为前提 |
| 2026-09-16 | #301 / [PR #303](http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/303) | `e5ed35e` | test(#301): release evidence boundary 豁免 Python 字节码产物并隔离回归字节码 |
| 2026-09-16 | #304 / [PR #306](http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/306) | `803fd90` | docs(#304): 两台主机重装 broker 使 #298 worktree 归属闸门实际生效 |
| 2026-09-16 | #305 / [PR #307](http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/307) | `e1290d2` | fix(#305): migration receipt 以 migration identity 为唯一判据，release_id 只作审计 |
| 2026-09-18 | #309 / [PR #310](http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/310) | `95c0f19` | infra(#309): gitea-ci 预装 Flutter 3.32.8 与 unzip，并更正 01 §4.1/§4.2 as-built |
| 2026-09-19 | #312 / [PR #314](http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/314) | `3ff6972` | governance(#312): 同步 NewEMaint required contexts，并让 routine pilot 声明多 context |
| 2026-09-19 | #313 / [PR #315](http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/315) | `480d1d2` | security(#313): routine merger scope 合同补 read:user，修好 NewEMaint audit 的 403 |
| 2026-10-02 | #318 / [PR #321](http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/321) | `5c2cd72` | governance(skills): 修齐 Codex/Claude 会话与接入合同 (#318) |
| 2026-10-02 | #320 / [PR #322](http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/322) | `11c0410` | docs(governance): clarify per-push SHA anchors (#320) |
| 2026-10-02 | #287 / [PR #324](http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/324) | `14bfe6e` | fix(architecture): stabilize profile prose checksums with V2 locks (#287) |
| 2026-10-02 | #308 / [PR #326](http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/326) | `65268ee` | platform: add read-only drift checks for eight installer surfaces (#308) |
| 2026-10-02 | #288 / [PR #328](http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/328) | `bd1761d` | fix(architecture): enforce Dockerfile FROM digest contract (#288) |
| 2026-10-02 | #319 / [PR #323](http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/323) | `70baa35` | fix(ci): 修复 Bash 3.2 UTF-8 registry 预检误报 (#319) |
| 2026-10-03 | #289 / [PR #325](http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/325) | `16beee0` | fix: #289 统一 required_docs 声明与终态校验 |
| 2026-10-03 | #317 / [PR #331](http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/331) | `d647963` | fix: #317 阻止迁移后无兼容依据的旧镜像回退 |
| 2026-10-03 | #286 / [PR #330](http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/330) | `4020765` | feat(#286): 支持 manifest 限定跨仓 Issue 依赖 |
| 2026-10-03 | #311 / [PR #329](http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/329) | `ee5d2ce` | maintenance: #311 保留在用 node22 并补 unknown 来源记录 |
| 2026-10-03 | #316 / [PR #332](http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/332) | `dc9aa46` | feat(credentials): 增加受控、可恢复的服务账号 PAT 轮换 (#316) |

#292 已由原生 Push Mirror 路线取代，自研 relay 未交付；#268 路线图是历史项目规划，不写成公司现场进度。
#301/#319 是已合并测试/fixture 修复，不提升为业务部署证明。其它源码能力按 README 领域表与对应 Change 追溯。

## 验证记录

| 检查 | 结果 | 证据与限制 |
|---|---|---|
| exact main / open Issues / main protection | PASS | [脱敏 broker 回执](evidence/gitea-readback.json)；open #327/#333/#334；required `CI / verify (pull_request)`；direct/force push 禁止、merge allowlist admin |
| 本票单写者归属 | PASS | exact branch/worktree claim，session 01a104d6-3f9a-72c2-b4bc-6f5e9e03361a；原 sandbox metadata 写被拒后同一 narrow claim 经受控 host 成功 |
| 分类 apply/verify + approved | PASS | docs/small，projected；用户原请求授权纯文档实施；不授权 PR/merge/deploy |
| 本地链接/标题锚点 | PASS | [Markdown audit](evidence/markdown-audit.json)；外部 HTTP URL 未探测；三个 installation-layout references 已确认 source |
| semantic documents | PASS | [documents.log](evidence/documents.log)，changes=155，pass=2，gap=0；映射 summary/verification，严格 required_docs resolver 通过 |
| 既有文档/合同断言 | PASS | [targeted.log](evidence/targeted.log)，32 tests；architecture/company delivery/session/required-documents |
| 默认 locale 完整 smoke | PASS | [smoke receipt](evidence/smoke-receipt.json)，exit 0；1111 runtime tests / 132.925s，static smoke passed；[完整日志](evidence/smoke.log.gz)，总执行 424.754s |
| 范围与空白 | PASS | [scope review](evidence/scope-review.json)；10 份现有 Markdown 与本票新文档/evidence；不改 AGENTS/skills/runtime/scripts/CI/manifests/history；最终 staged diff --check 另行真实运行 |
| 本票 push / PR / required remote CI | NOT RUN | final PR 提交确认待取得；不把 local PASS 当 PR CI |
| installed / VM / credential / company / deploy | NOT RUN | 本票仅 source 文档修正，没有运行真实 installer、PAT 轮换、服务或部署验收 |

## 回滚与交付状态

只需 revert 本票文档 commit；没有现场文件或 Secret 变更需要恢复。
本票完成本地核对后进入 `AWAITING_PR_CONFIRMATION`（Policy manual）。确认提交后才进行 broker FF push、
创建唯一 PR、summary-only backfill 与 exact head CI 读回；manual 在 READY_FOR_REVIEW 等人合并。

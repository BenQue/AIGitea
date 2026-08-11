---
issue: 77
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/77
change_type: docs
requested_complexity: auto
assessed_complexity: small
effective_complexity: small
contract_effect: restore
reason: 将核心文档中的合并前候选状态和已退役运行态恢复为 protected-main 与最后一次 live 验证支持的当前表述，并把历史实施资料移出核心入口
risk_flags: []
required_docs:
  - summary
documents:
  summary: summary-refresh-core-docs-260811.md
confidence: high
override_reason: ''
depends_on: []
status: ready-for-review
branch: change/77-refresh-core-docs
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/78
created: 2026-08-11
updated: 2026-08-11
---

## 问题/需求总结

protected `main@374d672a7af8c2f9a7974953a9dc3fae415c6706` 已包含 Issue
#21/#35/#57/#61/#73/#75 的合并结果，但核心文档仍混用这些 Change 的合并前状态：
Issue #21 的业务 runtime 和 `prod-sim` 已完成收口，01/02/06/07 仍把它们写成当前迁移或退役候选；
Issue #35 的 manager/project-agent 与仓库策略已经 live reconciliation，01 仍写作 `NOT RUN`；
Issue #57/#73/#75 已合并，README、03/04/06/08 仍称 source candidate 或等待最终 PR。

根目录的 10、11 已是完成后的实施记录，不再承担当前操作合同；v2 一页 PDF 创建于
2026-07-11，仍描述三道硬闸门、`prod-sim` 和 `gitea-ci` 同机业务 runtime。继续把这些文件放在
核心入口，会让历史状态看起来像当前状态。

## 影响范围

- 更新 README 与 01/02/03/04/05/06/07/08 的状态、导航和日常操作表述。
- 复核 09、12–15、`architecture/README.md`、`docker-release/README.md` 的设计/证据边界；只修正
  当前入口，不把 `NOT RUN` 的公司内网、Windows、production 或业务 Docker 部署写成完成。
- 将 10、11 和 v2 PDF 移入 `archive/`，新增 archive 导航；不批量改写历史 Change 文档。
- `.gitignore` 忽略 `.DS_Store`，并精确清理 canonical checkout 中已盘点的 4 个未跟踪实例。

## 初步方案与建议

核心分册统一采用三层事实：`protected-main source` 只说明版本库合同，`last live verification` 只说明
带时间戳的真实环境证据，未执行的业务环境/生产门禁继续写 `NOT RUN`。合并前的候选状态保留在对应
`docs/changes/*/verification*.md`，不再复制到 README 或日常运维命令。

历史资料使用 `git mv` 进入 `archive/`，保留 Git 可恢复性；`archive/README.md` 明确这些资料不得
作为当前配置、命令或 live 状态来源。当前导航链接更新到 archive，历史 Change 文件保持审计原样。

## 风险

- 把 PR 合并误写成部署会扩大事实；修订必须保留 `completed`、`deployed`、`NOT RUN` 的区别。
- 把设计中的 `candidate` 一律删除会损坏语义；只清理已经被合并/退役证据推翻的状态词，架构候选和
  GitHub source candidate 等领域术语继续保留。
- 批量改写历史 Change 会破坏当时证据；仅更新当前核心入口和 archive 导航。
- `.DS_Store` 清理只允许四个已盘点的 exact path，不使用仓库级递归删除。

## AI 判级

```yaml
change_type: docs
requested_complexity: auto
assessed_complexity: small
effective_complexity: small
contract_effect: restore
reason: 将核心文档中的合并前候选状态和已退役运行态恢复为 protected-main 与最后一次 live 验证支持的当前表述，并把历史实施资料移出核心入口
risk_flags: []
required_docs:
  - summary
confidence: high
override_reason: ''
```

### 判级证据

- 只修改文档、导航与忽略规则，不改变外部行为、平台合同、Agent、CI、部署脚本或权限。
- 目标是恢复与已合并 source 和既有 live verification 的一致性，改动可由单一 PR 简单 revert。
- Issue #77 已给出明确范围、验收标准和禁止边界，无需新增 spec/plan 决策。

### 缺失的 acceptance criteria 或决策

无。

## 验收结果

| 检查项 | 结果 | 证据与边界 |
|---|---|---|
| protected-main 与 live 基线只读核对 | PASS | `origin/main@374d672a7af8c2f9a7974953a9dc3fae415c6706`；通过项目 broker 只读核对 Issue #21/#35/#57/#61/#73/#75 与开放 PR。Issue #61 仍残留 `pr-open` 标签，属于 Gitea 外部元数据漂移，未在本次文档 PR 中越权修改 |
| 核心文档相对链接 | PASS | 扫描 19 份核心、归档入口和本 Change 文档，共 82 个相对链接，缺失 0 |
| 已知过时状态定向扫描 | PASS | `readable change-name contract candidate`、`Issue #73 candidate`、等待最终 PR、旧 `gitea-ci:8091` 待迁移、旧 `ci-bot` 保持等模式 0 命中 |
| Secret 形态扫描 | PASS | 对本次修改/新增的 Markdown 进行常见 token、PAT、AWS、Google API、JWT 形态扫描，0 命中 |
| Change 命名与文档解析 | PASS | `change-name 77 refresh-core-docs` 返回 `change/77-refresh-core-docs`；`resolve-documents --repo . 77` 只解析出本 summary，符合 small Change 合同 |
| Markdown/Git 差异格式 | PASS | `git diff --check` 无输出 |
| 平台 smoke | PASS | 首次运行因仓库既有 Issue #65 evidence checkout mode 为 `0644`、测试期望 `0444` 而 FAIL；仅在复跑期间将该文件临时规范为 `0444`，`bash codex/tests/smoke.sh` 通过 325 个测试和静态检查，随后恢复 `0644` 并确认该文件无差异 |
| 归档 PDF 完整性与内容复核 | PASS | 移动后 SHA-256 仍为 `b0b09ed8ebf11d69ca2ba6284442d0d498397d928e1bc29394b9d89d0aac7cfb`；已渲染检查其 v2/三闸门/旧 runtime 内容，适合归档、不适合继续作为当前入口 |
| canonical checkout 精确清理 | PASS | 仅删除盘点出的 4 个未跟踪 `.DS_Store`，并确认 canonical checkout 不再有未跟踪文件；未递归删除其他路径 |
| Registry、AppServer、数据库、真实部署与生产验收 | NOT RUN | 本 Change 仅做文档一致性和可恢复归档，不授权或执行环境 mutation |
| PR、远端 CI、人工合并 | NOT CONFIGURED / NOT RUN | PR #78 已创建且保持 `open`；`main` 保护规则为 `enable_status_check=false`、`status_check_contexts=[]`，head status 为 `total_count=0`/`pending`，因此不能声称 CI 通过；人工合并未执行 |

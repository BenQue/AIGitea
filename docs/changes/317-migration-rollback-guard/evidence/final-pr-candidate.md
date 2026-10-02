# #317 唯一最终 manual PR 候选

标题：`fix: #317 阻止迁移后无兼容依据的旧镜像回退`

Issue：#317；branch：`change/317-migration-rollback-guard`；base：`main`；policy：`manual`。
Source 验证 SHA：`ed37445c9986fbff2aaac747ad41457da2a622ef`；最新整合 main：`16beee09aefe89b5bc80a31544c59d456190ea32`。
正文：`final-pr-body.md`；本文件所在最终本地 HEAD 由独立 `/private/tmp/issue-317-final-candidate.json`
在提交后绑定，避免自引用 SHA。验证 SHA 保持真实执行点；后续仅本票证据/语义文档变更。

## 当前硬门与授权边界

- AC-01–13 source/local PASS；最新默认 UTF-8 完整 smoke 1057 runtime / 197 release，26 boundary，23 temporary installed fixture。
- Standards 0硬/0 heuristic、Spec 0 findings；严格 mapped docs 检查 PASS。
- Live classification projected：bugfix/complex；Issue open+approved；#317 对应 PR=[]；owner last_push_head=null。
- required CI：`CI / verify (pull_request)`；routine disabled；main 不可 push/force，manual 人工合并。
- 本地状态 `AWAITING_PR_CONFIRMATION`；Controller projection `NOT_WRITTEN`。本文件不是批准回执。
- PR CI、真实 E2E/installed/company-live/应用消费 NOT RUN；没有新的 merged SHA。

## 请求的最终确认

批准 #317 / change/317-migration-rollback-guard / manual 的唯一最终 PR 提交；确认后只经
manifest project broker 发布本人 exact 分支、读回 pushed_head、创建唯一 `Closes #317` PR，
回填实际 pr_url 并跟踪 required CI，合同内 CI 修复可继续，然后停在 `READY_FOR_REVIEW`，由人合并。
不得 force 更新既有远端历史、绕过 broker 或允许硬门失败 fallback；publication 冲突需停止读回。
本确认不包含 merge、安装、部署、凭据/grant 或应用 pin 更新。

确认门来自仓库 AGENTS.md 的最终 PR 提交规则及 aisoft-matt-workflow §Per-Issue flow 6，
不是重新请求已批准的产品合同/两文件范围。

## 2026-10-03 最终提交确认

用户在拥有本票的聊天直接回复“确认提交”，现已取得上文精确 Issue/branch/manual 的最终提交授权。
真实 receipt：`pr-submission-confirmation.json`。上文候选与批准前状态保留为送审快照；
后续只沿用此授权完成唯一 PR 与范围内 CI 修复，最终停 READY_FOR_REVIEW，由人合并。

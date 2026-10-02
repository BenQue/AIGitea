# #288 唯一最终 PR 候选

Issue: #288
Branch: change/288-dockerfile-digest
Policy: manual
状态: AWAITING_PR_CONFIRMATION
精确最终 candidate head：独立文档 commit 后写入 /private/tmp/issue-288-contract-data/loop-state/issues/288.json 的 candidate_head_sha；文件自身不自引用 commit SHA。

source 验证 head: 1507e358319ebfc2206fe0402ce1520f3392a246
pinned main: 65268ee5f1e622c486fd9e354dd35e20a2900f91

本地完整 runtime 1008 tests /101.684s PASS；完整 host smoke PASS，
含 installed-drift fixture 23 tests /44.320s 和 runtime 1008 tests /101.989s。
非容器四合同 × V1/V2 八组 canonical bytes 与 pinned main 一致；批准 hashes/static/docs/分类读回 PASS。
Standards hard 0 / nonblocking smell 1；Spec findings 0。
判级: bugfix / complex，exact #288 两维度 projected。routine disabled。

PR 草稿：final-pr-draft.json 与 final-pr-body.md；恰有一行 Closes #288。
未执行：push、PR/required CI、actual installation、application migration、builder provenance、现场、部署。

请确认提交唯一最终 PR。确认绑定 exact Issue #288、change/288-dockerfile-digest 与 manual policy。
确认后可继续当前合同内的 PR CI 修复；required CI 全绿后停在 READY_FOR_REVIEW，
等待人工审核并合并。部署不在本次授权内。

# Code review：#320

固定范围：5c2cd726c9aeaee9d17541d8feb049e33881bbac...05e555d441dc8db871454f1e67ce197e1d071eea。按 code-review 技能以两个独立只读代理执行，未改文件或访问 Gitea。

## Standards

review_standards：未发现阻塞违反项，也无需要提出的 Fowler smell 建议。

- 命名统一为 320-push-head-anchor，summary 显式映射四个语义角色。
- 六份治理指导均在 spec 的明确授权范围内；diff 未涉及 AGENTS.md、runtime、tests、CI 或部署脚本。
- session skill 保留首次候选比较；合法后续 push 要求 fresh 验证与读回，未知改写、范围扩大、不匹配停止；授权仍绑定 Issue/branch/policy。
- T01 收据与 plan 明确独立应用后停止；verification 未把 source/local 证据扩大为现场成功。
- 六处相似文字属于双 provider 及入口指导同步要求，不作为 Duplicated Code/Shotgun Surgery 建议。

## Spec

review_spec：PASS，0 项发现。

- T01 治理实现未发现遗漏。AC-1/2 的首次候选锚、后续 fresh head、授权绑定、停止条件及禁止自动接受未知 head 已完整表达（Codex session skill 46–56 行、Claude 35–42 行）。
- 未发现范围外变化；仅六份治理指导及本 Issue 合同/提案/证据，未改 runtime、tests 或 AGENTS。
- 03、08、两侧 session 与复合 skill 在首次 push、summary-only 回填、合同内 CI 修复及他人改写上的规则一致；实际 URL/status、mapped-summary-only diff 与文档检查完整。
- T02 收据由本会话续办；审查不推定 live、installed 或 CI 成功。

两轴分别 0 项发现；两轴均无阻塞项。此报告不代替测试、live 标签读回或最终 PR 确认。

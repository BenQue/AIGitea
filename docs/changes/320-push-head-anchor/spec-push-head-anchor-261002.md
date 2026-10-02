---
issue: 320
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/320
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
confidence: high
risk_flags:
  - agent-governance
  - platform-governance
depends_on: []
status: approved
branch: change/320-push-head-anchor
created: 2026-10-02
updated: 2026-10-02
---

# Spec：区分每次 push 的 SHA 比较锚

## 目标与原因

修正首次提交 push 与合法后续 push 共用旧 SHA 的治理措辞。只澄清既有 exact Issue/branch/policy 授权与每次验证纪律，不改变 broker、Controller、CLI 或产品行为。

## Acceptance criteria

- [x] AC-1：首次 push 的 `pushed_head` 等于提交确认候选中已验证的 exact head；PR summary-only 回填与范围内 CI 修复的每次后续 push，等于该次 fresh 本地验证并记录的 exact head，不沿用首次旧 SHA，也不省略比较。
- [x] AC-2：授权仍绑定 exact Issue/branch/manual policy；不新增每 commit 确认。后续 push 前核对本会话归属、exact branch、新增 diff 的合同范围、必要验证与清洁工作树，记录 40 位 lowercase head。意外改写、scope 扩大或 `pushed_head` 不匹配立即停止，查明原因后才能继续；不得简单把未知 head 当作新锚。
- [x] AC-3：03、08、两侧 session skill 与两侧复合 skill 的 PR 路径等价；覆盖首次 push、summary-only 回填、in-contract CI 修复、他人改写四类场景，并验证复用旧 head、漏比对、越范围与身份异常的负向案例。
- [x] AC-4：source/local/CI/installed/real-model/live 分层报告；合成场景 PASS 不推定 remote push、真实模型、安装或部署成功。
- [x] AC-5：治理源仅由独立 T01 受控步骤应用并停止；fresh run 重新读取合同后才能执行 T02 验证/候选准备。当前 AGENTS.md、runtime 与其它 Issue 均不修改。

## 精确授权目标（合同确认后生效）

- `03-Issue-Spec-Plan与单闸门开发流程.md`
- `08-双工具共存与实施.md`
- `codex/skills/issue-session-flow/SKILL.md`
- `skill-for-claude/issue-session-flow/SKILL.md`
- `skill-for-codex/SKILL.md`
- `skill-for-claude/aisoft-platform/SKILL.md`

仅上述六份治理文案和本 Issue 映射文档/提案/验证证据获授权。可审阅候选为 `proposals/push-head-anchor.patch.gz`。不得借验证结果改变 AC 或扩大范围。

## 实现决策

- 首次 push 必须仍比对已验证候选；若候选 head 在确认后发生变化，先停止并更新候选验证证据，不借后续 push 规则绕过首次纪律。
- PR 回填仅允许实际 PR URL 和 status 的 mapped summary-only commit；先 check-change-documents、审查唯一文件 diff、记录新 head，再 broker push 和读回。Controller 自动路径与 Mac 显式路径使用同一比较原则。
- 范围内 CI 修复验证必要测试、final diff 与 head，沿用已取得的提交授权；不把每次合法 head 前进等同于他人改写，也不把任意 head 前进视为合法。
- `previous_head` 只作最近 push 的审计信息，不取代本次验证锚；routine final-head hard gates 保持原合同。

## 用户故事与验证决策

1. 作为 Issue 会话写者，我需要首次 push 证明提交的是已核验候选。
2. 作为 PR 创建方，我需要合法 summary-only 回填产生的新 head 可验证并读回。
3. 作为 CI 修复方，我需要合同内追加 commit 继续执行既有授权，同时保留每次验证。
4. 作为 reviewer，我需要未知改写与漏校验被停止，并看清 synthetic 与 live 的边界。

验证采用治理全文 review、可审阅 patch apply-check、四场景桌面推演及负向矩阵；实施后运行既有 SessionContractTests、provider parity 与完整 smoke。不新增或修改 runtime/test 源文件。既有 test 如果与澄清后的语义冲突，记录阻塞并提出独立授权建议，不削弱测试。

## 接口、数据与兼容性影响

无 schema/API/CLI/runtime 更改。保留现行 branch 命名、单写者 claim、broker typed 操作、两确认点、required CI、人工合并与部署边界。

## 风险与回滚约束

治理源修改可通过本 Issue 的原子 commit revert 并经新 PR 回滚；未合并提案可丢弃且不影响 stable source。安装/全局技能更新未授权；source merge 不等于 installed 生效。

## 非目标

不改 AGENTS.md/CLAUDE.md、runtime（含 tests）、controller、CI/installer/部署脚本、权限/凭据、broker 安装、live provider/timer，不处理其它 Issue，不执行 merge 或部署。真实模型与 remote 事件场景本轮不模拟成 live PASS。

## 未决问题

技术方案无未决；用户已确认本完整合同与 T01/T02 breakdown。最终 PR 提交另有绑定 #320/branch/manual 的确认点。

## 当前验收层次

AC-1至AC-5的治理 source/local 验证已完成，证据见 mapped verification；实际首次push/PR #322与summary-only回填push已执行并读回；最终head required CI pending，真实CI repair、真实模型、installed/live、人工合并、终态与归档仍 NOT RUN。本次勾选不表示真实远端事件或交付已完成。

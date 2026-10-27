# 执行视图与候选审查适配

本合同承接同一 Issue 的路由、Txx 执行与审查范围；不创建另一套编排、批准或完成状态。
provider 的具体技能只从 [route-policy](route-policy.md) 展开。Codex、Claude、Cursor 共用本合同，
上游 vendor 保持原文，执行由一个 claimed worktree 的唯一写者负责。

## 入口与能力边界

以下是平台本地适配接口合同，命令是否可用必须由实际 runtime 验证；文档存在、source 校验通过
或安装了技能都不证明命令已经实现。缺命令/消费者不支持时报告 GAP，不伪造执行回执或静默跳过。

```text
aisoft resolve-route N --provider codex|claude|cursor --repo <checkout>
aisoft prepare-ticket N Txx --provider codex|claude|cursor [--resume] --repo <checkout>
aisoft review-candidate N Txx --head <40位SHA> --repo <checkout>
```

- `resolve-route`：读取 exact Issue 的映射 summary 与仓库 change_control，输出显式 provider、八键 route、
  命中规则与 policy 字节 SHA256。只输出具体技能；未知 provider、冲突或未展开义务明确失败。
- `prepare-ticket`：复核 approved 合同、exact branch/owner、frontier 和计划身份，生成本地执行视图与开始回执。
  `--resume` 校验已有回执、语义摘要、提交和验证证据，不凭 complete 文本跳票。
- `review-candidate`：从开始回执取 ticket_base，以指定的当前 HEAD 校验候选，输出固定范围包及需处理的遗漏。
  它不生成审查 PASS；两轴与会话仍须审查实际内容。
- 正常成功返回可审计的结构化产物；缺输入、无效身份、规则/范围不完整时非零退出并写具体原因。
  失败不推进 ticket/Issue 状态。所有 SHA 固定为完整 lowercase 40 位 Git commit id，内容摘要用 SHA256。
- helper 只读取 Git/合同，写当前 worktree 的本地缓存/派生物；不 add、commit、stash、reset、push、
  执行任意测试命令、改标签、开 PR、merge、安装或操作真实 HOME。远端读写继续使用当前来源的 typed 操作入口：项目来源是 `aisoft-access`，站点来源是 broker（ADR 0003）。

## Txx 与执行视图

production complex 的唯一任务合同是映射 plan：Ticket graph + 每票 Txx 正文。每票必须包含交付/范围、
blocked_by、AC、验证命令与 Expected、共享接口/全局约束及停止条件。图与正文不一致、缺正文、重复 ID、
未知依赖或依赖环都不能启动。匹配完整 ID，不把 T01 当 T010 前缀，也不把代码围栏中的伪标题当任务。

SP 的 Task N 只是从 canonical Txx 生成的可再生视图，保留原 Txx 与全部约束。
不能把映射 Txx plan 直接传给只识 Task N 的上游脚本，也不能人工维护第二份 plan。
Matt 继续接收 exact Issue/Txx 与所需合同路径。development complex 使用 Issue AC 与合成 T01；
small 按 small-direct 执行，不因这些接口增加 spec、票图或双轴审查。

平台派生视图/回执放在 `.superpowers/aisoft/<Issue>/`，原版 SP scratch 放在
`.superpowers/sdd/<派生plan-basename>/`。派生 basename 带 Issue、owner 和语义摘要的稳定标识；
两处都须核对 exact worktree、owner、plan-path 和已登记归属，拒绝路径逃逸、符号链接、
碰撞或覆盖别会话内容。只有必要证据已写回映射 verification 或现有 plan/summary，才允许清理自己登记的临时目录。
不得修改 vendor 来改变输出位置。缓存不是跨会话审查数据库，也不是授权事实源。

## 开始、摘要与恢复

开始前先记录：Issue/Txx、provider/实际技能来源及 pin、exact branch/owner、plan 路径、
原始全文 SHA256、任务语义 SHA256、ticket_base、起始 staged/unstaged/untracked 状态与授权范围。
整批另记 change_base，绝不从最后一票推导。没有可信开始前 BASE 时不能用 HEAD~1 代补。

语义摘要覆盖 Issue/branch、全局约束、完整 Ticket ID/依赖、交付/范围、AC、验证命令/Expected、
接口与停止条件；只排除 Ticket graph 的 Status 单元、updated 时间，以及由成对标记
`<!-- execution-evidence:start -->` / `<!-- execution-evidence:end -->` 包围的执行证据区。
标记必须成对、唯一、不可嵌套，且不得包住任务图、任务正文或约束；恶意标记不能隐藏语义变更。
不得按任意标题或词语启发式删段。旧格式不能无损解析时明确报告缺口，不自行编造任务正文。
原始全文摘要用于审计，不拿正常 Status/补证变化误判任务变更。无正式 plan 时规范化 Issue AC 与约束。

每次只选依赖已完成且验证证据齐全的 frontier。恢复时重新核对身份、语义摘要、BASE 祖先关系、
实际提交和验证结果；普通补证/合法状态推进可恢复，语义变更不能静默沿用原回执。
只有测试命令成功或 SP task-done 写 complete 不够：必要 AC/验证 FAIL、NOT RUN 或关联提交不清，均不能标完成。
任务图状态、缓存和真实证据不一致时保留事实并报告原因，不丢弃原有记录。

## Matt 候选与双轴审查

仅对使用 Matt implement/code-review 的执行单元采用下列顺序；不把它扩成 small 或 SP 的每票新义务：

1. 实现前记录 ticket_base 与起始状态。
2. 实现并运行合同要求的验证；唯一写者只提交本票改动，可有多笔线性 commit。
3. 固定 candidate_head，核对 branch/owner 与当前 HEAD。BASE 必须可解析且为 HEAD 祖先，
   全部本票 commit 在 BASE..HEAD 内，净 diff 非空。空净 diff 必须拒绝候选，不派审，也不得记为 PASS。
4. 检查相关 staged/unstaged/untracked 是否遗漏；结合起始状态、AC/范围与实际 diff 判定。
   既有无关文件保留；同一脏文件被本票继续修改、范围外真实改动或归属不明均需明确处置。
   必要 ignored 成果不能因 ignore 自动豁免。不得自动 add/stash/delete 无关用户文件。
5. Standards 与 Spec 两轴接收同一固定 BASE/HEAD、commit 清单、合同与规范来源。
   BASE 已为 HEAD 祖先时，上游 three-dot 比较与该固定范围一致；不能在执行中让符号 HEAD 漂移。
6. 修复后重新验证、追加 commit，记录 findings 的 fixed/residual/new，再按现合同复核新 HEAD。
   HEAD、branch、owner 改变时，旧 PASS 不代表当前候选；不可通过重写历史保留旧结论。

机器只证明祖先、净 diff、状态与身份等确定性条件。文件路径白名单不能证明语义归属，
它也不能证明编辑器未保存内容不存在。候选包须区分“机械检查已通过”与“范围归属仍需审查”，
不能把未知项写成完整。

## 逐票与整批审查

每票审查不自动等于最终整批审查。全部票完成后使用 change_base 覆盖第一票到最终 HEAD，
核对整个合同、AC 和跨票影响。平台 complex 最终仍由未参与实现的另一 provider 只读审查实际候选 HEAD；
FAIL 修复后按平台合同复核新 HEAD，此规则优先于 SP 的“一次修复后不再 review”。
项目仓依自己的已批准合同执行，不把平台 cross-provider gate 外推所有项目。
已有一次审查真正覆盖同一范围/职责时复用证据，不为了技能名字再叠加同义轮次。

SP 的自主裁决、completion 文本、临时目录清理或 finishing 菜单均不能替代平台授权/证据：
合同冲突按既有升级规则处理；重要裁决、驳回/延期的 finding 必须可见；
清理前保全证据；仍停在 AWAITING_PR_CONFIRMATION，确认点 2 后远端只走当前来源的 typed 操作入口，人合并。

## 持久证据与治理交接

复用既有 summary/plan/verification 串起 AC → Txx → 测试边界/实际结果 → commit → review/finding。
记录实际模型、调用配置强度、provider/技能来源、上下文及 BASE/HEAD；实际结果与计划分开，
source/local、CI、installed、真实 provider session、live 分开。未执行是 NOT RUN，不能用 fixture 代替现场采用。

治理文件必须由获批 complex 合同的独立受控步骤应用，commit 后停止。
fresh run 重读批准合同、治理 diff、当前规则、exact worktree/owner/HEAD 后继续。
原批准在合同内持续有效，fresh run、ticket、测试、普通修复、本地 commit 都不是新的人工确认点。
只有现有合同/启动和最终 PR 前两个确认点；merge 与部署权限边界不变。

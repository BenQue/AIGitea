# #317 installed-drift fixture 精确修订提案（未批准、未应用）

## 当前已完成与新阻塞

固定实现 head：`31e4f8592e178583c3b3be771e8d5c2f03173bd6`；fresh main：
`65268ee5f1e622c486fd9e354dd35e20a2900f91`，本票 branch/worktree/session/manual 不变。
原批准 T05 两文件实现已通过26项边界测试、完整 checker的197项release测试、历史快照回归及
两轴源码review。固定historical evidence、source身份/cache隔离保持；真实Docker/DB/安装/现场NOT_RUN。

整合新main的#308 smoke fixture后，`bash codex/tests/smoke.sh`真实exit=1：
`test-installed-drift.sh`的23 tests产生16 failures。八个临时安装row均PASS；真实PR的managed
source与cached origin/main有合法差异，public checker按已发布合同返回source GAP与exit=1，
fixture正例仍要求整体exit=0。此为fixture使用真实PR checkout作正例baseline的集成问题，
不是sandbox访问或release guard错误。后续smoke步骤NOT_RUN，不能申请最终PR提交。

当前spec授权新实现只包括checker/test两个精确文件，尚不包括下面第三个测试文件。
依据AGENTS“遇到合同冲突、范围扩张…必须停止并升级给人”，本票T05/T03保持pending。
不修改approved spec，不修改当前fixture，不重试同一已确认根因制造假绿。

## 备选的唯一额外实现范围（当前不重复请求批准）

只新增 `codex/tests/fixtures/installed-drift/test-installed-drift.py` 到本票test allowlist。
原文件SHA256：`fcda29eeaf0ebbb27ff53c855128309f0f8901d5d9c7bbbc55e934dd606dc984`。
具体待应用diff：`installed-drift-fixture-proposal.patch`，SHA256：`ed4c93e7d1efa047ee512ea261f91642ceb262eecea843175e38848ed8c36eda`。
本提案是待批准材料，不是新的治理事实源；原批准范围与所有旧evidence继续有效。

- 八个real installer仍仅在外部temp生成fixture安装树。
- 正例的source参数改用外部temp中当前repository data的副本；只在该临时副本初始化Git和
  固定fixture ref。该ref仅标识合成fixture bytes，不代表真实remote main或已发布版本。
- public CHECKER仍来自本票真实source；不mock成功、不改返回码、不改source-only/installed语义。
- 真实checkout的origin/main、HEAD、claim、remote、credential与host安装均不改。
- 新增隔离测试并保持所有原负例，尤其valid pending PR产生source GAP、installed非零，
  source-only不读取目标安装树。remote_freshness继续EXTERNAL_EVIDENCE_REQUIRED。
- 不新增目录/content豁免，不修改check-installed-drift.py/shell wrapper、smoke.sh、CI、installer、
  broker、AGENTS/CLAUDE、state/schema/runtime/API，也不更新任何应用pin。

## 可审阅草案的实际验证

未应用candidate脚本位于 `/private/tmp/issue-317-installed-fixture-candidate.py`；
命令 `python3 -B /private/tmp/issue-317-installed-fixture-candidate.py /private/tmp/issue-317-migration-rollback-guard`
在独立树外bytecode cache中实际通过24 tests，exit=0；日志为`installed-drift-draft-test.log.gz`。
原fixture bytes与fresh main完全一致，真实origin/main/HEAD/claim未改变。
这只是未应用草案的fixture试验；完整smoke仍FAIL，不表示本机installed/live通过。

Spec提案边界review 0 findings；Standards 0硬违反、1项不阻塞的possible Duplicated Code建议，
与文件中已有fixture Git setup形式一致。保留最小改动，未为维护性建议扩大修订范围。
审查记录见`review-t05.md`。

## 批准后步骤与权限

批准绑定#317 / change/317-migration-rollback-guard / manual及上述精确单测试文件diff。
先以独立、纯合同步骤补映射spec/plan及必要versioned contract，记录真实hash并停止；
后续fresh run重新读取合同，再实施该test修订、完整smoke、所有必要回归与两轴review。
T05/T03仅在全部hard gates实际通过后结项，随后请求唯一最终manual PR提交确认。

本次只请求修订实施范围。仍不授权push/PR/merge/install/deploy、真实DB迁移、操作现场，
不改broker解锁，不lease-force改写已发布branch。#327独立治理工作不并入本票。

## 去重后的当前交接

本提案完成后，调度提供#288已有独立治理的同根因fixture修订。只读实际patch及SHA核对见
`t05-upstream-fixture-reference.json`。当前优先等待该独立治理结果进入main，再fresh整合，
暂不重复请求本票扩范围。本draft保留为可审阅备选，未经#317精确授权不应用。
远端读回#288 open、当前#288/#317无实际PR；尚未存在的PR不加入hard depends_on。
不继承#288批准或将其测试变成本票PASS，完整smoke仍FAIL。当前local handoff为
BLOCKED_EXTERNAL（非Controller投影），若上游迟迟不可用再由负责人裁决备选范围。

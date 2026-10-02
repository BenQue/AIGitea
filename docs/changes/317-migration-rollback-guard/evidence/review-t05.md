# #317 T05 两轴审查与未应用fixture提案

固定点：`65268ee5f1e622c486fd9e354dd35e20a2900f91`；实现head：
`31e4f8592e178583c3b3be771e8d5c2f03173bd6`。
命令：`git diff 65268ee5f1e622c486fd9e354dd35e20a2900f91...31e4f8592e178583c3b3be771e8d5c2f03173bd6`。
原reviewer并行只读复核，未编辑或执行测试。

## Standards

0硬标准违反、0 heuristic smell。精确两文件范围、历史constants与evidence不变、5个fixed
mode/hash additions、disk/index拒绝、无override、source identity与树外cache均保持。
既有T02/T04审查集成未发现冲突；完整smoke结果由主会话真实命令单独记录。

## Spec

0 findings。AC11–13的source checker实现、exact scope/hash/mode和negative cases落实；
7个existing pins与5 additions的HEAD实算SHA匹配。未扩runtime/broker/smoke/CI范围。
真实E2E/installed/company_live保留NOT_RUN；review不代表完整smoke已通过。

两轴源码总计0/0 findings。主会话随后读回完整smoke FAIL：新#308 fixture baseline假设冲突，
T05/T03仍pending，非源码review未解决finding。

## 新fixture提案的只读审查（未批准、未应用）

Spec 0 findings：仅单test文件，独立外部temp source Git baseline，真实checkout/ref/claim不改；
CLI仍实际public checker，原valid pending PR source GAP/installed非零负例保持，无硬门遮盖。
草案24 tests OK仅为candidate局部试验。

Standards 0硬违反、1项possible Duplicated Code：新增init/add/commit/update-ref与原文件3处
fixture setup相似，可考虑共享helper。属维护性建议，不阻塞合同批准；当前优先最小修订。
未修改public checker或真实fixture，未伪造real main/installed事实，原负例保持。

提案两轴总计Standards 0硬违反+1不阻塞heuristic；Spec 0 findings。
完整smoke FAIL不被草案试验替代；单文件scope批准尚待用户。

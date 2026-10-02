# #317 T04 纯治理合同两轴审查

固定 base：32b0ee524ef5ae46f986498f6c617e8e5ce8cadf。
应用 head：c183a4d0acba74f14af8124661b252f43d1b33a1。
依据 code-review skill，两个原 reviewer 并行只读复核；未委派编辑、运行 Docker 或远端写入。

## Standards

PASS，0项硬性违反、0项heuristic smell。只修改versioned合同与本票记录；checker/runtime/tests/schema
和历史evidence未改。批准receipt的proposal/prior-spec hash与固定点一致，tuple/manual保持。
13条AC映射与frontier=T05一致；T04停止/T05 fresh-run边界、历史190-test PASS/smoke FAIL和
本轮NOT RUN区分清楚。新增授权只包含两文件及固定path/hash/mode，没有扩大豁免或跳过硬门。

## Spec

PASS，0项发现。批准的提案约束完整落入spec/plan/versioned contract：历史常量/evidence与
transport/matrix原pin保持、4个existing allowed、5个exact additions、disk/index bytes/mode、
failclosed且无override。T04只应用合同并停止，T05尚未实施，T03 pending；无scopecreep。
原proposal bytes保留；source snapshot 10项hash实算匹配。reviewer未运行runtime/smoke/Docker。

本次review通过仅证明T04合同应用符合批准，不表示T05或最终PR门禁通过。

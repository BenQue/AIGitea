# ADR-0001：V1 采用 strict JSON canonical contract

- 状态：Accepted
- 日期：2026-08-02
- 关联：Issue #23

V1 catalog、profile、project declaration 和 lock 统一采用 strict JSON 与 JSON Schema
2020-12。Reader 拒绝 duplicate keys、NaN/Infinity、float、unknown fields 和 YAML 路径；
canonical writer 使用 UTF-8、sorted keys、无多余空白并以单个换行结束。

选择原因是当前 runtime 必须 stdlib-only、离线可运行。引入 YAML 会带来未治理 parser、隐式
类型和 canonicalization 差异。未来支持 YAML 必须另建 Change，固定 parser/version、别名和
类型规则，并证明与 JSON lock byte identity，不得在 V1 静默选择两个事实源。

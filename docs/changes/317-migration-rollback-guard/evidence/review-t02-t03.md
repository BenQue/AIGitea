# #317 T02/T03 两轴审查回执

- 起始固定 base：`5c2cd726c9aeaee9d17541d8feb049e33881bbac`。
- 首轮 candidate：`f1c3a01249f2b870172d402477fca2a773e1c146`。
- 修复 candidate/source head：`233a0d6fb94ce380e1418f892ef8ff5d093099e2`。
- 按 code-review skill 的 Standards/Spec 独立只读 subagents 并行审查；没有委派实施、远端写入或 Docker 操作。

## Standards

首次发现1项硬性 P1：`rollback_compatibility.py` 从 profile pathname 重取 owner，未绑定已验证
profile inode。旧实现的替换回归真实失败：没有拒绝 other-owner evidence，旧镜像可启动。

修复：profile 内容与 UID 同 FD protected read/open/fstat 获得；有界读取前后验证 inode、
size/mtime/ctime 和 named inode；依据仅使用捕获 UID，缺失 fail closed。profile JSON 不能注入此 UID。
增加验证后替换 owner 与 protection-check/open 间不安全 mode 替换两项 public API 回归。
原 Standards reviewer 对修复 commit 只读复核 PASS，未发现新增问题；0 heuristic smell。

## Spec

首次未发现新增实现缺陷或 scope creep。DB cursor 与 completed receipt 分离、#305 no-op、四类
旧启动路径、strict evidence、失败 code/state/CLI、consumer 与 source/live 边界满足批准合同。

原 Spec reviewer 对 owner 修复只读复核 PASS：在 contract.py parser、compatibility 和安全 tests
allowlist 内，无新增 scope creep。

## 验证与剩余 blocker

190 release tests PASS（真实命令与 source hash 在 release-suite.json）；reviewer 没有重跑，不能
把只读复核当作测试。首轮完整 smoke FAIL，修复后完整 smoke NOT RUN：固定 evidence checker
拒绝新增 source 集合；没有修改或绕过。此治理范围未批准，T03 最终验收 pending。
修订草案 governance-amendment-proposal.md 是提案，不是授权。

当前真实 Docker/DB、PR CI、installed/live、消费项目 pin/集成均 NOT RUN。

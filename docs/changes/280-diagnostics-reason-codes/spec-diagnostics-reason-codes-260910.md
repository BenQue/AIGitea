---
issue: 280
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/280
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - external-contract
  - security
  - deployment
depends_on: []
status: approved
branch: change/280-diagnostics-reason-codes
created: 2026-09-10
updated: 2026-09-10
---

# Diagnostics reason codes 合同

## 目标与原因

使脱敏 diagnostics 能区分已知失败阶段，而不暴露配置、UFW 规则或任意异常文本。
基线 v1 collector 为 732c4a871c6ecdb77285f3fcc7d31e20b27cf353ab75b4f368ee3aeedf41a3ac，
来源 de4581ede598150904695a1821c5489e9cd9a6ad。
server_binding:394 的 missing/注释/https 同值符合原合同，只是诊断信息不足；
run:210–238、ufw:399–432、collect:443–455 同样丢失失败类别。
本票不认定现场 UFW parser 有 bug，也不推断现场 PROTOCOL 缺失。

## 接口、数据与兼容性影响

新增独立 runtime aisoft_company_baseline_diagnostics_v2.py，contract_version 固定
company-platform-baseline-diagnostics/v2，collector_version 初始 2.0.0。v1 collector/schema/builder/guide
及 baseline v1/v2 不改字节。v1 envelope 继续由原 verifier 验证；v2 verifier 拒绝 v1，反之亦然；
调用方按显式合同选择入口，不自动升级、不重写旧 checksum。

v2 保持 environment/host_role/host/source/collector/profile pins、不同的 baseline 与 diagnostic UUID、
24 小时时窗、canonical checksum、stdout-only envelope。三个 observation 仍为 systemd/server_binding/ufw。

server_binding.value 为 closed object：
section_present、http_addr_matches_profile、http_port_matches_profile 使用 yes/no；
protocol_state 使用 missing/http/other。缺键、注释字段或 server 节不存在 -> missing；
显式空值或任何非 http 字面值 -> other；仅精确 http -> http。不输出原值、不做插值。
重复字段/非法格式继续 BLOCKED，不默认 http。三项 yes 且 protocol_state=http 才 PASS；其它可解析事实 GAP。
该结果仅描述固定文件投影，不能证明运行进程使用该文件。

reason 使用以下 closed enum，不输出 exception message 或原始数据：

| reason | 意义 | status/value |
|---|---|---|
| observed | 允许的事实已解析 | 按事实 PASS/GAP，value 非 null |
| command-unavailable | 固定执行文件不存在或执行权限拒绝等启动 OSError | BLOCKED/null |
| command-failed | 固定子进程非零退出 | BLOCKED/null |
| timeout | 4 秒总期限或子进程等待超时 | BLOCKED/null |
| output-limit | stdout 超过 65536 bytes | BLOCKED/null |
| decode-failed | stdout 或配置不能严格 UTF-8 解码 | BLOCKED/null |
| parse-failed | stdout/配置语法、未知字段、缺必需元数据、重复字段或 schema 不匹配 | BLOCKED/null |
| config-unavailable | 固定配置读取/类型/mode/大小不满足安全要求 | BLOCKED/null |

OS permission error 不含用户名、路径或原始错误；command-failed 不推断 permission-denied。
run 层直接保留原因，collector 不再把所有失败压为同一 reason；未知异常只输出稳定失败，
不能绕过 checksum/schema/status 校验。verify 必须由 reason/value 一致性重算 receipt，拒绝伪造状态。
overall 仍按 BLOCKED 优先，其次 GAP，否则 PASS；mutation_authorized 恒 false。

## Acceptance criteria

- [ ] AC-1：合成 missing、commented、http、https、empty、duplicate 协议样例得到指定且可区分的结果；
  missing/other 不推定服务协议，不输出原值。
- [ ] AC-2：mock 固定命令的不存在、非零退出、timeout、limit、decode、parse 失败得到对应 reason，
  空输出为 parse-failed，所有非 observed reason 均 BLOCKED/null。
- [ ] AC-3：UFW 解析范围保持 v1；合法合成样例 PASS、inactive GAP、未知行/元数据缺失 BLOCKED。
  不扩展版本兼容范围；若需扩展，必须先修订本合同并提供权威依据。
- [ ] AC-4：v1 文件 SHA 全部不变，历史 envelope 在原 verifier 下仍按原语义验证；v2 closed schema、
  version/digest/UUID/time/status 伪造负例拒绝；新 builder/guide 使用独立 v2 文件名。
- [ ] AC-5：固定 systemd/UFW argv、4 秒总超时、65536 byte 上限、固定配置安全读取边界、profile 校验不放宽；
  mock/哨兵证明无真实探针、无 shell/sudo/HTTP/SQL/log/Secret 输出，mutation_authorized=false。
- [ ] AC-6：新 targeted tests 覆盖 12 个基线用例及 run 层 mock/安全/兼容负例，连续两次通过；
  既有 baseline/diagnostics 回归与文档检查通过，执行范围全部 local。
- [ ] AC-7：v2 包 exact commit provenance、独立 manifest、目录 0700/文件 0600、额外文件/symlink/mode/hash
  漂移拒绝；同一输入在两个新目录产生一致 payload/manifest，故意 drift 失败且不覆盖旧包；
  文档分别记录 source/local 与 installed/live。

## 风险与回滚约束

v2 为旁路新增，源码回退使用最终 PR revert；停止采用 v2 后旧 v1 仍可按旧合同使用。
不自动回滚已采集 evidence、不删除现场包或历史记录。本票不部署、不需要现场回滚演练。
新增 guide 应说明管理员执行需要另行授权；不得建议对用户可写脚本盲目提权，须先由现场管理员
核验完整包与所有权/可写边界。生成 source 包不授予现场执行权限。

## 非目标

不改 AGENTS/Controller/CI/全局安装器；不改 v1/baseline 合同；不采用产品默认值替代事实；
不扩大解析白名单，不自动配置 Gitea/UFW/PostgreSQL，不安装 Runner，不输出配置/日志/规则正文。
不连接公司服务器、数据库或业务服务，不创建/推送 PR、不合并、不安装或现场复采。

## 未决问题

无技术方向未决项。用户已明确批准本票 T01–T03 本地实施；远端 PR、人工合并与现场执行仍按各自闸门处理。

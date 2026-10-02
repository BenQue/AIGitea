---
issue: 319
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/319
change_type: bugfix
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
confidence: high
risk_flags:
  - ci-change
depends_on: []
status: verified
branch: change/319-registry-utf8-exit
created: 2026-10-02
updated: 2026-10-02
---

# #319 验证记录

## 基线与范围

- fresh authoritative main：`5c2cd726c9aeaee9d17541d8feb049e33881bbac`。
- 合同批准 commit：`fbf9984a8f9ffbd27a8e8e4b1aaebecde224bccd`；源代码修复 commit：`f4620b7b421c9b2d00a5d7f46ec0dbb5178185d1`。
- macOS：/bin/bash 3.2.57，默认 LC_ALL=C.UTF-8；扩展 en_US.UTF-8 与 zh_CN.UTF-8。
- Linux：gitea-ci /bin/bash 5.3.9 aarch64，C.UTF-8。
- registry HTTP 请求全部指向 fixture 的临时 127.0.0.1 服务；未访问真实 registry/credential，也未采用 LC_ALL=C workaround。
- 源代码验证后未再改变两份 shell 文件；最终文档 commit 只增加计数修正、状态与证据，独立运行文档/合同检查。

## 改前与中间失败证据

| Check | Result | Evidence |
|---|---|---|
| 基线三种 macOS UTF-8：健康 0、停止后错误退出 0、nounset | FAIL（已复现） | [baseline-macos-utf8.json](evidence/baseline-macos-utf8.json) |
| 基线 Linux UTF-8 fixture | PASS（非修复验收） | [baseline-linux-utf8.txt](evidence/baseline-linux-utf8.txt) |
| 增强回归先运行、尚未修改脚本 | FAIL | [regression-red.json](evidence/regression-red.json) |
| 首次只修4处后 macOS仍 nounset/0 | FAIL | [first-fix-diagnostic.json](evidence/first-fix-diagnostic.json)、[fixture-first-fix-failed.json](evidence/fixture-first-fix-failed.json) |
| 临时6处提案副本 | PASS（仅方案论证） | [six-boundary-prototype.json](evidence/six-boundary-prototype.json) |

初始计数漏掉两处 CURL_STATUS 紧邻中文右括号。用户明确回复“批准更正为 6 处并继续”，已记录 [boundary-count-amendment.json](evidence/boundary-count-amendment.json)。源脚本共有6处同类边界，详见 [boundary-inventory.json](evidence/boundary-inventory.json)；未擅自改变 AC 或扩大文件/行为范围。

最早基线包装器误继承 REGISTRY_PREFLIGHT_REGISTRY，完整测试的这部分记录标 INVALID_HARNESS_ENV 并保留，不作为产品证据。修复后的测试显式绑定 fixture 地址/包/版本，使用 `$BASH`，避免误读真实 registry 或另一 interpreter。

## 正式执行结果

| Command / check | Result | Evidence |
|---|---|---|
| macOS 三组 UTF-8 `/bin/bash codex/tests/test-registry-preflight.sh` | PASS，均 exit 0 | [fixture-macos-utf8.json](evidence/fixture-macos-utf8.json) |
| Linux C.UTF-8 同 fixture | PASS，exit 0 | [fixture-linux-utf8.json](evidence/fixture-linux-utf8.json) |
| `/bin/bash -n` 两份修改的 shell | PASS | [static-checks.json](evidence/static-checks.json) |
| ShellCheck 两份修改的 shell | PASS | 同 static-checks.json |
| `LC_ALL=C.UTF-8 /bin/bash codex/tests/smoke.sh` | PASS，exit 0，227.95 秒 | [smoke receipt](evidence/smoke-macos-utf8.json)、[完整输出](evidence/smoke-macos-utf8.log) |
| 独立 Standards / Spec review | PASS，两轴0项发现 | [code-review.md](evidence/code-review.md) |
| `apply-classification-labels.sh --repo <worktree> --verify 319` | projected，bugfix/complex | 真实只读 receipt；投影工具原字节不变，既有扁平布局选指定 installed broker |
| live Issue + `load_contract` | VALID | approved、bugfix/complex、exact tuple、spec/plan/verification 映射验证 |
| PR required CI / installed / live / 下游采纳 / 部署 / merge | NOT RUN | PR 尚未提交；本地 source 结果不推断这些层次 |

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | PASS | 源代码 diff 中6处变量边界，静态检查PASS，原配置/EXIT trap保留 |
| AC-2 | PASS | 正式fixture断言健康0/OK、停止1/connect且正确地址与curl7、恢复0/OK；HTTP500/notpackument/tarball404/config各退出1/stage保留，准确诊断、拒绝nounset/OK |
| AC-3 | PASS | macOS Bash3.2三种UTF-8及Linux Bash5.3 C.UTF-8正式fixture |
| AC-4 | 本地PASS；PR CI NOT RUN | bash-n/ShellCheck/fixture/完整smoke通过，PRCI待提交后独立验收 |

## 合同批准、流程缺口与边界

用户已确认启动并授权 broker 判级/流程投影，见 [contract-approval.json](evidence/contract-approval.json)。原 auto-review 标签调用拒绝已在明确确认后解决；source/runtime 由后续 fresh turn 实施。随后用户明确批准计数修正并继续。

`未决问题` 的已解决说明移到独立章节，使既有 load_contract 可识别“无。”；不改变实现/AC。live Matt triage typed 操作缺口仍为 GAP，未绕过 broker，不在 #319 扩改治理接口。该缺口不阻止已有 approved 合同加载。

无阻塞 Issue 依赖。merge policy=manual；最终 PR 提交仍待 exact Issue/branch/manual 确认，人工merge与部署独立。不得在此阶段写 completed 或归档。

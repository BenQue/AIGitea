---
issue: 274
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/274
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - security
  - schema
  - external-contract
depends_on: []
status: approved
branch: change/274-baseline-profile-support
created: 2026-09-07
updated: 2026-09-07
---

# Baseline profile v2 验收记录

## 基线与范围

- Commit SHA：由最终 handoff 读取，避免提交自引用；本记录中的文件 hash 固定实现字节。
- 基线：`origin/main=a2dc131a65c733ff6d868bd5fd5e6b4bf13e4bb3`。
- 环境：本地 macOS Python/unittest；不访问公司网络或主机。
- 本记录负责证明 AC-1 至 AC-8 的 source/local 结果，并明确 installed/live 保持 NOT RUN。

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| `PYTHONPATH=codex/runtime python3 -m unittest codex.runtime.tests.test_company_baseline codex.runtime.tests.test_company_baseline_v2` | PASS | `Ran 59 tests in 0.860s`，`OK`；v1=35，v2=24 |
| `PYTHONPATH=codex/runtime python3 -m unittest discover -s codex/runtime/tests` | PASS | hardening 后最终 `Ran 793 tests in 81.608s`，`OK` |
| published schemas vs CLI | PASS | v2 test 对 `profile-schema`、`schema` stdout 与两个发布文件做 bytes equality |
| v1 checksum | PASS | `aisoft_company_baseline.py` 仍为 `3561d2f1fc607cdee1ba4688489645db1b2142cf57cc4d99433c35b1f33a7a88` |
| project-literal/unsafe API review | PASS | 产品代码/schema 无 NewEMaint IP、主机、cluster、18.2；无 shell=True、environment/config/journal/credential 读取 |
| `PYTHONPATH=codex/runtime python3 -m aisoft_loop.cli check-change-documents --repo .` | PASS | `changes=126 pass=2 gap=0` |
| `git diff --check` | PASS | whitespace/error 检查为空 |
| shell syntax/ShellCheck/`bash codex/tests/smoke.sh` | NOT RUN | 未修改 shell、installer、CI、skill 或 shared shell runtime；Python 完整 suite 已运行 |
| 公司 installed/live collection | NOT RUN | #274 仅交付 source；由 NewEMaint #79 消费稳定版本后另行执行 |

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | PASS（source/local） | v1 exact SHA test + 35 个既有 v1 tests；新增独立 v2 script/schema |
| AC-2 | PASS（source/local） | canonical LF、mode、`O_NOFOLLOW` fd read、profile digest/inventory tamper/CLI identity tests |
| AC-3 | PASS（source/local） | private/loopback 地址与 cluster/unit/storage relationship 负向测试；固定 binaries/root paths |
| AC-4 | PASS（source/local） | FakeHost exact argv/HTTP/storage allowlist；bounded subprocess；Secret/error 不透传 |
| AC-5 | PASS（source/local） | external-interface 与 hyphen-free cluster fixture；wildcard/错误地址 listener 为 GAP |
| AC-6 | PASS（source/local） | adopt/remediation/BLOCKED、missing current、history、manual supplement 与 mutation=false 回归 |
| AC-7 | PASS（source/local） | 24 个 v2 tests、schema bytes equality、完整 793 tests |
| AC-8 | PASS（授权 source 范围） | diff/semantic checker PASS；公司、NewEMaint installed/live 全部 NOT RUN |

## 遗留风险与未完成项

- NewEMaint 的真实 profile、现场采集与 SCM onboarding 属于 #79，不得在本 verification 写成 PASS。
- UFW 全主机历史规则存在 owner-review GAP；#274 不改变或裁决现场规则。
- push、最终 PR、CI、merge、安装、部署与清理均未执行。

## 审查与固定字节

- 首轮职责审查发现测试 fixture 使用了与现场相同的 PostgreSQL patch 数字，已改为中性 `18.7`，复测 PASS；产品源码和 schema 从未包含项目具体值。
- 安全审查发现 profile `lstat` 后读取存在 symlink replacement 时间窗，已改为 `O_NOFOLLOW` 打开同一 fd 后 `fstat` 和有界读取，复测 targeted 59 与完整 793 tests PASS。
- v2 collector SHA-256：`6ebb743d82a55f1745f450203e22c0141405c09f78ffd2c438ad583a2c6de529`。
- profile schema SHA-256：`ef22e83e6fe4ad3b62de7748f4cd14e596929bbcd6299b472678d75acf78b495`。
- inventory schema SHA-256：`c5f81131cc2ef6bd9f37199c55824bbc6dbd8ff703d37367949e0d959238ffe6`。

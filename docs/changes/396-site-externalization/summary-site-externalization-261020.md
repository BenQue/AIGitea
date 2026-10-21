---
issue: 396
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/396
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 改 broker manifest schema 与 aisoft_host_access 合同校验、broker 与轮换读取路径、泄漏守卫、技能与下发模板，合并后两台重装，属于共享核心、schema、跨模块与平台治理变更
risk_flags:
  - shared-core
  - schema-change
  - cross-module
  - rollback
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-site-externalization-261020.md
  spec: spec-site-externalization-261020.md
  plan: plan-site-externalization-261020.md
  verification: verification-site-externalization-261020.md
confidence: high
override_reason: ''
depends_on:
  - 391
status: pr-open
branch: change/396-site-externalization
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/398
created: 2026-10-20
updated: 2026-10-20
---

## 问题/需求总结

整改路线 R13：平台内核不再钉死某台 Mac、某个账号、某个 OrbStack 机器名。broker manifest 新增 `site` 段作为站点值唯一来源，`aisoft_host_access/contract.py` 改为结构校验；泄漏守卫覆盖站点值与全部注册仓库名（含 public-test）。合同与验收见 spec。

## 影响范围

`codex/config/host-access-broker.json` 与夹具；`aisoft_host_access` 的 contract、broker、credential_rotation 与测试；`check-project-leak.py` 与基线；`skills/aisoft-platform` 技能与两份 references；`templates/project/ci/ci.yml` 与 `registry-preflight.sh`；`01`、`07`、`13`、`README` 的 public allowlist；使用层发布包。

## 初步方案与建议

三个站点键从 `mac_host` 迁入 `site`，其余与已有声明做一致性校验，不另立第二来源。守卫用同一棘轮基线管两组集合。技能与模板（治理文件）单独 commit 后停下重读。

## 风险

manifest schema 变更要求代码与 manifest 同装；源码 runtime 与已安装 broker 在合并到重装之间不一致。回滚为 revert 后两台重装。与 R10b 共改 `SKILL.md` 与发布包，后合并者 merge commit 集成。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 改 broker manifest schema 与 aisoft_host_access 合同校验、broker 与轮换读取路径、泄漏守卫、技能与下发模板，合并后两台重装，属于共享核心、schema、跨模块与平台治理变更
risk_flags:
  - shared-core
  - schema-change
  - cross-module
  - rollback
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
```

### 判级证据

- 改 broker manifest 结构与合同校验、broker 与 K1 轮换的读取路径，属强制 complex 的共享核心、schema 与跨模块类别。
- 改 `aisoft-platform` 技能与下发模板（发布包成员），属平台治理，需受控步骤与发布包升版。
- 验收含合并后两台重装与 audit 读回，不能只靠 diff review 与 CI 重放，故声明 verification。

### 缺失的 acceptance criteria 或决策

- 无。任务书三条验收展开为 spec AC1–AC6；负责人 2026-10-20 15:21Z 在线程回「确认」接受 spec「决定」一节的默认值。

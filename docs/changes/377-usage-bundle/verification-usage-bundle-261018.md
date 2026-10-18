---
issue: 377
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/377
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - platform-governance
  - shared-core
depends_on: []
status: verified
branch: change/377-usage-bundle
created: 2026-10-18
updated: 2026-10-18
---

# #377 验证记录

## 基线与范围

- Commit SHA：代码与测试的验证对象 `fa03ab5ae99e19a93fdaa2d687eb1d6067845969`；本记录随后的 commit 只改本目录文档与 plan 状态，最终 head 另跑 `check-change-documents` 与泄漏检查
- 基线：`origin/main` = `bcf2fd7d`
- 环境：macOS 本机（Darwin 27.0.0，Python 3.14.4，`/opt/homebrew/bin/rg`）；Codex 复核另用 `/usr/bin/python3` 3.9.6 跑带基线的 `--verify`
- 本记录负责证明的 acceptance criteria：AC3–AC5、AC10，以及 Codex 独立审查

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| `bash codex/tests/smoke.sh` | PASS | 退出 0；Python 回归 1238 个用例 OK；包含 `test-usage-bundle: PASS` 与 `usage-bundle.sh --verify --baseline-ref origin/main` |
| `bash codex/tests/test-usage-bundle.sh` | PASS | 17 组用例：首发、拒绝重复发布与非递增版本、成员改动未升版本、模板任一字节变化都算成员改动、build 确定性、pin 当前与旧版本、无 lock、未知版本、摘要不符、合同副本漂移、改写历史、exact 未归核对项、核对项无成员、U+2028 与 CRLF 指针边界、基线前缀不可改写与可追加、lock 落点固定 |
| `bash codex/tests/test-project-check.sh` | PASS | 63 个用例；对齐夹具 pin 最新版本，新增缺 lock 与合同副本漂移两个 GAP 用例 |
| `bash codex/tools/change-template-sync.sh --verify-digest` | PASS | summary 模板依赖边注释删除后已刷新 digest（smoke 内） |
| `python3 -B codex/tests/check-project-leak.py` | PASS | 14 个基线文件、92 处命中；summary 模板退出基线，`usage/CONTRACT.md` 已加入治理文件项目名与交付实现名守卫 |
| Codex 独立审查（Herdr 只读会话） | FAIL → FAIL → PASS | 首轮 5 major 2 minor：历史可自洽改写、指针边界与 awk 不一致、导出字节不受版本保护、exact 成员可不核对、合同与指针对 development complex 路由冲突，以及 schema 偏离 AC3、本记录未填；`8eab8d4` 修复。复核 1 major 2 minor：`lock_path` 可改、基线读取失败被当作首发、small 文档义务表述过窄；`fa03ab5` 修复。终审 PASS |

## 对接入项目的只读核对（AC10，采用前）

本机 checkout 的 project-check 本地段，左为 `origin/main` 平台工具，右为本分支：

| 项目 checkout | pointer-sections | change-templates | platform-pin |
|---|---|---|---|
| NewEMaint `dfcde808` | GAP → GAP | GAP → GAP | 无此项 → GAP（缺 lock） |
| LocalWMS `182ea7e` | PASS → GAP | GAP → GAP | 无此项 → GAP（缺 lock） |

LocalWMS 的 `pointer-sections` 由 PASS 变 GAP，是因为 1.0.0 的常驻指针改为指向本仓 pin 的使用合同。两个项目采用 1.0.0（复制 `usage-bundle.sh --build` 产物、提交 lock）是各自仓库的 Issue；采用后平台前进不再改变它们的结论。NewEMaint 的 docker-release 合同字节 pin 不受影响（本票未改 `docker-release/` 与 `aisoft_release`）。

## 未执行项

- installed 层：技能源改动后本机已装的两侧平台技能会漂移。合并后由负责人运行 `bash codex/install-skills.sh "$HOME"` 与 `bash skill-for-claude/install.sh "$HOME"`，再用 `bash codex/tools/check-installed-drift.sh` 读回。PR 内 NOT RUN。
- 项目采用：NewEMaint、LocalWMS 采用 1.0.0 不在本票范围，NOT RUN。
- `08` §7 项目使用层的真实 pilot 与非生产部署：不适用于本票，NOT RUN。

---
issue: 383
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/383
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - shared-core
  - rollback
  - platform-governance
depends_on:
  - 380
status: pending
branch: change/383-reference-impl-exit
created: 2026-10-19
updated: 2026-10-19
---

# #383 验证记录

## 基线与范围

- 基线：`origin/main` = `80a38dc`（R7 合并后；合同取证时为 `a395f7a`）
- 环境：macOS（MacM4ProBQue），bash 3.2 系统 shell
- 本记录负责证明 spec AC 1–10

## 执行结果

实现 head 见各行；全量 smoke 在 `44f2fc0` 运行，之后只改文档措辞（交叉审查 P3）与本记录，提交前在最终 head 复跑。

| Command / check | Result | Evidence |
|---|---|---|
| 改动前 `bash codex/tests/smoke.sh`（`3475faa`，基线 `80a38dc`） | PASS | exit 0，8 分 49 秒；runtime discover `Ran 1238 tests` |
| 改动后 `bash codex/tests/smoke.sh`（`44f2fc0`） | PASS | exit 0，6 分 53 秒；runtime discover `Ran 849 tests`，installed-drift 夹具 `Ran 35 tests` |
| `bash codex/tests/test-installer-source-guard.sh` | PASS | `7 installers x 3 source states` |
| `bash codex/tools/check-installed-drift.sh --source-only` | PASS | 七个 surface 全 `SOURCE PASS`，`RESULT PASS` |
| `bash codex/tools/usage-bundle.sh --verify --baseline-ref origin/main` | PASS | `VERIFIED 1.2.0`；1.0.0、1.1.0 未改 |
| `python3 -B codex/tests/check-project-leak.py` | PASS | 基线收紧为 4 个文件、11 处命中（原 13 个文件），被删路径条目移除 |
| AC8 残留扫描 `rg` 被删路径与模块名（排除 `docs/changes/`、`archive/`、`docs/adr/`、`docs/governance/`、06 踩坑表） | PASS（有说明） | 剩余命中：指向 `archive/` 的链接；`12` §0 标注为“平台原参考 CLI 接口形态示例”的两行命令；architecture 测试与夹具对 `docker-release/` 交付形态名称前缀的断言 |
| 删除清单核对 | PASS | 127 个文件，按目录计数写入 `archive/reference-implementations-exit-261019.md` |

## 外部影响与已安装副本（AC3、AC10）

- 只读探测（2026-10-19，`orb -m <vm> -u benque`）：DockerLab 有 `/opt/aisoft-docker-release`、`/usr/local/bin/aisoft-docker-release`、`/usr/local/bin/aisoft-docker-release-gate`；gitea-ci 与 AppServer 没有。平台不删除这些副本。之后若需重装或升级，来源改为采用方项目仓的副本；不再使用时由采用方在自己的 Issue 中卸载。
- NewEMaint 按 `e1290d2`、`1164318` 取文件，本 PR 不改写历史，取法不变；governance manifest 未改。
- 合并后两侧技能 installer 重装与漂移读回：NOT RUN（合并后执行）。

## 交叉审查（`03` §7）

| 轮次 | 审查方 | head | 结论 | 发现与处置 |
|---|---|---|---|---|
| 1 | Codex（Herdr 新会话，`--sandbox read-only`） | `44f2fc0` | FAIL | P2 本记录未填实际证据：已补。P3 README 三处“八个安装面”：改为七个。P3 `platform-bootstrap/README.md`、漂移检查 docstring、06 小节标题含被删路径文字：改为引用迁出说明或不写路径。其余项（157 个路径均在 git_scope、127 个删除与清单一致、未误删 K1–K5、保留覆盖未丢、治理 commit 隔离、旧发布版本与 pin 未变、无断链）无发现 |

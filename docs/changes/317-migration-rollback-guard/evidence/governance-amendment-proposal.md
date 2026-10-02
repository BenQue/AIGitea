# Issue #317 固定证据闸门合同修订提案（未批准）

当前批准 spec/plan 不变。本文件是供用户审阅的精确修订草案，不是新的实施授权。

## 实际阻塞及必须升级的原因

`bash codex/tests/smoke.sh` exit=1；固定检查器
`codex/tests/check-release-evidence-boundary.py` 拒绝 current file set differs from the fixed baseline。
它既冻结 #65/#290 历史文件集合，又只允许 runner/transport/matrix 的 exact current pin。
#317 的 approved scope 新增 module/schema/contract，并改变 state/parser/errors/target-profile bytes，
因此无论代码行为测试是否通过，都无法通过这个原边界。

AGENTS.md 明确：“遇到合同冲突、范围扩张、破坏性迁移、安全决策、外部阻塞或重复失败时必须停止并升级给人。”
该检查器不在 approved allowlist；扩大其允许集合属于治理范围扩张。尚未修改、跳过或降级这个 hard gate。

## 建议批准的精确范围

仅将以下两文件加入本票实现 allowlist：

- `codex/tests/check-release-evidence-boundary.py`
- `codex/runtime/tests/test_release_evidence_boundary.py`

保持同一 #317 / change/317-migration-rollback-guard / docs tuple / manual policy / 唯一最终 PR。
不修改 smoke.sh、CI workflows、AGENTS/CLAUDE、Controller/provider/broker/installers、权限、live 配置或应用仓。

## 固定检查器的受限修订

1. `BASELINE`、`SCOPES`、`CONTENT_EXEMPT`、`RUNNER_BEFORE`、`RUNNER_AFTER`、`EVIDENCE_SHA256`
   和原历史 regression snapshot 完全保持，历史 evidence 文件不能变。
2. existing-source amendment 的固定 allowed 集合只增加 contract.py、errors.py、state.py 与
   target-profile-v1 schema；runner 新 hash；transport/matrix 的现有 hash 保持。
3. 新增独立固定 `CURRENT_ADDITIONS`，只容纳下表的5个新增 path、mode 与 SHA256。
   expected file set = historical baseline set + 这5个明确对象；不是 glob/目录/content 豁免。
4. baseline 既有文件与新增对象都必须同时验证 disk/index exact bytes 与 mode；未知、缺失、
   改名、symlink、mode/hash drift 或额外 byte 一律 fail closed。参数不增加 override。
5. current_release_regression 必须真实运行完整 release suite；history/current regression 前后
   再验证 source identity，不能把历史执行或 in-tree bytecode 作为当前 source PASS。
6. 明确区分历史真实 evidence、当前 FakeDocker/source regression 与未运行的当前真实 E2E。
   current_real_e2e/installed/company_live 继续 NOT_RUN，不 provision/安装/部署/操作真实 Docker/DB。

## 待审阅的当前 bytes 清单

下列 bytes 是当前本地候选，若 review 修复导致变化，须重新记录真实 SHA256 再固定；禁止
在正常 checker run 自动重算认可 hash。所有 record 均固定 `100644`。

| Path | 类别 | Mode | SHA256 |
|---|---|---|---|
| `codex/runtime/aisoft_release/contract.py` | 原有文件新 bytes | `100644` | `b79deccc5f94368c671f9f1b6d7af06c5312556e3f51096ad583fce21b215ef3` |
| `codex/runtime/aisoft_release/errors.py` | 原有文件新 bytes | `100644` | `f76e0264c9480cc7a2ef70f20899d65e81bdf3ad994b9bd9b0015a36f32b28ac` |
| `codex/runtime/aisoft_release/runner.py` | 原有文件新 bytes | `100644` | `a51abcaa2bcb9862b9a981df1d8c3efd2d32c70ae795b485678cac322f04eb4c` |
| `codex/runtime/aisoft_release/state.py` | 原有文件新 bytes | `100644` | `1350ddab013eabb7f0286ba12a6835974e221775e3a25823f38cb332445c8e2a` |
| `codex/runtime/aisoft_release/rollback_compatibility.py` | 新增 | `100644` | `70767f26238d6fe1d083d7c0019910a207cda5ff2d27a5af2a4bd85b479a0de2` |
| `docker-release/schema/target-profile-v1.schema.json` | 原有文件新 bytes | `100644` | `d6174d0b78eecbba73962210720b70eea6f0558a6ed176b765e2bdb916c114e4` |
| `docker-release/schema/state-v3.schema.json` | 新增 | `100644` | `3fce0413e7cdc19ab80ecae9bb1962dfab49a48d4ca9694dd2f3be41c2c0f326` |
| `docker-release/schema/rollback-compatibility-v1.schema.json` | 新增 | `100644` | `94d2ea3f822b6fded55fc351546793d9334133b79baf439402f4e93c5c2ee9b2` |
| `docker-release/contracts/migration-rollback-v1.md` | 新增 | `100644` | `17077aea5bdf46f26b859bf3d57682d67230442c8cb4721c3e062dce233b11e8` |
| `docker-release/examples/rollback-compatibility-v1.example.json` | 新增 | `100644` | `3c01fa1196ae8ffe78b81afd2b0ef6b52c5ca7d6f043e18aed4e3b43ae10169d` |

## 新增验收

- 对每个新增对象验证：exact disk/index/mode 正例；额外 byte、staged-only drift、删除/改名、
  symlink、mode 变更、unknown addition、untracked extra 均拒绝。
- 非 allowlist 路径（尤其 historical evidence）不能成为 current pin/addition；invalid hash/mode 拒绝。
- 原 boundary/bytecode isolation 回归继续通过；历史 evidence hash 恒定。
- 新 checker exit=0 后才重跑完整 `bash codex/tests/smoke.sh`，并真实保存执行结果。
- 本票完整 hard gates 都通过，才能请求独立 exact manual 最终 PR 提交确认。

## 应用步骤与停止点

建议用户批准此修订后：T04 只应用 spec/plan/versioned governance contract 的精确修订并本地
提交，记录授权后停止；后续 fresh run 重读新合同，再执行 T05 的 bounded checker/tests/pins、
完整 regression/smoke 和两轴 review。现有本地 source commit 保留，无回滚或重写历史。
修订批准不授权 push/PR/merge/安装/部署；最终 PR 提交确认仍独立保留。

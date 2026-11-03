---
issue: 438
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/438
change_type: bugfix
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
confidence: high
risk_flags:
  - agent-governance
  - ci-change
depends_on: []
git_scope:
  - docs/changes/438-skill-frontmatter-yaml/summary-skill-frontmatter-yaml-261103.md
  - docs/changes/438-skill-frontmatter-yaml/spec-skill-frontmatter-yaml-261103.md
  - docs/changes/438-skill-frontmatter-yaml/plan-skill-frontmatter-yaml-261103.md
  - docs/changes/438-skill-frontmatter-yaml/verification-skill-frontmatter-yaml-261103.md
  - skills/aisoft-platform/SKILL.md
  - codex/tools/check-skill-frontmatter.sh
  - codex/tools/check-skill-frontmatter.py
  - codex/tests/test-skill-frontmatter.sh
  - codex/tests/smoke.sh
  - usage/bundle.json
  - docs/governance/review-evidence-index.md
branch: change/438-skill-frontmatter-yaml
created: 2026-11-03
updated: 2026-11-03
---

# 技能 frontmatter 恢复为合法 YAML，并由 smoke 守住

## 目标与原因

CarbonEngine 跑 `/doctor` 发现：发布包 1.21.2 起分发的 `aisoft-platform` 技能，frontmatter 的 `description` 是一行未加引号的纯量，
英文段里的 `platform: Issue analysis` 让严格 YAML 解析器报 `mapping values are not allowed`。Claude Code 目前容错，所以没有可见故障；
但 frontmatter 解析失败时 name、description 等字段都会被丢弃，换成严格解析的工具（Codex、其他 agent、平台自己的脚本）时技能路由会
静默变差。平台仓里没有任何检查拦得住这类错误，所以同类问题会再次出现。

## 范围与非范围

范围：

- 把 `skills/aisoft-platform/SKILL.md` 的 `description` 改成合法 YAML：`platform: Issue analysis` 改为 `platform, including Issue analysis`，
  其余文字不动，仍是单行纯量。
- 新增只读检查器 `codex/tools/check-skill-frontmatter.sh`（薄包装）+ `check-skill-frontmatter.py`：对 `skills.manifest` 声明的每个技能，
  用真实 YAML 解析器严格解析 `SKILL.md` 首个 `---` 块；结果必须是映射，`name` 是等于目录名的字符串，`description` 是非空字符串。
  同时解析每个技能 `agents/*.yaml`，结果必须是映射。manifest 声明的技能缺 `SKILL.md`、frontmatter 缺失或未闭合都算失败。
- 解析器后端：优先 PyYAML `safe_load`（CI 所在 VM 有系统包 `python3-yaml`），没有时用系统 Ruby 的 Psych `YAML.safe_load`（macOS 自带）；
  两者都没有时以退出码 2 失败并说明原因，不回退到手写解析。
- 新增 `codex/tests/test-skill-frontmatter.sh`（临时目录夹具，正例与各类反例），并按 smoke 新工具登记的 5 处登记；smoke 对仓库自身跑检查器。
- 改了发布包成员，同 PR 发布 `1.22.1`（`--compatibility patch`）。
- 在 `docs/governance/review-evidence-index.md` 追加本批交叉审查行。

非范围：

- Issue「附带观察」：用户全局与项目各装一份同名 `aisoft-platform` 时加载哪一份、推荐安装位置与版本不一致提示。这是安装与采用合同的
  问题，不在本批；如需处理另开 Issue。
- 不改其他技能正文，不改 vendor 快照（Matt、superpowers 的技能不归平台校验），不改 installer 与漂移检查。
- 不重装本机技能、不升级任何项目的发布包；合并后由人按项目记忆里的命令重装。

## Acceptance criteria

- [ ] AC-1：PyYAML 与 Ruby Psych 两个后端都能把 8 个平台技能的 frontmatter 解析为映射，`aisoft-platform` 的 `name`、`description` 读回为字符串，
  description 只把 `platform: Issue analysis` 换成 `platform, including Issue analysis`（`git diff` 只有这一处）。
- [ ] AC-2：`bash codex/tools/check-skill-frontmatter.sh` 对本仓输出 PASS 并以 0 退出；对 `origin/main` 上旧版 `SKILL.md` 构造的夹具以非 0 退出，
  输出点名 `aisoft-platform` 与解析错误（反向证明）。
- [ ] AC-3：`test-skill-frontmatter.sh` 覆盖正例与反例：未加引号的 `: `、`name` 与目录不符、缺 `description`、frontmatter 未闭合、
  非映射 frontmatter、manifest 声明但缺 `SKILL.md`、坏的 `agents/*.yaml`；本机可用的每个后端各跑一遍，两个后端都不可用时检查器以 2 退出。
- [ ] AC-4：`bash codex/tests/smoke.sh` 全绿，`grep -n 'test-skill-frontmatter' codex/tests/smoke.sh` 有 3 行（两处静态 + 一处执行），检查器也在两处静态清单里；
  删掉 smoke 里执行检查器的那一行后，旧 `SKILL.md` 不再被拦（证明守卫确实在跑）。
- [ ] AC-5：`usage/bundle.json` 新增 `1.22.1`，`usage-bundle.sh --verify --baseline-ref origin/main` PASS。
- [ ] AC-6：未参与实现的 Codex 对候选 head 只读交叉审查 PASS，记入 verification 与证据索引。

## 风险与回滚约束

- 风险：CI 主机将来去掉 `python3-yaml` 时守卫以 2 失败，smoke 变红；这是有意的 fail closed，修复是装回系统包，不是放宽守卫。
- 风险：两个后端对 YAML 1.1/1.2 细节可能不一致；本批只要求两者都接受当前 8 个技能、都拒绝 `: ` 反例，测试在两边都跑。
- 回滚：revert 本 PR；已发布的 `1.22.1` 留在 releases 里（只追加），后续批次再发新版本。

## 接口、数据与兼容性影响

- 技能 description 的语义不变，触发词与中英文段都保留；项目升级到 1.22.1 后 `platform-pin` 按新字节核对。
- 新检查器只读，不写缓存或临时文件（`python3 -B`，`PYTHONDONTWRITEBYTECODE=1`）；不触网、不读用户 home。
- 无 schema、数据或部署影响。

## 未决问题

无。

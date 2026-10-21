# 合成 manifest 夹具

`gitea-governance.json` 与 `host-access-broker.json` 是平台测试用的冻结夹具（#380，ADR 0001 D3）。
测试断言这里的合成项目，不读 `codex/config/` 下的真实 manifest；smoke 有守卫拦截测试改回读真实文件。

- 来源：2026-10-18 `origin/main` `8fa4458` 的真实 manifest，机械改名。
- 改名：四个 internal-application 项目换成 AlphaApp、BetaApp、GammaBoard、DeltaDB，project id、
  agent、VM profile 与 checkout 路径随之改名；平台仓与 public-test 项目保持原样。
- #397 起两份 manifest 不再含已退出的自动合并字段（夹具与真实 manifest 同步删除，合同拒绝旧字段）。
- #396 起站点值集中在 `site` 段（从 `mac_host` 迁入三个键）；夹具与真实 manifest 同值，换站点的测试在临时目录里改写它。
- 夹具不随真实 manifest 同步。schema 变化时同时改夹具与断言；项目接入或退出平台不应触碰这里。
- 改完运行 `PYTHONPATH=codex/runtime python3 -m aisoft_host_access.cli --access-manifest
  codex/tests/fixtures/manifests/host-access-broker.json --governance-manifest
  codex/tests/fixtures/manifests/gitea-governance.json validate`。

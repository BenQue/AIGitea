# 交叉审查证据索引

平台仓 complex 变更的交叉审查记录（`03` §7「交叉审核」）。每批一行；逐轮的发现与处置在「来源」所指的
verification 或 PR 正文里。规则：实现方 ≠ 审查方；审查 head 写 40 位 SHA；仓内与 PR 正文都没有的写「未记录」，不补造。

从 #408 起，每批在自己的 verification 固定节 `## 交叉审查` 逐轮记录，并在本批 PR 里追加本表一行；行在合并前写，
PR 编号以该批 summary 的 `pr_url` 为准，「合并」列写 `—`，合并 SHA 由 git 历史给出。

## 第二轮整改前（R0–R8）与运维批次

实现方一列：R0–R8、#385、#387 的 summary 没有实现方字段，表中「Claude」是按当时分工与审查方为 Codex 推定的，
标 `*`。#370 起有明确记录。

| 批次 | Issue | PR | 合并 | 实现方 | 审查方 | 审查 head（按轮） | 各轮结论 | 来源 |
|---|---|---|---|---|---|---|---|---|
| R0 | #364 | 365 | `af3ee324a952e5df2eb77312fd0f0f697f9c401e` | Claude* | 未做交叉审查 | 无；PR head `b69adccf68960f6f543e00f6c14145f65cbd4c69` | — | PR 365 正文（只有 source/local 证据） |
| R1 | #366 | 367 | `fe3b0264d0083e38a4bf8f7946e51ae484f2dd4d` | Claude* | 未做交叉审查 | 无；PR head `0e96391cf6997e2be01619b6ca7a92bf69e8cbb1` | — | PR 367 正文 |
| R2 | #368 | 369 | `5fa109a8b76e8e77715fe2e2162240e298c96201` | Claude* | 未做交叉审查 | 无；PR head `8fe2e5d83fde8b83ef957a57c05e6abf2cc5b8e1` | — | PR 369 正文 |
| R3 | #371 | 372 | `87be7a35e3216cc1ee7f54cf21ccbcf5db89bdba` | Claude* | 未做交叉审查 | 无；PR head `deed18f36fccbc6f750a8c106f2f6cb04332259a` | — | PR 372 正文 |
| R4 | #373 | 374 | `c3d49edcda9383ee0a57c01a51d91cfab976437d` | Claude* | Codex | 1：`78a3237670c32ad7bc22152d942167a5426ae2d5` | PASS-WITH-NITS（minor 已在 `ef6ae86` 补用例） | PR 374 正文「交叉审查（ADR D6）」 |
| R5 | #375 | 376 | `bcf2fd76ad286d7f1fc07f8c3093ec6358de00b4` | Claude* | Codex | 1：未记录；修复 head `e0ea16ea8bffa1455b07efd51c483e35c83c16c2`，复审未记录 | FAIL → 已修复（复审结论未记录） | `docs/changes/375-skills-update/verification-skills-update-261018.md` |
| R6 | #377 | 378 | `8fa44585da0133918eff498441800a575a8e865d` | Claude* | Codex（Herdr 只读） | 1：未记录；2：`8eab8d4937d3458a6a006be1ad5ed693fcd911ee`；3：`fa03ab5ae99e19a93fdaa2d687eb1d6067845969` | FAIL → FAIL → PASS | `docs/changes/377-usage-bundle/verification-usage-bundle-261018.md`；任务书在项目库 `codex-review-377.md` |
| R6b | #380 | 382 | `a395f7ad9bcee68f1c29b858e879d06e88de5c8f` | Claude* | Codex（Herdr 只读） | 1：未记录；2：`d2f22b5493b5d0b8e8413cc325241f400d41e095` | FAIL → PASS（P3 已抑制） | `docs/changes/380-fixture-manifests/verification-fixture-manifests-261018.md` |
| R7 | #379 | 381 | `80a38dcbfb254bb6a4b1b04c7618e34a132688d1` | Claude* | Codex（Herdr 只读） | 1：`605c196cf0109c2efcd4320f40239ed07dd424d6`；2：`4c9036b5939148702834c9177765dda06928dd83`；3：`d7be64911f63e6fdb8247e989f7b6e960991740d` | FAIL → FAIL → PASS | `docs/changes/379-skills-single-source/verification-skills-single-source-261018.md`「Codex 交叉审查」 |
| R8 | #383 | 384 | `f49f15a1771189028ce14565ab9c006b69d458d8` | Claude* | Codex（Herdr 只读） | 1：`44f2fc08be9241e61a3ab4cd71f25c1be2f0c974`；2：`1deded74c637d01c1bd81a18e094c5f07fd4995b` | FAIL → PASS | `docs/changes/383-reference-impl-exit/verification-reference-impl-exit-261019.md`「交叉审查」 |
| — | #385 | 386 | `7eca227654a45fe79a2ba046c6a4fe225e2fb788` | Claude* | Codex（Herdr 只读） | 1：`65b943e1ce7b580f0266d0bb2a1f14eda4a824b8`；2：范围 `65b943e..bbb333ca1b77a7fa7ba5285c622075e261244936` | FAIL → PASS-WITH-NITS（nit 在 `e93e17f`） | `docs/changes/385-newemaint-routine-exit/verification-newemaint-routine-exit-261019.md`；项目库 `codex-review-385.md` |
| — | #387 | 388 | `77ad6072f83b8ee2f9b6c8280dcec9652c930ad0` | Claude* | Codex（`codex exec -s read-only`） | 1：`2c0adbf30cb1cba7e2c25f49e3fea961f84918ed`；2：`7f5c7c03e1b56ecc6bc51310a7f3ac57567f3cd9`；3：`679fcd2193fcab5a1ac9468663a2cabb660ccd08` | FAIL → FAIL → PASS-WITH-NITS（nit 在 `515eb94`） | `docs/changes/387-vm-timer-alerts/verification-vm-timer-alerts-261019.md`；项目库 `codex-review-387.md` |
| — | #370 | 401 | `fdf93c1da2272ed20ca215ba285cb50cb7e9cfc3` | Claude | Codex（只读） | 1：`0f4b3ac2b1d24c6c26c7688961c88ac943505f9f`；2：`dd58deb902d83e93101c1697ba7a4afc3866288e` | FAIL（一条 P2 已修）→ PASS | `docs/changes/370-ci-download-cache/verification-ci-download-cache-261020.md`；项目库 `codex-review-370.md` |

计划里的「Codex 实现、Claude 审」反向批次已由负责人取消（2026-10-20 改为 Claude 实现，#408 确认点 1 记录）；
#370 原定为反向首例，最终由 Claude 实现、Codex 审查。

## #408 起

| 批次 | Issue | PR | 合并 | 实现方 | 审查方 | 审查 head（按轮） | 各轮结论 | 来源 |
|---|---|---|---|---|---|---|---|---|
| R15 | #408 | 见 summary `pr_url` | — | Claude | Codex（`codex exec -s read-only`） | 1：`2256a105552868b805260978fe46869caa34fd02` | FAIL（4 major 3 minor，已修） | `docs/changes/408-peer-review-evidence/verification-peer-review-evidence-261021.md`「交叉审查」；项目库 `codex-review-408.md` |

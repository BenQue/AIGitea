# #316 T04B 双轴复审闭环（2026-10-03）

固定 Issue 起点：82bab79546b298a0776dc666b4fcbb30442930d2。两个文件的 imported source baseline：fresh main 16beee09aefe89b5bc80a31544c59d456190ea32。实际审查 delta：t04b-fresh-main-source-fix.patch.gz；只修改批准的 checker 与 fixture 源码及本票文档/证据。

## Standards

初审 1 项 P2：固定 helper SOURCE 输入仅加入 source identity，却未在 SOURCE definition 阶段读取。隔离注入 build.py missing 时返回 SOURCE PASS/exit 0，违反新增固定依赖校验合同。

修复后只对固定必需 helper 输入执行 no-follow 读取和 lock schema/model/toolchain/Linux pin 校验；合法 PR 的 cached-source identity GAP 仍与定义合法性分开。独立复现 build.py missing 返回 SOURCE ERROR/exit 2，已核对负向、helper-selected 零写入 audit 和 metadata parent replacement 绿灯回执。最终无残留硬违反或需报告的新增 Fowler smell。

## Spec

初审同一 SOURCE 定义门 P2；缺失、链接或不可读输入原可能被降为 identity GAP 而不使 source-only 拒绝。修复后必需输入与坏 lock 有负例，红/绿日志已读回。当前未发现剩余 Spec 阻塞项或范围扩张。

固定四键 metadata、不跟随 JSON 路径、独立 public provenance、helper:null 的本机/远端边界、source-only 零 target/外部证据读取均符合已批准补充合同。installer PIN 在映射首轮 32 tests 与 P2/额外保护 3 tests 通过后才推进。

审查仅为源码证据，不能代替完整组合 smoke、required CI、installed 或 live 回执。红日志 t04b-source-input-red.log；绿日志 t04b-source-input-green.log（3 tests PASS），均在本票临时 build 目录。最终 smoke 结果另列 verification。

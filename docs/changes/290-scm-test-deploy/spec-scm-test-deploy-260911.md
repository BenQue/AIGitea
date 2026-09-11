---
issue: 290
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/290
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - security
  - deployment
status: approved
branch: change/290-scm-test-deploy
created: 2026-09-11
updated: 2026-09-11
---

# 允许 scm-ci 测试部署

## 目标

基于现有TargetProfile.environment增加精确例外：scm-ci + test允许测试部署，scm-ci + production仍拒绝。不新增字段/角色，不重新实现部署流程。

## AC

1. scm-ci/test允许stage、migrate、activate、deploy、status、rollback；verify/verify-target维持原行为。
2. scm-ci/production上述动作全部拒绝；未知动作/角色/环境、错误hostname不得被例外放行，拒绝发生在Docker调用或状态写入前。
3. appserver-test/appserver-prod既有行为保持；profile文件保护、制品/兼容性校验、action grant不变。
4. 表驱动矩阵覆盖角色/环境/动作；scm-ci/test使用fake adapter验证部署、重复no-op及失败回滚；production拒绝零Docker事件；既有release tests通过。
5. 文档明确source/local、installed、company live分层，项目需独立Compose项目/目录/数据库/端口，不能覆盖SCM资源。

## 明确授权的修改范围

治理阶段：README.md、docker-release/README.md、本Change语义文档；不修改AGENTS或全局skills。
下一轮runtime阶段：codex/runtime/aisoft_release/runner.py及相关release tests；只按既有environment精确判断，不改schema、不绕过guard。
若发现其它实际运行保护阻塞，先据实际调用链定位，不关闭全局guard或扩大生产权限。

## 非目标

无现场执行、安装、Secret操作、数据库迁移/恢复、服务重启、生产部署；不修改现有SCM服务资源。
允许工具路径不等于授权执行migrate；现场仍按项目批准的固定操作实施。

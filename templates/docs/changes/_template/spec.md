---
issue: ISSUE_NUMBER
gitea_url: ISSUE_URL
change_type: CHANGE_TYPE
requested_complexity: auto
assessed_complexity: ASSESSED_COMPLEXITY
effective_complexity: EFFECTIVE_COMPLEXITY
contract_effect: CONTRACT_EFFECT
confidence: CONFIDENCE
risk_flags: []
depends_on: []
git_scope:
  - GIT_SCOPE_PATH
branch: change/ISSUE_NUMBER-SHORT-SLUG
created: YYYY-MM-DD
updated: YYYY-MM-DD
---

# Spec template

<!-- TEMPLATE_CONDITIONAL:
简版或完整版按路由表「文档义务」：简版（small、无高风险 flag 的 development complex）
删除「接口、数据与兼容性影响」与「未决问题」两节，「风险与回滚约束」没有内容时也删除。
`git_scope` 列出本 Issue 全部映射文档与所有将提交的文件，每行一个仓库相对路径；
推送守卫只从已提交的 spec 读取它。
-->

## 目标与原因

## 范围与非范围

## Acceptance criteria

- [ ] 每项使用可观察、可验证的结果表述。

## 风险与回滚约束

## 接口、数据与兼容性影响

## 未决问题

进入 `approved` 前必须清空所有会改变实现方向的未决问题。

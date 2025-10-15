## 概述 (Summary)
请简要说明本次改动的目的与背景。

## 关联 Issue
- 主要 Epic / 父 Issue：#1 （若适用）
- 子 Issue / 任务：填写或移除，例如：#5

## 变更类型 (Type of Change)
- [ ] Feature
- [ ] Fix
- [ ] Refactor
- [ ] Docs
- [ ] Chore / Build

## 主要改动 (Highlights)
- 
- 

## 配置校验 (Config Validation)
- [ ] 执行 `python scripts/check_config.py` 结果 `degraded_ai=false`
- [ ] Config validation passed (yes/no): ____
- 若为 “no” 列出原因：
  - 

## 测试 (Testing)
### 手动验证
- [ ] AI 标准化 CLI 正常运行
- [ ] 邀请 CLI 正常运行（关键参数：organization / token）

### 自动测试
- [ ] 新增/更新单测通过：`pytest`
- [ ] 无破坏性回归

## 回滚策略 (Rollback Plan)
若需要紧急回滚，说明步骤或可安全移除的 commit。

## 兼容性 / 风险 (Risks)
- 影响范围：
- 潜在风险：
- 缓解措施：

## 截图 / 日志（可选）
附上关键信息（配置校验输出、AI 代码生成示例等）。

## Checklist
- [ ] README 已更新（若需要）
- [ ] 文档已更新（CONFIGURATION / Plan）
- [ ] 未引入敏感数据 / 未提交企业私有 CSV
- [ ] 通过 `scripts/scan_enterprise.py`

---
> 提示：保持 PR 聚焦单一主题；若新增 Task 建议先建 Issue，再在此引用。
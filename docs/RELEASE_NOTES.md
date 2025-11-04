# Release Notes - v0.2.1

**发布日期**：2025-10-31  
**分支**：Dev_Branch  
**PR/变更类型**：维护性更新（未发起 PR）

---

## 🎯 版本概述

- 固化仓库规范，新增 `*.csv` 忽略规则，避免测试数据误提交。
- README 加入版本与日期信息，指向最新 Release Notes，确保对外信息同步。
- 更新本文件以记录上述维护性改动并预留版本演进脉络。

---

## 🛠 改动详情

- **仓库规则**：`.gitignore` 新增 `*.csv`，覆盖所有 CSV 测试数据；如需长期保留，请在本地维护或压缩存档。
- **文档同步**：`README.md` 顶部新增“版本 + 日期 + Release Notes 链接”，便于读者快速确认当前版本。
- **版本记录**：在 `docs/RELEASE_NOTES.md` 添写 v0.2.1 条目；旧版 v0.2.0 内容保持不变并下移。

---

## ✅ 测试

- 2025-10-31：`pytest`（root）

---

# Release Notes - v0.2.0

**发布日期**：2025-10-15  
**分支**：feature/ai-config-validation  
**PR**：#6  
**关联 Issue**：#5

---

## 🎯 版本概述

本版本实现了**统一配置体系**和**AI 辅助数据标准化增强**，重点包括：
- 统一 AI/邀请配置变量命名（引入 API_TYPE 枚举）
- 实现配置验证框架和降级模式
- 修复关键 Bug（GitHub Models 401 认证、CSV 列顺序）
- 新增 17 个单元测试，覆盖率 100%

---

## ✨ 新功能

### 1. 统一配置变量命名

**迁移说明**：
```bash
# ❌ 旧版配置（已弃用）
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o
OPENAI_BASE_URL=...
OPENAI_API_VERSION=...

# ✅ 新版配置（推荐）
API_TYPE=openai          # 新增：供应商类型
API_KEY=sk-...           # 统一密钥名称
MODEL_NAME=gpt-4o        # 统一模型名称
API_BASE_URL=...         # 统一端点 URL
API_VERSION=...          # 统一 API 版本
```

### 2. 多供应商支持（API_TYPE）

| API_TYPE | 必需变量 | 自动配置 | 说明 |
|----------|---------|---------|------|
| `openai` | `API_KEY` | ✅ base_url | 默认 OpenAI 官方 API |
| `github` | `API_KEY` 或 `GITHUB_TOKEN` | ✅ base_url | GitHub Models（开发/测试） |
| `azure` | `API_KEY`, `API_BASE_URL` | ❌ | Azure OpenAI |
| `custom` | `API_KEY`, `API_BASE_URL` | ❌ | 自定义端点 |

### 3. 配置验证框架

**功能**：
- ✅ 启动时自动校验配置完整性
- ✅ 供应商特定规则矩阵验证
- ✅ 降级模式（AI 不可用不阻塞邀请流程）
- ✅ 密钥自动脱敏（日志安全）
- ✅ 友好的错误提示

**示例输出**：
```
配置验证摘要：✅ 有效 | Errors: 0 | Warnings: 0 | GitHub Models (gpt-4o)
```

### 4. CSV 列顺序标准化

**修复前**：列顺序随机
```
姓名,工号,Team,Mail,线上OR线下,Organization
```

**修复后**：强制顺序（Mail, Team, Organization 前三列）
```
Mail,Team,Organization,姓名,工号,线上OR线下
```

---

## 🐛 Bug 修复

### Bug #1: GitHub Models 401 认证错误
**问题**：设置 `API_TYPE=github` 但未自动配置 `base_url`，导致请求发送到 OpenAI  
**影响**：GitHub Models 用户无法正常使用  
**修复**：LLMService 自动配置 `base_url=https://models.github.ai/inference`

### Bug #2: CSV 列顺序不一致
**问题**：`_clean.csv` 列顺序随机，影响后续程序解析  
**影响**：邀请流程可能读取错误列  
**修复**：execute_transformation 添加列重排序逻辑

---

## 🧪 测试

### 单元测试
- **文件**：`tests/test_config_validation.py`
- **测试数量**：17 个
- **通过率**：100%
- **覆盖场景**：
  - ✅ OpenAI 基础验证（缺 API_KEY）
  - ✅ GitHub fallback 机制（GITHUB_TOKEN → API_KEY）
  - ✅ Azure 验证（缺 API_BASE_URL）
  - ✅ Custom 供应商验证
  - ✅ CLI 参数覆盖优先级
  - ✅ 密钥脱敏功能
  - ✅ 默认值填充

### 集成测试
- ✅ CLI `--help` 输出正确
- ✅ 配置错误时友好退出
- ✅ `scripts/check_config.py` JSON 输出格式正确
- ✅ 列顺序修复验证通过

---

## 📝 文档

### 新增文档
- **`docs/CONFIGURATION.md`**：完整配置指南
  - 环境变量详细说明
  - 供应商配置矩阵
  - 故障排查指南
  - 迁移步骤（OPENAI_* → API_*）

### 更新文档
- **`.env.example`**：新变量示例
- **`README.md`**：配置说明更新
- **`docs/requirements/req-ai-assisted-normalization.md`**：AC7 列顺序要求

---

## 🔄 向后兼容性

### ⚠️ 破坏性更改
- 环境变量重命名：`OPENAI_*` → `API_*`（需手动迁移）

### ✅ 兼容措施
- `GITHUB_TOKEN` 作为 `API_KEY` 的 fallback（带警告提示）
- 现有代码仍可使用旧变量名（临时过渡期）

### 📖 迁移指南

#### 1. OpenAI 用户
```bash
# 之前
export OPENAI_API_KEY=sk-...
export OPENAI_MODEL=gpt-4o

# 现在
export API_TYPE=openai
export API_KEY=sk-...
export MODEL_NAME=gpt-4o
```

#### 2. GitHub Models 用户
```bash
# 之前
export GITHUB_TOKEN=ghp_...
export OPENAI_MODEL=gpt-4o
export OPENAI_BASE_URL=https://models.github.ai/inference

# 现在（推荐）
export API_TYPE=github
export API_KEY=ghp_...     # 或使用 GITHUB_TOKEN
export MODEL_NAME=gpt-4o   # base_url 自动配置
```

#### 3. Azure OpenAI 用户
```bash
# 之前
export OPENAI_API_KEY=...
export OPENAI_BASE_URL=https://your-resource.openai.azure.com/openai/v1/
export OPENAI_MODEL=gpt-4o

# 现在
export API_TYPE=azure
export API_KEY=...
export API_BASE_URL=https://your-resource.openai.azure.com/openai/v1/
export MODEL_NAME=gpt-4o
```

---

## 📊 代码统计

- **新增文件**：2 个
  - `invitation/config_validation.py`
  - `tests/test_config_validation.py`
- **修改文件**：5 个
  - `invitation/ai_normalization_service.py`
  - `invitation/ai_normalizer_cli.py`
  - `docs/requirements/req-ai-assisted-normalization.md`
  - `.env.example`
  - `README.md`
- **测试通过**：17/17 ✅
- **代码行数**：+450 / -50

---

## 🚀 后续计划

### Task 6 剩余部分
- [ ] 在 `invitation/inviter.py` 中集成 `DEFAULT_ORGANIZATION` 和 `DEFAULT_TEAM_PREFIX` 支持
- [ ] 完善邀请流程的配置降级处理

### 优化改进
- [ ] 添加配置缓存机制（避免重复验证）
- [ ] 实现配置热重载功能
- [ ] 增加更多供应商支持（如 Anthropic Claude）

### 文档完善
- [ ] 添加视频教程（配置迁移步骤）
- [ ] 翻译英文文档
- [ ] 补充故障排查 FAQ

---

## 👥 贡献者

- **主要开发**：@DevOps-zhuang
- **代码审查**：待定
- **测试验证**：@DevOps-zhuang

---

## 📌 相关链接

- **Pull Request**：https://github.com/DevOps-zhuang/github_manager/pull/6
- **Issue #5**：https://github.com/DevOps-zhuang/github_manager/issues/5
- **Epic #1**：https://github.com/DevOps-zhuang/github_manager/issues/1
- **配置指南**：`docs/CONFIGURATION.md`

---

## 🙏 致谢

感谢 GitHub Copilot 在整个开发过程中提供的智能辅助！

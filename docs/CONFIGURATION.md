## 统一配置指南（AI 与邀请功能）

本文件描述项目在测试阶段采用的“统一环境变量”与“启动校验”规范。旧的 `OPENAI_*` 变量已移除，不再兼容。

---
## 1. 总览

| 目标 | 说明 |
|------|------|
| 明确供应商 | 使用 `API_TYPE` 区分 openai / github / azure / custom |
| 语义化命名 | 统一 `API_KEY`, `MODEL_NAME`, `API_BASE_URL` 等 |
| 可降级 | AI 配置错误不阻断邀请流程 |
| 可扩展 | future 第三方模型通过 `API_TYPE=custom` 适配 |

---
## 2. 环境变量定义

| 变量 | 必填条件 | 示例 | 说明 |
|------|---------|------|------|
| `API_TYPE` | 是 | `openai` | 模型供应商类型：`openai|github|azure|custom` |
| `API_KEY` | 见规则 | `sk-xxxxx` | 模型访问凭据；github 模型优先用它 |
| `MODEL_NAME` | 否 | `gpt-4o` | 默认 gpt-4o；github 内部自动处理命名映射 |
| `API_BASE_URL` | `azure/custom` 必填 | `https://xxx.openai.azure.com/openai/v1/` | openai/github 可留空 |
| `API_VERSION` | Azure 旧接口可选 | `2024-02-15-preview` | 大多数新接口可忽略 |
| `DEFAULT_ORGANIZATION` | 否 | `MyOrgX` | 邀请 CLI 默认组织（可被 --organization 覆盖） |
| `DEFAULT_TEAM_PREFIX` | 否 | `SH-` | 邀请时为团队名自动加前缀（若不存在） |
| `GITHUB_TOKEN` | 邀请功能 | `github_pat_xxx` | GitHub 邀请专用；`API_TYPE=github` 且 `API_KEY` 缺失时可作为回退（警告） |

---
## 3. API_TYPE 校验矩阵

| API_TYPE | 必填 | 可选 | 默认 | 说明 |
|----------|------|------|------|------|
| openai   | API_KEY | MODEL_NAME | MODEL_NAME=gpt-4o | 无需 BASE_URL |
| github   | API_KEY 或 (GITHUB_TOKEN 回退) | MODEL_NAME | MODEL_NAME=gpt-4o | 内部 endpoint |
| azure    | API_KEY, API_BASE_URL | MODEL_NAME, API_VERSION | MODEL_NAME=gpt-4o | BASE_URL 必填 |
| custom   | API_KEY, API_BASE_URL | MODEL_NAME | MODEL_NAME=gpt-4o | 代理/第三方 |

---
## 4. 优先级

```
CLI 参数 > 环境变量 > 内置默认
```

示例：`--model my-model` 覆盖 `MODEL_NAME`；未提供则回退环境变量；仍缺则使用默认 `gpt-4o`。

---
## 5. 典型配置示例

### OpenAI
```
API_TYPE=openai
API_KEY=sk-your-key
MODEL_NAME=gpt-4o
```

### GitHub Models
```
API_TYPE=github
API_KEY=ghu_or_finegrained_key   # 推荐
GITHUB_TOKEN=github_pat_for_invites
MODEL_NAME=gpt-4o
```

### Azure OpenAI
```
API_TYPE=azure
API_KEY=azure-key-xxx
API_BASE_URL=https://your-resource.openai.azure.com/openai/v1/
MODEL_NAME=gpt-4o
API_VERSION=2024-02-15-preview
```

### 自建代理
```
API_TYPE=custom
API_KEY=proxy-key-xxx
API_BASE_URL=https://my-proxy.internal/api/v1/
MODEL_NAME=gpt-4o
```

---
## 6. 启动校验逻辑 (设计)

模块：`invitation/config_validation.py`

伪代码结构：
```python
def validate_config(cli_overrides: dict) -> ValidationResult:
    env = load_env()
    effective = merge(cli_overrides, env, defaults)
    errors, warnings = [], []
    degraded_ai = False

    # 基础判断
    api_type = effective.get("API_TYPE")
    if api_type not in {"openai", "github", "azure", "custom"}:
        errors.append("Unsupported API_TYPE")
        degraded_ai = True

    # 针对 api_type 的必填检查
    # ...（按矩阵填充）

    # github 回退逻辑
    if api_type == "github" and not effective.get("API_KEY"):
        if effective.get("GITHUB_TOKEN"):
            warnings.append("API_KEY missing; falling back to GITHUB_TOKEN for model auth (not recommended)")
            effective["API_KEY"] = effective["GITHUB_TOKEN"]
        else:
            errors.append("GitHub model requires API_KEY or GITHUB_TOKEN")
            degraded_ai = True

    return ValidationResult(
        is_valid=not errors,
        degraded_ai=degraded_ai,
        errors=errors,
        warnings=warnings,
        effective=redact(effective)
    )
```

AI CLI 行为：
1. 调用 `validate_config` → 若 `degraded_ai=True` 输出摘要 + 退出码 0。
2. 否则继续 LLM 代码生成流程。

邀请 CLI 行为：
1. 调用 `validate_config` → 忽略 AI 相关 `errors`（作为 warnings 打印）。
2. 若存在 `DEFAULT_ORGANIZATION` 且未传 `--organization` → 自动使用。

---
## 7. 输出格式规范

启动时打印：
```
[CONFIG] api_type=openai model=gpt-4o ai_enabled=True default_org=Acme warnings=1 errors=0
```

脱敏：`sk-xxxxabcd` → `sk-x...cd`。

---
## 8. 降级策略

| 场景 | 结果 |
|------|------|
| 缺少 API_KEY (openai) | AI 禁用，CLI 退出（代码 0） |
| github 无 API_KEY 但有 GITHUB_TOKEN | 警告回退，AI 仍启用 |
| azure 缺 API_BASE_URL | AI 禁用 |
| custom 缺 API_BASE_URL | AI 禁用 |
| MODEL_NAME 缺失 | 使用默认 gpt-4o |

---
## 9. 常见错误与诊断

| 问题 | 可能原因 | 建议 |
|------|----------|------|
| AI CLI 提示已降级 | 配置缺失 | 运行 `python scripts/check_config.py` 复查 |
| GitHub 回退警告 | 忘记设置 API_KEY | 补充专用模型密钥（避免权限不足） |
| 邀请 CLI 未使用默认组织 | 未设置 DEFAULT_ORGANIZATION | 在 .env 添加并重试 |

---
## 10. 后续可扩展点（不在当前实现范围）

- 多模型优先级链（主→备）
- Profile 切换（dev / staging / prod）
- 自动探测可用 Endpoint

---
## 11. 变更记录（初版）

| 版本 | 内容 |
|------|------|
| v0.1 | 首次引入统一配置体系；移除 OPENAI_* 命名 |

---
若发现文档遗漏或需要新供应商支持，请在 PR 中补充“配置矩阵 + 降级策略”两节。

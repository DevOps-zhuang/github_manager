# 实施计划：AI 辅助的数据标准化工作流

## 1. 概述

本文档旨在将 `req-ai-assisted-normalization.md` 中定义的需求拆解为一系列可执行的开发任务。计划遵循敏捷思想，从搭建核心框架开始，逐步集成 AI 能力，最终完成端到端的交付。

**目标**：交付一个 MVP (Minimum Viable Product) 版本的命令行工具，允许用户通过自然语言指令完成 CSV 文件的标准化。

## 2. 技术选型与环境准备 (Task 0)

- **负责人**: TBD
- **状态**: 未开始
- **任务描述**:
  - [ ] **选择并添加 CLI 库**: 评估 `click` 或 `typer` 库用于构建用户友好的命令行交互界面。将其添加到 `requirements.txt`。
  - [ ] **选择并添加 LLM 库**: 引入 `openai` 或其他大语言模型提供商的官方 Python SDK。将其添加到 `requirements.txt`。
  - [ ] **配置环境变量**: 建立 `.env` 文件模板 (`.env.example`)，用于管理 `GITHUB_TOKEN` 和新增的 `LLM_API_KEY` 等敏感信息。确保 `.env` 文件在 `.gitignore` 中。

## 3. 核心任务分解

### Task 1: 搭建 CLI 框架与用户交互流程

- **负责人**: TBD
- **状态**: 未开始
- **依赖**: Task 0
- **任务描述**:
  - [ ] 创建一个新的主入口脚本，例如 `ai_normalizer.py`。
  - [ ] 使用选定的 CLI 库 (如 `click`) 实现基础的命令结构。
  - [ ] 实现引导式用户交互，依次提示用户输入：
    - `enterprise_key` (业务实体/项目名称)。
    - 源 CSV 文件的路径。
    - 自然语言描述的转换规则。
  - [ ] 实现对用户输入的初步校验（如文件是否存在）。
  - [ ] 在此阶段，只打印用户输入，不进行实际处理，以验证交互流程。

### Task 2: 实现智能目录与文件管理

- **负责人**: TBD
- **状态**: 未开始
- **依赖**: Task 1
- **任务描述**:
  - [ ] 基于用户输入的 `enterprise_key`，实现动态检查和创建 `invitation/customize/<Enterprise>/` 目录的逻辑。
  - [ ] 将用户提供的源 CSV 文件复制到上述专属目录中，以便后续处理和存档。
  - [ ] 设计并实现输出文件的命名和存放策略，例如，所有输出都存放在对应的 `customize` 目录下。

### Task 3: 集成 LLM 并设计提示工程 (Prompt Engineering)

- **负责人**: TBD
- **状态**: 未开始
- **依赖**: Task 1
- **任务描述**:
  - [ ] 创建一个独立的模块（如 `llm_service.py`）用于封装与大语言模型 API 的所有交互。
  - [ ] 设计核心的**系统提示 (System Prompt)**，该提示将指导 AI 的行为。内容应包括：
    - **角色定义**: "你是一个 Python 代码生成专家，专门为我们的数据处理框架生成 `normalizer` 脚本。"
    - **上下文**: 解释 `BaseNormalizer` 的结构，以及需要实现的 `transform` 方法。
    - **输入格式**: 告知 AI 它将收到源 CSV 的列头 (headers) 和用户的自然语言指令。
    - **输出要求**: 明确要求 AI 只返回纯 Python 代码字符串，不包含任何解释性文字。
    - **代码示例**: 提供一个或两个简单的、高质量的 `normalizer.py` 实现作为 few-shot 示例。
  - [ ] 实现一个函数，该函数读取源 CSV 的列头，结合用户的自然语言指令，组装成最终的提示，并发送给 LLM。
  - [ ] 从 LLM 的响应中提取生成的 Python 代码字符串。

### Task 4: 实现安全的代码生成与执行

- **负责人**: TBD
- **状态**: 未开始
- **依赖**: Task 2, Task 3
- **任务描述**:
  - [ ] 将从 LLM 获取的 Python 代码字符串，准确地保存到 `invitation/customize/<Enterprise>/normalizer.py`。
  - [ ] **关键任务**: 复用现有的 `invitation.pipeline` 模块来执行标准化。通过 `subprocess` 调用 `python -m invitation.pipeline <enterprise_key> <input_csv_path>`。
    - 这样做可以天然地利用项目已有的动态加载机制，并把新生成的代码运行在一个独立的进程中，提供了一定程度的隔离。
  - [ ] 捕获 `subprocess` 的输出和错误，判断标准化流程是否成功执行。
  - **安全考量**: 在此 MVP 阶段，我们信任 AI 生成的代码在 `pandas` 操作范围内是安全的。后续版本可引入更强的沙箱机制（如 Docker 或 `RestrictedPython`）作为增强。

### Task 5: 实现双文件输出与用户确认

- **负责人**: TBD
- **状态**: 未开始
- **依赖**: Task 4
- **任务描述**:
  - [ ] 修改或扩展 `invitation.pipeline`（或在其外部进行包装），使其在执行标准化后，能够根据需求生成两种文件：
    - `_clean.csv`: 只包含 `Mail`, `Organization`, `Team` 和其他用户要求的标准列。
    - `_report.csv`: 包含所有原始列，并追加所有标准列。
  - [ ] 在 CLI 中，实现标准化完成后的预览功能：读取 `_report.csv` 文件，向用户展示前 5 行数据。
  - [ ] 向用户提问：“数据预览如上，是否确认执行后续的邀请流程？”
  - [ ] 根据用户的确认，决定是结束流程还是调用 `invitation.inviter` 模块。

### Task 6: 统一模型/邀请配置与启动校验（新增）

- **负责人**: TBD
- **状态**: 未开始
- **依赖**: Task 1 （CLI 入口已建立）
- **任务描述**:
  - [ ] 引入新的统一变量命名：`API_TYPE`, `API_KEY`, `MODEL_NAME`, `API_BASE_URL`, `API_VERSION`（可选），`DEFAULT_ORGANIZATION`，`DEFAULT_TEAM_PREFIX`（可选），以及保留 `GITHUB_TOKEN`（仅用于 GitHub 邀请，不再作为模型主凭据）。
  - [ ] 移除并停止文档引用所有旧变量：`OPENAI_API_KEY`, `OPENAI_BASE_URL`, `OPENAI_MODEL`, `OPENAI_API_VERSION`。
  - [ ] 设计变量必填矩阵：
    | API_TYPE | 必填 | 可选 | 默认 | 说明 |
    |----------|------|------|------|------|
    | openai   | API_KEY | MODEL_NAME | MODEL_NAME=gpt-4o | 无需 BASE_URL |
    | github   | API_KEY（首选，缺失可回退 GITHUB_TOKEN） | MODEL_NAME | MODEL_NAME=gpt-4o | 内部映射 endpoint |
    | azure    | API_KEY, API_BASE_URL | MODEL_NAME, API_VERSION | MODEL_NAME=gpt-4o | BASE_URL 必填 |
    | custom   | API_KEY, API_BASE_URL | MODEL_NAME | MODEL_NAME=gpt-4o | 完全自定义 |
  - [ ] 生成配置校验模块（`invitation/config_validation.py`）：
    - 暴露函数：`validate_config(cli_overrides: dict) -> ValidationResult`。
    - 结构：`ValidationResult { is_valid: bool, degraded_ai: bool, errors: list[str], warnings: list[str], effective: dict }`。
    - 校验失败（AI 侧不可用）→ 记录 `degraded_ai=True`，允许非 AI 功能继续。
  - [ ] 在 `invitation/ai_normalizer_cli.py` 中：
    - 最早阶段调用校验；若 `degraded_ai=True` → 采用策略 A（本次确认：直接友好退出，exit code 0，并提示“请补齐配置后再运行 AI 标准化”）。
  - [ ] 在 `invitation/inviter.py` 中：
    - 支持从 env 读取 `DEFAULT_ORGANIZATION` 与 `DEFAULT_TEAM_PREFIX` 作为缺省值；CLI 显式参数优先级更高（CLI > ENV > 默认）。
  - [ ] 新增脚本：`scripts/check_config.py`，用于单独快速验证配置（输出 JSON/表格 + 着色警告）。
  - [ ] 新增文档：`docs/CONFIGURATION.md`（集中说明变量语义、优先级、示例、常见错误、排查建议）。
  - [ ] 更新 `.env.example` 与 `README.md` 配置章节，完全移除旧命名。
  - [ ] 定义日志输出格式（可选）：首次校验时打印一行摘要：`[CONFIG] api_type=..., model=..., ai_enabled=...`。
  - [ ] 约定密钥打印只保留前 4 + '***' + 后 2。
  - [ ] 预留 future placeholder：若未来新增供应商（如 bedrock / vertex），使用 `API_TYPE=custom` 方式接入，后续才扩展专用分支逻辑。

- **验收标准**:
  - 在缺少 `API_KEY`（openai 类型）运行 AI CLI → 友好退出并提示应补齐的字段。
  - 在 `API_TYPE=github` 且无 `API_KEY` 但有 `GITHUB_TOKEN` → 使用后者并提示“已回退”警告。
  - 在 `API_TYPE=azure` 缺失 `API_BASE_URL` → 输出错误并标记 `degraded_ai`。
  - 在邀请 CLI 中未传 `--organization` 但存在 `DEFAULT_ORGANIZATION` → 自动使用并打印来源说明。
  - `scripts/check_config.py` 返回非 0 退出码仅当存在结构性错误（如值非法），普通缺失导致 AI 降级返回 0（便于 CI 继续）。
  - 文档中有最少 3 组示例：OpenAI / GitHub Models / Azure。

- **风险与注意事项**:
  - 直接移除旧变量可能影响尚未同步环境的成员 → 需在 PR 描述高亮。
  - GitHub Token 既用作邀请又可能被误认为模型凭据 → 警告语需明确“仅在 API_KEY 缺失且 API_TYPE=github 时尝试回退”。
  - 自定义类型（custom）可能被误用 → 文档需强调其对接第三方代理或自建网关场景。

- **后续增强（非本任务范围）**:
  - 支持多模型候选链路（如：主模型失败 → 回退 cheap 模型）。
  - 输出配置快照加密缓存（避免重复解析 .env）。
  - 引入 profile（`CONFIG_PROFILE=dev|prod`）切换。


## 3. 里程碑 (Milestones)

- **M1: CLI 交互与文件管理完成**
  - 完成 Task 1, Task 2。
  - **可交付成果**: 一个可以接收用户输入并正确组织文件目录的命令行工具。

- **M2: AI 代码生成与执行打通**
  - 完成 Task 3, Task 4。
  - **可交付成果**: 工具能够根据用户指令调用 AI 生成代码，并执行该代码完成一次（可能不完美的）数据转换。

- **M3: MVP 版本完成**
  - 完成 Task 5，并进行端到端测试。
  - **可交付成果**: 一个功能完整的 MVP 版本，满足 `req-ai-assisted-normalization.md` 中定义的所有核心验收标准。

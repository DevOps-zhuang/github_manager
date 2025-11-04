# B/S架构部署分析总结

## 📋 文档导航

本次分析创建了两个核心文档，回答了如何将AI辅助数据标准化系统部署为B/S架构的问题：

### 1. 需求分析文档
📄 **文件路径**：`docs/requirements/req-bs-deployment-analysis.md`

**内容概要**：
- ✅ B/S架构整体设计（前后端架构图）
- ✅ 部署方案选择（单容器一体化 vs 分离部署）
- ✅ **自动生成Python代码的安全执行方案**（核心重点）
  - 三层防护机制（白名单验证 + 受限环境 + 超时控制）
  - 安全代码执行器（SafeCodeExecutor）详细设计
  - LLM代码生成约束Prompt
- ✅ 任务和会话持久化方案
- ✅ 多轮交互状态管理策略
- ✅ API接口设计规范
- ✅ 前端界面设计
- ✅ 安全性总结和验收清单

### 2. 实施指南文档
📄 **文件路径**：`docs/plans/plan-bs-implementation-guide.md`

**内容概要**：
- ✅ 完整目录结构设计
- ✅ 分阶段实施计划（Phase 1-3）
- ✅ **详细代码示例**（可直接复制使用）
  - Flask应用骨架
  - 认证系统（JWT）
  - 任务管理和文件上传
  - 安全代码执行器完整实现
  - 多轮对话接口
  - 中间件和错误处理
- ✅ 前端React实施计划
- ✅ 容器化部署方案（Dockerfile + docker-compose）
- ✅ 测试策略
- ✅ 部署清单

---

## 🎯 核心问题解答

### Q1: 如何部署为B/S结构？

**答案**：采用**单容器一体化部署**方案

```
┌─────────────────┐
│  用户浏览器     │ (React前端)
└────────┬────────┘
         │ HTTPS/REST API
┌────────┴────────┐
│  Flask Server   │ (后端API + 静态文件托管)
├─────────────────┤
│ - API接口层     │
│ - 业务服务层    │
│ - AI标准化服务  │
└────────┬────────┘
         │
┌────────┴────────┐
│  文件系统       │ (runtime/目录)
│ - tasks/       │
│ - uploads/     │
│ - results/     │
└─────────────────┘
```

**技术栈**：
- 后端：Python 3.12 + Flask 3.0
- 前端：React 18 + Vite
- 认证：JWT（3小时有效期）
- 持久化：JSON文件（基于文件系统）
- 部署：Docker（多阶段构建）

**优势**：
- ✅ 部署简单（一个容器）
- ✅ 无需额外数据库（文件系统持久化）
- ✅ 适合Phase 1单管理员场景
- ✅ 易于后续扩展（预留接口）

### Q2: 自动生成的Python代码如何安全执行？

**答案**：**三层防护机制 + 白名单验证 + 沙箱环境**

#### 防护层1：代码白名单验证

```python
# 允许的模块
ALLOWED_MODULES = ['pandas', 're', 'datetime', 'decimal', 'collections']

# 禁止的操作（正则检测）
FORBIDDEN_PATTERNS = [
    r'\bimport\s+os\b',        # 禁止文件系统访问
    r'\bimport\s+sys\b',       # 禁止系统调用
    r'\bimport\s+subprocess\b', # 禁止子进程
    r'\beval\b', r'\bexec\b',  # 禁止动态执行
    r'\bopen\b',               # 禁止文件打开
    r'__\w+__'                 # 禁止魔术方法
]
```

**验证流程**：
1. 检查import语句是否在白名单内
2. 扫描禁止的操作模式
3. 确认必须包含`def transform_data(df)`函数

#### 防护层2：受限执行环境（沙箱）

```python
# 构建受限的全局命名空间
safe_globals = {
    '__builtins__': {
        # 只允许安全的内置函数
        'len': len, 'str': str, 'int': int, 'float': float,
        'list': list, 'dict': dict, 'range': range, ...
        # 不包含：open, eval, exec, __import__, compile
    },
    'pd': pandas,  # 允许pandas
    're': re,      # 允许正则
}

# 在受限命名空间中执行
exec(compiled_code, safe_globals, local_namespace)
```

**沙箱特点**：
- ✅ 无法访问文件系统（无open函数）
- ✅ 无法执行系统命令（无os/sys/subprocess）
- ✅ 无法动态执行代码（无eval/exec）
- ✅ 无法导入任意模块（无__import__）

#### 防护层3：超时和异常隔离

```python
# 执行超时控制（默认30秒）
with timeout_context(30):
    exec(compiled_code, safe_globals, local_namespace)

# 异常捕获
try:
    result_df = transform_func(input_df.copy())
    return result_df, errors
except Exception as e:
    errors.append(f"转换错误: {str(e)}")
    return input_df, errors  # 返回原始数据，不中断流程
```

#### LLM代码生成约束

在Prompt中明确要求LLM遵守安全规则：

```
严格要求：
1. 只能使用以下模块：pandas, re, datetime, decimal, collections
2. 必须定义函数：def transform_data(df: pd.DataFrame) -> pd.DataFrame
3. 禁止使用：os, sys, subprocess, open, eval, exec, __import__
4. 不能访问文件系统或网络
5. 代码必须是纯函数，无副作用
```

#### 执行流程图

```
用户输入规则
    ↓
LLM生成代码（遵循安全约束）
    ↓
SafeCodeExecutor.validate_code()  ← 白名单验证（第一道防线）
    ↓
代码预览展示给用户（透明化）
    ↓
用户确认执行
    ↓
SafeCodeExecutor.execute_transformation()
    │
    ├─ 构建沙箱环境 ← 受限命名空间（第二道防线）
    ├─ 编译代码
    ├─ 执行转换（带超时） ← 超时控制（第三道防线）
    └─ 异常捕获 ← 错误隔离
    ↓
返回标准化结果 + 错误行
```

#### 安全等级评估

| 威胁类型 | 防护措施 | 安全等级 |
|---------|---------|---------|
| 恶意代码注入 | 白名单验证 + 模式扫描 | ⭐⭐⭐⭐⭐ |
| 文件系统访问 | 无open函数 + 禁止os/sys | ⭐⭐⭐⭐⭐ |
| 网络请求 | 无网络库 + 沙箱隔离 | ⭐⭐⭐⭐⭐ |
| 资源耗尽 | 超时控制（30秒） | ⭐⭐⭐⭐ |
| 无限循环 | 超时自动终止 | ⭐⭐⭐⭐ |
| 内存爆炸 | 同步执行 + 文件大小限制（1MB） | ⭐⭐⭐ |

**注意**：Phase 1的安全措施适合≤1MB文件的同步执行场景。未来如需处理更大文件或更高安全要求，建议升级到**Docker容器隔离执行**（Phase 2+）。

### Q3: 任务如何持久化？服务重启后数据是否丢失？

**答案**：**基于文件系统的JSON持久化**，服务重启后数据不丢失

#### 数据模型

```json
{
  "task_id": "uuid-12345",
  "status": "pending|interactive|applied",
  "created_at": "2025-11-01T10:00:00Z",
  "updated_at": "2025-11-01T10:05:00Z",
  "original_file": {
    "filename": "users.csv",
    "path": "runtime/uploads/uuid-12345_users.csv",
    "size": 1024
  },
  "analysis": {
    "row_count": 100,
    "column_count": 5,
    "columns": ["Name", "Email", "Phone", "Dept", "Status"]
  },
  "conversation": [
    {"role": "system", "content": "初始规则...", "timestamp": "..."},
    {"role": "user", "content": "请转小写", "timestamp": "..."},
    {"role": "assistant", "content": "已更新...", "timestamp": "..."}
  ],
  "rule_draft": {
    "description": "当前规则描述",
    "code": "生成的Python代码",
    "version": 3
  },
  "preview": {
    "rows": [...],  // 前20行
    "generated_at": "..."
  },
  "result": {
    "output_path": "runtime/results/normalized_users_20251101.csv",
    "error_path": "runtime/results/errors_uuid-12345.csv",
    "stats": {
      "total_rows": 100,
      "success_rows": 98,
      "error_rows": 2
    }
  }
}
```

#### 目录结构

```
runtime/
├── tasks/              # 任务元数据（JSON）
│   ├── uuid-001.json
│   ├── uuid-002.json
│   └── ...
├── uploads/            # 上传的原始文件
│   ├── uuid-001_original.csv
│   └── ...
└── results/            # 标准化结果
    ├── normalized_original_20251101.csv
    ├── errors_uuid-001.csv
    └── ...
```

#### 原子写入保证

```python
def save_task(self, task: dict) -> None:
    """原子写入，避免数据损坏"""
    task_file = self.tasks_dir / f"{task['task_id']}.json"
    temp_file = task_file.with_suffix('.json.tmp')
    
    # 1. 写入临时文件
    with temp_file.open('w', encoding='utf-8') as f:
        json.dump(task, f, indent=2, ensure_ascii=False)
    
    # 2. 原子替换（rename是原子操作）
    temp_file.replace(task_file)
```

#### 重启恢复

```python
# 服务启动时自动加载现有任务
def list_tasks(self, limit: int = 20) -> list[dict]:
    """列出最近的任务"""
    task_files = sorted(
        self.tasks_dir.glob("*.json"),
        key=lambda p: p.stat().st_mtime,  # 按修改时间排序
        reverse=True
    )[:limit]
    
    # 加载任务
    tasks = []
    for task_file in task_files:
        with task_file.open('r', encoding='utf-8') as f:
            tasks.append(json.load(f))
    
    return tasks
```

**优势**：
- ✅ 无需数据库（降低运维复杂度）
- ✅ 数据可读性强（JSON格式）
- ✅ 易于备份（直接复制runtime目录）
- ✅ 服务重启后任务仍可访问

### Q4: 多轮对话如何管理？上下文会膨胀吗？

**答案**：**上下文截断策略 + 摘要机制**

#### 对话膨胀问题

用户可能进行10+轮对话，每轮对话的上下文会累积：
- 问题：LLM token限制（如GPT-4的8K/32K）
- 影响：响应变慢、成本增加、可能超限

#### 解决方案：智能截断

```python
MAX_RECENT_TURNS = 8  # 保留最近8轮

def _truncate_conversation(self, messages: list) -> list:
    """截断对话历史，保留关键信息"""
    # 1. 保留第一条（系统初始规则）
    first_msg = messages[0]
    
    # 2. 保留最近N轮
    recent_msgs = messages[-self.MAX_RECENT_TURNS:]
    
    # 3. 生成中间摘要
    summary = {
        "role": "system",
        "content": f"[历史摘要: 共{len(messages) - self.MAX_RECENT_TURNS - 1}轮对话，"
                   f"主要修改了邮箱格式、部门映射、日期规范化]",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # 4. 组合：初始 + 摘要 + 最近N轮
    return [first_msg, summary] + recent_msgs
```

#### 上下文结构

```
[0] System: "初始规则建议：根据列名Email→Mail, Department→Team..."
[1] Summary: "[历史摘要: 5轮对话，修改了邮箱格式和部门映射]"
[2] User: "请将Email转为小写"
[3] Assistant: "已更新规则：Email列转小写..."
[4] User: "去除前后空格"
[5] Assistant: "已更新规则：Email列转小写并去除空格..."
[6] User: "部门'研发部'改为'R&D'"
[7] Assistant: "已更新规则：..."
[8] User: "添加Organization列默认值'MyCompany'"
[9] Assistant: "已更新规则：..."
```

**优势**：
- ✅ 始终保留初始上下文（重要）
- ✅ 保留最近对话（连贯性）
- ✅ 中间历史压缩为摘要（节省token）
- ✅ 控制总token数在合理范围

---

## 🚀 快速开始

### 开发环境

```bash
# 1. 安装后端依赖
pip install -r requirements-web.txt

# 2. 配置环境变量
export SECRET_KEY="your-secret-key"
export ADMIN_USERNAME="admin"
export ADMIN_PASSWORD="admin123"
export API_KEY="your-openai-api-key"

# 3. 启动后端
python -m web.app

# 4. 启动前端（另一个终端）
cd frontend
npm install
npm run dev

# 5. 访问应用
open http://localhost:3000
```

### 生产环境（Docker）

```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑 .env 文件

# 2. 构建并启动
docker-compose up -d

# 3. 检查健康状态
curl http://localhost:5000/api/health

# 4. 访问应用
open http://localhost:5000
```

---

## 📊 API接口一览

```
认证接口
  POST   /api/auth/login              # 登录获取token
  POST   /api/auth/password           # 修改密码（需认证）

任务管理接口
  POST   /api/normalize/tasks         # 上传CSV创建任务
  GET    /api/normalize/tasks         # 列出任务（可选）
  GET    /api/normalize/tasks/{id}    # 获取任务详情
  POST   /api/normalize/tasks/{id}/chat      # 多轮对话修改规则
  POST   /api/normalize/tasks/{id}/apply     # 确认执行标准化
  GET    /api/normalize/tasks/{id}/download  # 下载标准化结果
  GET    /api/normalize/tasks/{id}/errors    # 下载错误行文件

健康检查
  GET    /api/health                  # 服务健康状态
```

---

## ✅ 验收清单

Phase 1完成后，应通过以下验收：

- [ ] 用户可通过浏览器登录系统（POST /api/auth/login）
- [ ] 上传CSV文件（≤1MB）成功创建任务（返回task_id）
- [ ] 系统自动生成初始规则建议和预览（前20行）
- [ ] 用户可进行≥5轮对话修改规则
- [ ] 每轮对话后预览正确更新
- [ ] 用户确认后生成标准化结果文件（POST /apply）
- [ ] 可下载标准化结果CSV
- [ ] 可下载错误行CSV（如存在）
- [ ] 生成的Python代码经过安全验证（白名单检查通过）
- [ ] 服务重启后任务和结果仍可访问（持久化生效）
- [ ] 未登录用户无法访问受保护接口（返回401）
- [ ] 并行创建多个任务互不干扰（任务隔离）
- [ ] Docker容器可一键启动服务（docker-compose up）
- [ ] 错误响应不暴露内部堆栈信息（统一错误处理）
- [ ] 健康检查接口返回200（GET /api/health）

---

## 📚 相关文档

| 文档 | 路径 | 说明 |
|------|------|------|
| 原始需求 | `docs/requirements/req-web-interactive-standardization.md` | Phase 1完整需求 |
| 实施计划 | `docs/plans/plan-web-interactive-standardization.md` | 原始实施计划 |
| **部署分析** | `docs/requirements/req-bs-deployment-analysis.md` | **B/S架构需求分析（本次输出）** |
| **实施指南** | `docs/plans/plan-bs-implementation-guide.md` | **分阶段实施指南（本次输出）** |
| AI配置 | `docs/AI_CONFIGURATION.md` | LLM配置说明 |
| AI标准化 | `docs/AI_NORMALIZATION.md` | AI标准化使用指南 |

---

## 🔧 技术栈

| 类别 | 技术 | 版本 | 说明 |
|------|------|------|------|
| 语言 | Python | 3.12 | 后端核心语言 |
| Web框架 | Flask | 3.0+ | REST API服务 |
| 认证 | PyJWT | 2.8+ | JWT令牌管理 |
| 前端框架 | React | 18+ | 用户界面 |
| 构建工具 | Vite | 最新 | 前端构建 |
| HTTP客户端 | Axios | 最新 | API调用 |
| 数据处理 | Pandas | 2.0+ | CSV处理 |
| AI服务 | OpenAI SDK | 1.0+ | LLM集成 |
| 容器化 | Docker | 最新 | 部署容器 |
| 编排 | Docker Compose | 最新 | 多容器管理 |

---

## 🛡️ 安全性总结

| 层面 | 威胁 | 防护措施 | 状态 |
|------|------|----------|------|
| **代码执行** | 恶意代码注入 | 白名单验证 + 受限命名空间 + 超时控制 | ✅ 完善 |
| **文件上传** | 恶意文件 | 类型检查 + 大小限制（1MB） + 编码验证 | ✅ 完善 |
| **认证授权** | 未授权访问 | JWT令牌 + 中间件校验 + 令牌过期（3h） | ✅ 完善 |
| **数据泄露** | 敏感信息暴露 | 错误信息脱敏 + 不返回堆栈 | ✅ 完善 |
| **资源耗尽** | DoS攻击 | 文件大小限制 + 代码超时 + 同步执行 | ⚠️ 基础 |
| **会话劫持** | Token盗用 | HTTPS传输（生产） + 短过期时间 | ✅ 完善 |

**评级说明**：
- ✅ 完善：已实现多层防护，风险可控
- ⚠️ 基础：已有防护措施，但未来需增强（如rate limiting）

---

## 🔮 后续优化方向（Phase 2+）

| 优化项 | 优先级 | 说明 |
|--------|--------|------|
| **异步执行** | 高 | 引入Celery + Redis，支持大文件异步处理 |
| **Docker隔离执行** | 高 | 每次代码执行在独立容器中，最高安全等级 |
| **Rate Limiting** | 中 | API限流，防止滥用 |
| **WebSocket** | 中 | 实时预览更新和进度推送 |
| **规则版本管理** | 中 | 规则快照、比对、回滚 |
| **审计日志** | 中 | 详细的操作记录和回放 |
| **多组织支持** | 低 | 租户隔离、权限管理 |
| **GitHub App集成** | 低 | Webhook触发自动标准化 |

---

## 📞 联系与反馈

如有问题或建议，请：
1. 查看详细文档（本目录下的两个md文件）
2. 检查现有issue
3. 创建新issue并附上详细描述

---

**文档版本**：v1.0  
**创建日期**：2025-11-01  
**最后更新**：2025-11-01  
**作者**：AI Agent based on user requirements

---

**总结**：本次分析完整回答了如何将AI辅助数据标准化系统部署为B/S架构，特别是如何安全执行自动生成的Python代码。通过三层防护机制（白名单验证 + 沙箱环境 + 超时控制），在提供便利性的同时确保了系统安全性。整体方案采用单容器一体化部署，降低运维复杂度，并为后续扩展预留了接口空间。

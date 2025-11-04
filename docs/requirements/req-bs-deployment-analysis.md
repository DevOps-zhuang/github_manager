# B/S架构部署需求分析与实现建议

| 字段 | 内容 |
| ---- | ---- |
| 文件名 | `req-bs-deployment-analysis.md` |
| 关联需求 | `req-web-interactive-standardization.md`, `plan-web-interactive-standardization.md` |
| 状态 | 分析中 |
| 版本 | v1.0 |
| 日期 | 2025-11-01 |
| 作者 | AI Agent |

## 一、背景与问题陈述

根据 `req-web-interactive-standardization.md` 和 `plan-web-interactive-standardization.md` 的需求，我们需要将现有的CLI形式的AI辅助数据标准化系统改造为B/S（Browser/Server）架构的Web应用。核心挑战包括：

1. **如何部署为B/S结构**：前后端分离还是一体化部署？
2. **自动生成Python代码的安全执行**：如何安全运行AI生成的标准化代码并返回结果？
3. **任务和会话持久化**：如何确保服务重启后数据不丢失？
4. **多轮交互的状态管理**：如何维护用户的对话上下文？

## 二、B/S架构部署方案

### 2.1 整体架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                       用户浏览器 (Browser)                    │
│  ┌────────────┐  ┌────────────┐  ┌──────────────┐          │
│  │  登录界面  │  │  上传界面  │  │  对话/预览界面│          │
│  └────────────┘  └────────────┘  └──────────────┘          │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTPS / REST API
┌──────────────────────┴──────────────────────────────────────┐
│                    Flask Web Server (Server)                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  API Layer (Flask Blueprints)                       │   │
│  │  - /api/auth/* : 认证和会话管理                     │   │
│  │  - /api/normalize/* : 标准化任务管理                │   │
│  │  - /api/health : 健康检查                           │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Application Services                                │   │
│  │  - TaskRepository: 任务持久化                       │   │
│  │  - ConversationManager: 对话管理                    │   │
│  │  - NormalizationService: 标准化服务                 │   │
│  │  - CodeExecutor: 代码安全执行器 ★重点★              │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Domain Layer                                        │   │
│  │  - AINormalizationService (现有)                    │   │
│  │  - LLMService (现有)                                │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────┬───────────────────────────────────────┘
                      │
        ┌─────────────┴──────────────┐
        │ File System Persistence     │
        │ - runtime/tasks/           │
        │ - runtime/uploads/         │
        │ - runtime/results/         │
        └────────────────────────────┘
```

### 2.2 部署方案选择

**推荐方案：单容器一体化部署**

理由：
- Phase 1 目标是最小可用闭环，复杂度低
- 仅有管理员单角色，流量压力小
- 前端静态文件可由Flask直接托管
- 简化运维和部署流程

**具体实现：**

1. **后端Flask服务**：
   - 端口：5000（可配置）
   - 提供REST API接口
   - 托管React编译后的静态文件

2. **前端React应用**：
   - 开发：使用Vite本地开发服务器（端口3000）
   - 生产：编译为静态文件，放置在Flask的`static/`目录

3. **容器化**：
   ```dockerfile
   # 多阶段构建
   # Stage 1: 构建React前端
   FROM node:18 AS frontend-builder
   WORKDIR /app/frontend
   COPY frontend/package*.json ./
   RUN npm install
   COPY frontend/ ./
   RUN npm run build
   
   # Stage 2: Python后端 + 前端静态文件
   FROM python:3.12
   WORKDIR /app
   COPY requirements-web.txt ./
   RUN pip install -r requirements-web.txt
   COPY . ./
   COPY --from=frontend-builder /app/frontend/dist ./static
   EXPOSE 5000
   CMD ["python", "-m", "web.app"]
   ```

4. **本地开发模式**：
   - 后端：`python -m web.app`（端口5000）
   - 前端：`cd frontend && npm run dev`（端口3000，配置代理到5000）

### 2.3 网络和安全

1. **HTTPS支持**：
   - 开发：HTTP（本地/内网）
   - 生产：通过Nginx反向代理提供HTTPS

2. **CORS配置**：
   - 开发模式：允许localhost:3000
   - 生产模式：前后端同域，无需CORS

3. **会话管理**：
   - JWT令牌（存储在localStorage）
   - 过期时间：3小时
   - 刷新策略：过期后需重新登录

## 三、自动生成Python代码的安全执行方案

### 3.1 核心挑战

AI生成的标准化代码本质上是**不可信代码**，存在以下风险：
- 恶意代码注入（如文件删除、网络请求）
- 资源耗尽（无限循环、内存爆炸）
- 敏感信息泄露

### 3.2 安全执行策略

**方案一：代码白名单验证 + 受限执行环境（推荐）**

```python
class SafeCodeExecutor:
    """安全的代码执行器"""
    
    # 允许的模块白名单
    ALLOWED_MODULES = {
        'pandas', 're', 'datetime', 'decimal',
        'collections', 'itertools', 'functools'
    }
    
    # 禁止的操作黑名单
    FORBIDDEN_PATTERNS = [
        r'\bimport\s+os\b', r'\bimport\s+sys\b',
        r'\bimport\s+subprocess\b', r'\b__import__\b',
        r'\beval\b', r'\bexec\b', r'\bopen\b',
        r'\bfile\b', r'__.*__',  # 魔术方法
    ]
    
    def validate_code(self, code: str) -> tuple[bool, str]:
        """验证代码安全性"""
        # 1. 检查禁止模式
        for pattern in self.FORBIDDEN_PATTERNS:
            if re.search(pattern, code):
                return False, f"禁止的操作: {pattern}"
        
        # 2. 检查import语句
        imports = re.findall(r'import\s+(\w+)', code)
        for imp in imports:
            if imp not in self.ALLOWED_MODULES:
                return False, f"不允许的模块: {imp}"
        
        # 3. 检查必须包含transform_data函数
        if 'def transform_data(df):' not in code:
            return False, "缺少transform_data函数定义"
        
        return True, "代码验证通过"
    
    def execute_transformation(
        self, code: str, input_df: pd.DataFrame,
        timeout: int = 30
    ) -> tuple[pd.DataFrame, list[str]]:
        """在受限环境中执行转换代码"""
        # 1. 验证代码
        is_valid, message = self.validate_code(code)
        if not is_valid:
            raise SecurityError(message)
        
        # 2. 构建受限的全局命名空间
        safe_globals = {
            '__builtins__': {
                'len': len, 'str': str, 'int': int,
                'float': float, 'bool': bool, 'list': list,
                'dict': dict, 'set': set, 'tuple': tuple,
                'range': range, 'enumerate': enumerate,
                'zip': zip, 'map': map, 'filter': filter,
            },
            'pd': pd,
            're': re,
            'datetime': __import__('datetime'),
        }
        
        # 3. 编译代码（检查语法）
        try:
            compiled_code = compile(code, '<generated>', 'exec')
        except SyntaxError as e:
            raise SecurityError(f"语法错误: {e}")
        
        # 4. 执行代码（带超时）
        local_namespace = {}
        with timeout_context(timeout):
            exec(compiled_code, safe_globals, local_namespace)
        
        # 5. 调用transform_data函数
        transform_func = local_namespace.get('transform_data')
        if not transform_func:
            raise SecurityError("未找到transform_data函数")
        
        # 6. 执行转换并捕获错误
        errors = []
        try:
            result_df = transform_func(input_df.copy())
            return result_df, errors
        except Exception as e:
            errors.append(f"执行错误: {str(e)}")
            return input_df, errors
```

**方案二：Docker容器隔离执行（未来扩展）**

对于更高安全要求的场景，可以：
- 每次执行创建独立的Docker容器
- 在容器中运行生成的代码
- 限制容器资源（CPU、内存、网络）
- 执行完成后销毁容器

这个方案在Phase 1暂不实现，但架构需要预留接口。

### 3.3 代码生成规范

为确保AI生成的代码符合安全要求，需要在LLM的Prompt中明确约束：

```python
CODE_GENERATION_PROMPT = """
你是一个数据标准化代码生成助手。请根据用户的转换规则，生成Python代码。

严格要求：
1. 只能使用以下模块：pandas, re, datetime, decimal, collections
2. 必须定义函数：def transform_data(df: pd.DataFrame) -> pd.DataFrame
3. 禁止使用：os, sys, subprocess, open, eval, exec, __import__
4. 不能访问文件系统或网络
5. 代码必须是纯函数，无副作用
6. 对于无法处理的行，添加到errors列表而不是抛出异常

示例代码结构：
```python
import pandas as pd
import re

def transform_data(df):
    # 创建副本避免修改原数据
    result_df = df.copy()
    
    # 转换逻辑
    result_df['Mail'] = result_df['Email'].str.lower().str.strip()
    
    return result_df
```

用户规则：{user_rules}
当前列名：{columns}

请生成符合要求的Python代码：
"""
```

### 3.4 执行流程

```
用户输入规则
    ↓
LLM生成代码（遵循安全约束）
    ↓
SafeCodeExecutor.validate_code()  ← 第一道防线
    ↓
代码预览展示给用户（透明化）
    ↓
用户确认执行
    ↓
SafeCodeExecutor.execute_transformation()  ← 第二道防线
    ↓
返回标准化结果 + 错误行
```

## 四、任务和会话持久化方案

### 4.1 数据模型

**任务（Task）**：
```json
{
  "task_id": "uuid-xxxx",
  "status": "pending|interactive|applied",
  "created_at": "2025-11-01T10:00:00Z",
  "updated_at": "2025-11-01T10:05:00Z",
  "original_file": {
    "filename": "users.csv",
    "size": 1024,
    "path": "runtime/uploads/uuid-xxxx_users.csv",
    "encoding": "utf-8"
  },
  "analysis": {
    "row_count": 100,
    "column_count": 5,
    "columns": ["Name", "Email", "Phone", "Department", "Status"]
  },
  "rule_draft": {
    "description": "最新规则描述文本",
    "code": "生成的Python代码",
    "version": 3
  },
  "conversation": [
    {"role": "system", "content": "初始规则建议", "timestamp": "..."},
    {"role": "user", "content": "请将Email列转为小写", "timestamp": "..."},
    {"role": "assistant", "content": "已更新规则...", "timestamp": "..."}
  ],
  "preview": {
    "rows": [...],  // 前20行预览数据
    "generated_at": "2025-11-01T10:05:00Z"
  },
  "result": {
    "output_path": "runtime/results/normalized_users_20251101.csv",
    "error_path": "runtime/results/errors_uuid-xxxx.csv",
    "stats": {
      "total_rows": 100,
      "success_rows": 98,
      "error_rows": 2
    }
  }
}
```

### 4.2 持久化实现

**目录结构**：
```
runtime/
├── tasks/
│   ├── uuid-001.json
│   ├── uuid-002.json
│   └── ...
├── uploads/
│   ├── uuid-001_original.csv
│   └── ...
├── results/
│   ├── normalized_original_20251101.csv
│   ├── errors_uuid-001.csv
│   └── ...
└── sessions/
    └── session-xxx.json  # JWT令牌黑名单（可选）
```

**TaskRepository实现**：
```python
class TaskRepository:
    """任务持久化管理"""
    
    def __init__(self, base_path: Path = Path("runtime")):
        self.base_path = base_path
        self.tasks_dir = base_path / "tasks"
        self.uploads_dir = base_path / "uploads"
        self.results_dir = base_path / "results"
        
        # 确保目录存在
        for dir_path in [self.tasks_dir, self.uploads_dir, self.results_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def save_task(self, task: dict) -> None:
        """保存任务（原子写入）"""
        task_file = self.tasks_dir / f"{task['task_id']}.json"
        temp_file = task_file.with_suffix('.json.tmp')
        
        # 写入临时文件
        with temp_file.open('w', encoding='utf-8') as f:
            json.dump(task, f, indent=2, ensure_ascii=False)
        
        # 原子替换
        temp_file.replace(task_file)
    
    def load_task(self, task_id: str) -> dict | None:
        """加载任务"""
        task_file = self.tasks_dir / f"{task_id}.json"
        if not task_file.exists():
            return None
        
        with task_file.open('r', encoding='utf-8') as f:
            return json.load(f)
    
    def list_tasks(self, limit: int = 20) -> list[dict]:
        """列出最近的任务"""
        task_files = sorted(
            self.tasks_dir.glob("*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )[:limit]
        
        tasks = []
        for task_file in task_files:
            with task_file.open('r', encoding='utf-8') as f:
                tasks.append(json.load(f))
        
        return tasks
```

### 4.3 会话管理

**JWT令牌方案**：
```python
import jwt
from datetime import datetime, timedelta

class SessionManager:
    """会话管理"""
    
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.token_expiry = timedelta(hours=3)
    
    def create_token(self, username: str) -> str:
        """创建JWT令牌"""
        payload = {
            'username': username,
            'exp': datetime.utcnow() + self.token_expiry,
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def verify_token(self, token: str) -> dict | None:
        """验证令牌"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
```

## 五、多轮交互状态管理

### 5.1 对话上下文策略

**问题**：多轮对话后，上下文可能膨胀，影响性能和LLM token限制。

**解决方案**：
1. **保留最近N轮**：只保留最近8轮对话（用户+助手各4次）
2. **规则摘要**：将早期规则变更压缩为摘要
3. **重点保留**：始终保留初始分析和最新规则草稿

```python
class ConversationManager:
    """对话管理器"""
    
    MAX_RECENT_TURNS = 8  # 最近对话轮次
    
    def add_message(self, task_id: str, role: str, content: str):
        """添加消息"""
        task = self.task_repo.load_task(task_id)
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        }
        task['conversation'].append(message)
        
        # 自动截断
        if len(task['conversation']) > self.MAX_RECENT_TURNS + 2:
            task['conversation'] = self._truncate_conversation(
                task['conversation']
            )
        
        self.task_repo.save_task(task)
    
    def _truncate_conversation(self, messages: list) -> list:
        """截断对话历史，保留关键信息"""
        # 保留第一条（系统初始规则）
        first_msg = messages[0]
        
        # 保留最近N轮
        recent_msgs = messages[-self.MAX_RECENT_TURNS:]
        
        # 生成中间摘要
        summary = {
            "role": "system",
            "content": f"[历史摘要: 进行了{len(messages) - self.MAX_RECENT_TURNS - 1}轮对话]",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return [first_msg, summary] + recent_msgs
    
    def get_context_for_llm(self, task_id: str) -> list[dict]:
        """获取用于LLM的上下文"""
        task = self.task_repo.load_task(task_id)
        return task['conversation']
```

### 5.2 预览生成优化

预览只需要前20行数据，避免全量处理：

```python
def generate_preview(self, task_id: str, code: str) -> list[dict]:
    """生成预览（仅前20行）"""
    task = self.task_repo.load_task(task_id)
    
    # 只读取前25行（留5行缓冲）
    df = pd.read_csv(task['original_file']['path'], nrows=25)
    
    # 执行转换
    executor = SafeCodeExecutor()
    result_df, errors = executor.execute_transformation(code, df)
    
    # 返回前20行
    preview_rows = result_df.head(20).to_dict(orient='records')
    
    return preview_rows
```

## 六、API接口设计

### 6.1 认证接口

```
POST /api/auth/login
Request: {"username": "admin", "password": "***"}
Response: {"token": "jwt-token", "expires_in": 10800}

POST /api/auth/password
Request: {"old_password": "***", "new_password": "***"}
Headers: Authorization: Bearer <token>
Response: {"success": true}
```

### 6.2 任务管理接口

```
POST /api/normalize/tasks
Content-Type: multipart/form-data
Body: file=<csv file>
Response: {
  "task_id": "uuid",
  "analysis": {...},
  "initial_suggestion": "规则建议文本",
  "preview": [...]
}

GET /api/normalize/tasks/{task_id}
Response: {
  "task_id": "uuid",
  "status": "interactive",
  "rule_draft": {...},
  "preview": [...],
  "conversation": [...]
}

POST /api/normalize/tasks/{task_id}/chat
Body: {"message": "请将Email转为小写"}
Response: {
  "updated_rule": "...",
  "preview": [...],
  "conversation": [...]
}

POST /api/normalize/tasks/{task_id}/apply
Response: {
  "status": "applied",
  "stats": {...}
}

GET /api/normalize/tasks/{task_id}/download
Response: <CSV file>

GET /api/normalize/tasks/{task_id}/errors
Response: <CSV file> or 404
```

### 6.3 健康检查

```
GET /api/health
Response: {
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "..."
}
```

## 七、前端React界面设计

### 7.1 页面结构

```
├── LoginPage                 # 登录页
├── DashboardPage            # 主界面
│   ├── TaskList             # 任务列表（侧边栏）
│   └── TaskDetailPage       # 任务详情
│       ├── UploadZone       # 上传区域（新任务）
│       ├── ChatPanel        # 对话面板
│       ├── RuleDraftView    # 规则草稿展示
│       ├── PreviewTable     # 预览表格
│       ├── StatsCard        # 统计信息
│       └── ActionButtons    # 操作按钮（确认、下载）
└── SettingsPage             # 设置页（修改密码）
```

### 7.2 关键组件

**ChatPanel（对话面板）**：
```tsx
const ChatPanel = ({ taskId, conversation, onSendMessage }) => {
  return (
    <div className="chat-panel">
      <div className="messages">
        {conversation.map(msg => (
          <Message key={msg.timestamp} role={msg.role} content={msg.content} />
        ))}
      </div>
      <div className="input-area">
        <textarea placeholder="输入转换指令..." />
        <button onClick={onSendMessage}>发送</button>
      </div>
    </div>
  );
};
```

**PreviewTable（预览表格）**：
```tsx
const PreviewTable = ({ columns, rows }) => {
  return (
    <div className="preview-table">
      <div className="table-header">预览（前20行）</div>
      <table>
        <thead>
          <tr>
            {columns.map(col => <th key={col}>{col}</th>)}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, idx) => (
            <tr key={idx}>
              {columns.map(col => <td key={col}>{row[col]}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
```

## 八、部署和运维

### 8.1 环境变量配置

```env
# .env.example
# Flask配置
FLASK_ENV=production
SECRET_KEY=<生成的随机密钥>
PORT=5000

# 管理员凭证
ADMIN_USERNAME=admin
ADMIN_PASSWORD=<初始密码>

# LLM配置（继承现有）
API_TYPE=openai
API_KEY=<your-api-key>
MODEL_NAME=gpt-4o

# 存储路径
RUNTIME_DIR=./runtime
MAX_FILE_SIZE_MB=1

# 会话配置
SESSION_EXPIRY_HOURS=3
```

### 8.2 Docker Compose部署

```yaml
version: '3.8'

services:
  github-manager-web:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - SECRET_KEY=${SECRET_KEY}
      - ADMIN_USERNAME=${ADMIN_USERNAME}
      - ADMIN_PASSWORD=${ADMIN_PASSWORD}
      - API_KEY=${API_KEY}
    volumes:
      - ./runtime:/app/runtime
    restart: unless-stopped
```

### 8.3 运行方式

**开发模式**：
```bash
# 后端
python -m web.app

# 前端（另一个终端）
cd frontend && npm run dev
```

**生产模式（Docker）**：
```bash
docker-compose up -d
```

## 九、安全性总结

| 层面 | 威胁 | 防护措施 |
|------|------|----------|
| 代码执行 | 恶意代码注入 | 白名单验证 + 受限命名空间 + 超时控制 |
| 文件上传 | 恶意文件 | 文件类型检查 + 大小限制（1MB） + 编码验证 |
| 认证授权 | 未授权访问 | JWT令牌 + 中间件校验 + 令牌过期 |
| 数据泄露 | 敏感信息暴露 | 错误信息脱敏 + 不返回堆栈 |
| 资源耗尽 | DoS攻击 | 文件大小限制 + 代码超时 + 同步执行 |
| 会话劫持 | Token盗用 | HTTPS传输 + 短过期时间 |

## 十、后续优化方向（Phase 2+）

1. **异步执行**：引入Celery + Redis实现大文件异步处理
2. **Docker隔离执行**：每次代码执行在独立容器中运行
3. **资源限制**：CPU/内存配额、并发任务数限制
4. **审计日志**：详细的操作记录和回放
5. **WebSocket**：实时预览更新和进度推送
6. **规则版本管理**：规则快照、比对、回滚
7. **多组织支持**：租户隔离、权限管理

## 十一、验收检查清单

Phase 1完成后，应通过以下验收：

- [ ] 用户可通过浏览器登录系统
- [ ] 上传CSV文件（≤1MB）成功创建任务
- [ ] 系统自动生成初始规则建议和预览
- [ ] 用户可进行≥5轮对话修改规则
- [ ] 每轮对话后预览正确更新
- [ ] 用户确认后生成标准化结果文件
- [ ] 可下载标准化结果和错误行文件
- [ ] 生成的Python代码经过安全验证
- [ ] 服务重启后任务和结果仍可访问
- [ ] 未登录用户无法访问受保护接口
- [ ] 并行创建多个任务互不干扰
- [ ] Docker容器可一键启动服务
- [ ] 错误响应不暴露内部堆栈信息

---

**总结**：本文档提供了将AI辅助数据标准化系统部署为B/S架构的完整方案，重点解决了自动生成Python代码的安全执行问题。通过代码白名单验证、受限执行环境、多层防护机制，确保系统在提供便利性的同时保障安全性。整体架构采用单容器一体化部署，降低运维复杂度，为后续扩展预留了接口空间。

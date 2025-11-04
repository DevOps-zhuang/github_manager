# B/S架构实现指南

| 字段 | 内容 |
| ---- | ---- |
| 文件名 | `plan-bs-implementation-guide.md` |
| 关联文档 | `req-bs-deployment-analysis.md` |
| 状态 | 实施中 |
| 版本 | v1.0 |
| 日期 | 2025-11-01 |
| 作者 | AI Agent |

## 一、实施概览

本文档基于 `req-bs-deployment-analysis.md` 的需求分析，提供具体的分阶段实施建议。

### 1.1 实施原则

1. **增量开发**：每个阶段产出可运行的系统
2. **最小改动**：复用现有AI标准化服务代码
3. **安全优先**：代码执行安全在第一阶段就要到位
4. **持续测试**：每个功能完成后立即测试

### 1.2 技术栈确认

**后端**：
- Flask 3.0+ （Web框架）
- Flask-CORS （开发模式跨域）
- PyJWT （JWT令牌）
- 复用现有：pandas, openai, python-dotenv

**前端**：
- React 18+ （UI框架）
- Vite （构建工具）
- Axios （HTTP客户端）
- TailwindCSS 或 Ant Design （UI组件）

**部署**：
- Docker + Docker Compose
- Nginx（可选，用于生产HTTPS）

## 二、目录结构设计

```
github_manager/
├── web/                          # 新增：Web服务
│   ├── __init__.py
│   ├── app.py                   # Flask应用入口
│   ├── config.py                # 配置管理
│   ├── blueprints/              # API蓝图
│   │   ├── __init__.py
│   │   ├── auth.py             # 认证接口
│   │   ├── normalize.py        # 标准化接口
│   │   └── health.py           # 健康检查
│   ├── services/                # 业务服务层
│   │   ├── __init__.py
│   │   ├── task_repository.py  # 任务持久化
│   │   ├── conversation_manager.py  # 对话管理
│   │   ├── code_executor.py    # 安全代码执行器
│   │   └── normalization_service.py  # 标准化服务包装
│   ├── middleware/              # 中间件
│   │   ├── __init__.py
│   │   ├── auth_middleware.py  # JWT验证
│   │   └── error_handler.py    # 统一错误处理
│   └── utils/                   # 工具函数
│       ├── __init__.py
│       ├── session_manager.py  # 会话管理
│       └── file_helper.py      # 文件操作
├── frontend/                    # 新增：前端项目
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   ├── src/
│   │   ├── main.jsx
│   │   ├── App.jsx
│   │   ├── api/                # API调用
│   │   │   └── client.js
│   │   ├── pages/              # 页面
│   │   │   ├── LoginPage.jsx
│   │   │   ├── DashboardPage.jsx
│   │   │   └── TaskDetailPage.jsx
│   │   ├── components/         # 组件
│   │   │   ├── ChatPanel.jsx
│   │   │   ├── PreviewTable.jsx
│   │   │   ├── UploadZone.jsx
│   │   │   └── RuleDraftView.jsx
│   │   └── utils/              # 工具
│   │       └── auth.js
├── runtime/                     # 新增：运行时数据（.gitignore）
│   ├── tasks/
│   ├── uploads/
│   └── results/
├── invitation/                  # 现有：核心逻辑（复用）
├── tests/                       # 现有 + 新增Web测试
├── requirements.txt             # 现有
├── requirements-web.txt         # 新增：Web依赖
├── Dockerfile                   # 新增
├── docker-compose.yml           # 新增
└── README.md                    # 更新

```

## 三、分阶段实施计划

### Phase 1：后端基础框架（Day 1-2）

**目标**：搭建Flask骨架，实现认证和健康检查

#### 步骤1.1：创建Flask应用

**文件：`web/app.py`**

```python
"""Flask Web Application for AI Normalization Service."""

from flask import Flask, jsonify
from flask_cors import CORS
from pathlib import Path
import os

from web.blueprints.auth import auth_bp
from web.blueprints.normalize import normalize_bp
from web.blueprints.health import health_bp
from web.middleware.error_handler import register_error_handlers
from web.config import Config


def create_app(config=None):
    """Application factory."""
    app = Flask(__name__)
    
    # Load configuration
    if config:
        app.config.from_object(config)
    else:
        app.config.from_object(Config)
    
    # Enable CORS for development
    if app.config['ENV'] == 'development':
        CORS(app, origins=["http://localhost:3000"])
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(normalize_bp, url_prefix='/api/normalize')
    app.register_blueprint(health_bp, url_prefix='/api')
    
    # Register error handlers
    register_error_handlers(app)
    
    # Ensure runtime directories exist
    runtime_dir = Path(app.config['RUNTIME_DIR'])
    for subdir in ['tasks', 'uploads', 'results']:
        (runtime_dir / subdir).mkdir(parents=True, exist_ok=True)
    
    return app


if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
```

**文件：`web/config.py`**

```python
"""Application configuration."""

import os
from pathlib import Path


class Config:
    """Base configuration."""
    
    # Flask
    ENV = os.environ.get('FLASK_ENV', 'production')
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Admin credentials
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')
    
    # Session
    SESSION_EXPIRY_HOURS = int(os.environ.get('SESSION_EXPIRY_HOURS', 3))
    
    # File upload
    MAX_FILE_SIZE_MB = int(os.environ.get('MAX_FILE_SIZE_MB', 1))
    MAX_CONTENT_LENGTH = MAX_FILE_SIZE_MB * 1024 * 1024
    ALLOWED_EXTENSIONS = {'csv'}
    
    # Runtime storage
    RUNTIME_DIR = Path(os.environ.get('RUNTIME_DIR', './runtime'))
    
    # LLM (inherit from existing env vars)
    API_TYPE = os.environ.get('API_TYPE', 'openai')
    API_KEY = os.environ.get('API_KEY') or os.environ.get('GITHUB_TOKEN')
    MODEL_NAME = os.environ.get('MODEL_NAME', 'gpt-4o')
    API_BASE_URL = os.environ.get('API_BASE_URL')
```

#### 步骤1.2：实现认证蓝图

**文件：`web/blueprints/auth.py`**

```python
"""Authentication blueprint."""

from flask import Blueprint, request, jsonify, current_app
from web.utils.session_manager import SessionManager

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['POST'])
def login():
    """Admin login."""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    # Validate credentials
    if (username == current_app.config['ADMIN_USERNAME'] and 
        password == current_app.config['ADMIN_PASSWORD']):
        
        # Create session token
        session_mgr = SessionManager(current_app.config['SECRET_KEY'])
        token = session_mgr.create_token(username)
        
        return jsonify({
            'token': token,
            'expires_in': current_app.config['SESSION_EXPIRY_HOURS'] * 3600,
            'username': username
        }), 200
    else:
        return jsonify({'error': '认证失败'}), 401


@auth_bp.route('/password', methods=['POST'])
def change_password():
    """Change admin password (requires authentication)."""
    # TODO: Implement password change with token verification
    return jsonify({'error': 'Not implemented yet'}), 501
```

**文件：`web/utils/session_manager.py`**

```python
"""Session management with JWT."""

import jwt
from datetime import datetime, timedelta
from typing import Optional


class SessionManager:
    """JWT-based session manager."""
    
    def __init__(self, secret_key: str, expiry_hours: int = 3):
        self.secret_key = secret_key
        self.expiry_hours = expiry_hours
    
    def create_token(self, username: str) -> str:
        """Create JWT token."""
        payload = {
            'username': username,
            'exp': datetime.utcnow() + timedelta(hours=self.expiry_hours),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def verify_token(self, token: str) -> Optional[dict]:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(
                token, self.secret_key, algorithms=['HS256']
            )
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
```

#### 步骤1.3：实现健康检查

**文件：`web/blueprints/health.py`**

```python
"""Health check blueprint."""

from flask import Blueprint, jsonify
from datetime import datetime

health_bp = Blueprint('health', __name__)


@health_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'version': '1.0.0',
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }), 200
```

#### 步骤1.4：实现错误处理

**文件：`web/middleware/error_handler.py`**

```python
"""Unified error handling."""

from flask import jsonify
from werkzeug.exceptions import HTTPException


def register_error_handlers(app):
    """Register error handlers."""
    
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({'error': '请求参数错误', 'code': 'BAD_REQUEST'}), 400
    
    @app.errorhandler(401)
    def unauthorized(e):
        return jsonify({'error': '未授权访问', 'code': 'UNAUTHORIZED'}), 401
    
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'error': '资源不存在', 'code': 'NOT_FOUND'}), 404
    
    @app.errorhandler(413)
    def request_entity_too_large(e):
        return jsonify({'error': '文件过大', 'code': 'FILE_TOO_LARGE'}), 413
    
    @app.errorhandler(500)
    def internal_error(e):
        # Do not expose internal stack trace
        return jsonify({'error': '服务器内部错误', 'code': 'INTERNAL_ERROR'}), 500
    
    @app.errorhandler(Exception)
    def handle_exception(e):
        # Log the error (but don't expose to client)
        app.logger.error(f"Unhandled exception: {e}", exc_info=True)
        
        if isinstance(e, HTTPException):
            return jsonify({'error': e.description, 'code': e.name}), e.code
        
        return jsonify({'error': '服务器错误', 'code': 'UNKNOWN_ERROR'}), 500
```

#### 步骤1.5：创建依赖文件

**文件：`requirements-web.txt`**

```
# Web framework
flask>=3.0.0
flask-cors>=4.0.0

# JWT
pyjwt>=2.8.0

# Include base requirements
-r requirements.txt
```

#### 步骤1.6：测试Phase 1

```bash
# 安装依赖
pip install -r requirements-web.txt

# 运行服务
python -m web.app

# 测试健康检查
curl http://localhost:5000/api/health

# 测试登录
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

**预期输出**：
- 健康检查返回200和JSON响应
- 登录成功返回token
- 错误凭证返回401

---

### Phase 2：任务管理和文件上传（Day 3-4）

**目标**：实现任务创建、文件上传、任务持久化

#### 步骤2.1：实现TaskRepository

**文件：`web/services/task_repository.py`**

```python
"""Task persistence layer."""

import json
import uuid
from pathlib import Path
from typing import Optional
from datetime import datetime


class TaskRepository:
    """Manages task persistence using JSON files."""
    
    def __init__(self, base_path: Path):
        self.base_path = Path(base_path)
        self.tasks_dir = self.base_path / 'tasks'
        self.uploads_dir = self.base_path / 'uploads'
        self.results_dir = self.base_path / 'results'
        
        # Ensure directories exist
        for dir_path in [self.tasks_dir, self.uploads_dir, self.results_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def create_task(self, original_filename: str, file_path: Path, 
                   analysis: dict) -> dict:
        """Create a new task."""
        task_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat() + 'Z'
        
        task = {
            'task_id': task_id,
            'status': 'pending',  # pending -> interactive -> applied
            'created_at': now,
            'updated_at': now,
            'original_file': {
                'filename': original_filename,
                'path': str(file_path),
                'size': file_path.stat().st_size
            },
            'analysis': analysis,
            'conversation': [],
            'rule_draft': None,
            'preview': None,
            'result': None
        }
        
        self.save_task(task)
        return task
    
    def save_task(self, task: dict) -> None:
        """Save task with atomic write."""
        task['updated_at'] = datetime.utcnow().isoformat() + 'Z'
        task_file = self.tasks_dir / f"{task['task_id']}.json"
        temp_file = task_file.with_suffix('.json.tmp')
        
        # Write to temp file
        with temp_file.open('w', encoding='utf-8') as f:
            json.dump(task, f, indent=2, ensure_ascii=False)
        
        # Atomic replace
        temp_file.replace(task_file)
    
    def load_task(self, task_id: str) -> Optional[dict]:
        """Load task by ID."""
        task_file = self.tasks_dir / f"{task_id}.json"
        if not task_file.exists():
            return None
        
        with task_file.open('r', encoding='utf-8') as f:
            return json.load(f)
    
    def list_tasks(self, limit: int = 20) -> list[dict]:
        """List recent tasks."""
        task_files = sorted(
            self.tasks_dir.glob("*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )[:limit]
        
        tasks = []
        for task_file in task_files:
            if not task_file.name.endswith('.tmp'):
                with task_file.open('r', encoding='utf-8') as f:
                    tasks.append(json.load(f))
        
        return tasks
```

#### 步骤2.2：实现文件上传接口

**文件：`web/blueprints/normalize.py`（部分）**

```python
"""Normalization blueprint."""

from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from pathlib import Path
import pandas as pd

from web.services.task_repository import TaskRepository
from invitation.ai_normalization_service import AINormalizationService, LLMService
from web.middleware.auth_middleware import require_auth

normalize_bp = Blueprint('normalize', __name__)


def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


@normalize_bp.route('/tasks', methods=['POST'])
@require_auth
def create_task():
    """Upload CSV and create normalization task."""
    # Check file in request
    if 'file' not in request.files:
        return jsonify({'error': '未提供文件', 'code': 'NO_FILE'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': '文件名为空', 'code': 'EMPTY_FILENAME'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': '不支持的文件类型', 'code': 'INVALID_FILE_TYPE'}), 400
    
    # Save uploaded file
    filename = secure_filename(file.filename)
    runtime_dir = Path(current_app.config['RUNTIME_DIR'])
    temp_id = str(uuid.uuid4())
    upload_path = runtime_dir / 'uploads' / f"{temp_id}_{filename}"
    file.save(upload_path)
    
    # Analyze CSV
    try:
        llm_service = LLMService(
            api_key=current_app.config['API_KEY'],
            model=current_app.config['MODEL_NAME'],
            base_url=current_app.config.get('API_BASE_URL')
        )
        ai_service = AINormalizationService(llm_service=llm_service)
        analysis = ai_service.analyze_csv(upload_path)
    except Exception as e:
        current_app.logger.error(f"CSV analysis failed: {e}")
        return jsonify({'error': 'CSV分析失败', 'code': 'ANALYSIS_ERROR'}), 400
    
    # Create task
    task_repo = TaskRepository(runtime_dir)
    task = task_repo.create_task(filename, upload_path, analysis)
    
    # Generate initial rule suggestion
    try:
        initial_suggestion = "初始规则建议：根据列名自动映射..."  # TODO: Call LLM
        preview_rows = []  # TODO: Generate preview
        
        task['conversation'].append({
            'role': 'system',
            'content': initial_suggestion,
            'timestamp': task['updated_at']
        })
        task['status'] = 'interactive'
        task_repo.save_task(task)
        
        return jsonify({
            'task_id': task['task_id'],
            'analysis': analysis,
            'initial_suggestion': initial_suggestion,
            'preview': preview_rows
        }), 201
    except Exception as e:
        current_app.logger.error(f"Rule generation failed: {e}")
        return jsonify({'error': '规则生成失败', 'code': 'RULE_GEN_ERROR'}), 500
```

#### 步骤2.3：实现认证中间件

**文件：`web/middleware/auth_middleware.py`**

```python
"""Authentication middleware."""

from functools import wraps
from flask import request, jsonify, current_app
from web.utils.session_manager import SessionManager


def require_auth(f):
    """Decorator to require authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get token from header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': '未授权', 'code': 'UNAUTHORIZED'}), 401
        
        token = auth_header.split(' ')[1]
        
        # Verify token
        session_mgr = SessionManager(current_app.config['SECRET_KEY'])
        payload = session_mgr.verify_token(token)
        
        if not payload:
            return jsonify({'error': '令牌无效或已过期', 'code': 'INVALID_TOKEN'}), 401
        
        # Attach user info to request
        request.user = payload
        
        return f(*args, **kwargs)
    
    return decorated_function
```

---

### Phase 3：多轮对话和预览（Day 5-7）

**目标**：实现对话接口、规则更新、预览生成

#### 步骤3.1：实现安全代码执行器

**文件：`web/services/code_executor.py`**

```python
"""Safe code execution engine."""

import re
import pandas as pd
from typing import Tuple, List
import signal
from contextlib import contextmanager


class SecurityError(Exception):
    """Code security violation."""
    pass


class TimeoutError(Exception):
    """Execution timeout."""
    pass


@contextmanager
def timeout_context(seconds: int):
    """Context manager for execution timeout."""
    def timeout_handler(signum, frame):
        raise TimeoutError("代码执行超时")
    
    # Set signal handler
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)
    
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)


class SafeCodeExecutor:
    """Safe execution of generated transformation code."""
    
    # Allowed modules
    ALLOWED_MODULES = {
        'pandas', 'pd', 're', 'datetime', 'decimal',
        'collections', 'itertools', 'functools', 'math'
    }
    
    # Forbidden patterns
    FORBIDDEN_PATTERNS = [
        r'\bimport\s+os\b', r'\bimport\s+sys\b',
        r'\bimport\s+subprocess\b', r'\b__import__\b',
        r'\beval\b', r'\bexec\b', r'\bopen\b',
        r'\bfile\b', r'__\w+__',  # Dunder methods (except allowed)
        r'\bcompile\b', r'\bglobals\b', r'\blocals\b',
    ]
    
    def validate_code(self, code: str) -> Tuple[bool, str]:
        """Validate code safety."""
        # Check forbidden patterns
        for pattern in self.FORBIDDEN_PATTERNS:
            if re.search(pattern, code, re.IGNORECASE):
                return False, f"禁止的操作: {pattern}"
        
        # Check imports
        import_matches = re.findall(r'import\s+(\w+)', code)
        from_matches = re.findall(r'from\s+(\w+)', code)
        all_imports = import_matches + from_matches
        
        for imp in all_imports:
            if imp not in self.ALLOWED_MODULES:
                return False, f"不允许的模块: {imp}"
        
        # Check required function
        if 'def transform_data(' not in code:
            return False, "缺少transform_data函数定义"
        
        return True, "代码验证通过"
    
    def execute_transformation(
        self, 
        code: str, 
        input_df: pd.DataFrame,
        timeout: int = 30
    ) -> Tuple[pd.DataFrame, List[str]]:
        """Execute transformation code safely."""
        # Validate
        is_valid, message = self.validate_code(code)
        if not is_valid:
            raise SecurityError(message)
        
        # Build safe globals
        safe_globals = {
            '__builtins__': {
                'len': len, 'str': str, 'int': int, 'float': float,
                'bool': bool, 'list': list, 'dict': dict, 'set': set,
                'tuple': tuple, 'range': range, 'enumerate': enumerate,
                'zip': zip, 'map': map, 'filter': filter, 'sum': sum,
                'min': max, 'max': max, 'abs': abs, 'round': round,
                'sorted': sorted, 'reversed': reversed,
                'True': True, 'False': False, 'None': None,
            },
            'pd': pd,
            're': re,
        }
        
        # Compile code
        try:
            compiled_code = compile(code, '<generated>', 'exec')
        except SyntaxError as e:
            raise SecurityError(f"语法错误: {e}")
        
        # Execute with timeout
        local_namespace = {}
        try:
            with timeout_context(timeout):
                exec(compiled_code, safe_globals, local_namespace)
        except TimeoutError:
            raise
        except Exception as e:
            raise SecurityError(f"执行错误: {e}")
        
        # Get transform function
        transform_func = local_namespace.get('transform_data')
        if not transform_func:
            raise SecurityError("未找到transform_data函数")
        
        # Execute transformation
        errors = []
        try:
            result_df = transform_func(input_df.copy())
            return result_df, errors
        except Exception as e:
            errors.append(f"转换错误: {str(e)}")
            return input_df, errors
```

#### 步骤3.2：实现对话接口

继续完善 `web/blueprints/normalize.py`：

```python
@normalize_bp.route('/tasks/<task_id>/chat', methods=['POST'])
@require_auth
def chat(task_id):
    """Multi-turn conversation for rule refinement."""
    data = request.get_json()
    user_message = data.get('message', '').strip()
    
    if not user_message:
        return jsonify({'error': '消息不能为空', 'code': 'EMPTY_MESSAGE'}), 400
    
    # Load task
    task_repo = TaskRepository(Path(current_app.config['RUNTIME_DIR']))
    task = task_repo.load_task(task_id)
    
    if not task:
        return jsonify({'error': '任务不存在', 'code': 'TASK_NOT_FOUND'}), 404
    
    if task['status'] == 'applied':
        return jsonify({'error': '任务已锁定', 'code': 'TASK_LOCKED'}), 400
    
    # Add user message to conversation
    task['conversation'].append({
        'role': 'user',
        'content': user_message,
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    })
    
    # Call LLM to update rule
    try:
        # TODO: Implement LLM call with conversation context
        # For now, mock response
        updated_rule_description = f"已根据指令'{user_message}'更新规则..."
        generated_code = "import pandas as pd\n\ndef transform_data(df):\n    return df"
        
        task['rule_draft'] = {
            'description': updated_rule_description,
            'code': generated_code,
            'version': (task['rule_draft']['version'] if task['rule_draft'] else 0) + 1
        }
        
        # Generate preview
        preview_rows = generate_preview(task, generated_code)
        task['preview'] = {
            'rows': preview_rows,
            'generated_at': datetime.utcnow().isoformat() + 'Z'
        }
        
        # Add assistant response
        task['conversation'].append({
            'role': 'assistant',
            'content': updated_rule_description,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })
        
        # Save task
        task_repo.save_task(task)
        
        return jsonify({
            'updated_rule': task['rule_draft'],
            'preview': preview_rows,
            'conversation': task['conversation'][-6:]  # Return recent 6 messages
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Chat processing failed: {e}")
        return jsonify({'error': '对话处理失败', 'code': 'CHAT_ERROR'}), 500


def generate_preview(task: dict, code: str, limit: int = 20) -> list:
    """Generate preview by executing code on first N rows."""
    try:
        # Load first N rows
        df = pd.read_csv(task['original_file']['path'], nrows=limit + 5)
        
        # Execute transformation
        executor = SafeCodeExecutor()
        result_df, errors = executor.execute_transformation(code, df)
        
        # Convert to list of dicts
        preview_rows = result_df.head(limit).to_dict(orient='records')
        
        return preview_rows
    except Exception as e:
        current_app.logger.error(f"Preview generation failed: {e}")
        return []
```

---

## 四、前端实施计划（简化版）

由于篇幅限制，前端实施计划仅提供关键步骤：

### 步骤F1：初始化React项目

```bash
cd github_manager
npm create vite@latest frontend -- --template react
cd frontend
npm install axios @tanstack/react-query
```

### 步骤F2：配置API客户端

**文件：`frontend/src/api/client.js`**

```javascript
import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:5000/api';

const client = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
client.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle auth errors
client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default client;
```

### 步骤F3：实现关键页面

页面开发顺序：
1. LoginPage（登录）
2. DashboardPage（任务列表）
3. TaskDetailPage（任务详情 + 对话 + 预览）

具体实现略（可参考现代React最佳实践）。

---

## 五、容器化部署

### 步骤D1：创建Dockerfile

**文件：`Dockerfile`**

```dockerfile
# Multi-stage build
# Stage 1: Build frontend
FROM node:18 AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Python backend
FROM python:3.12-slim
WORKDIR /app

# Install dependencies
COPY requirements-web.txt ./
RUN pip install --no-cache-dir -r requirements-web.txt

# Copy application code
COPY . ./

# Copy frontend build
COPY --from=frontend-builder /app/frontend/dist ./static

# Create runtime directory
RUN mkdir -p runtime/tasks runtime/uploads runtime/results

# Expose port
EXPOSE 5000

# Run application
CMD ["python", "-m", "web.app"]
```

### 步骤D2：创建docker-compose.yml

**文件：`docker-compose.yml`**

```yaml
version: '3.8'

services:
  github-manager-web:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - SECRET_KEY=${SECRET_KEY:-default-secret-change-me}
      - ADMIN_USERNAME=${ADMIN_USERNAME:-admin}
      - ADMIN_PASSWORD=${ADMIN_PASSWORD:-admin123}
      - API_KEY=${API_KEY}
      - MODEL_NAME=${MODEL_NAME:-gpt-4o}
      - API_TYPE=${API_TYPE:-openai}
    volumes:
      - ./runtime:/app/runtime
    restart: unless-stopped
```

---

## 六、测试策略

### 单元测试

创建 `tests/web/` 目录，为每个服务编写测试：

```python
# tests/web/test_code_executor.py
def test_safe_code_validation():
    executor = SafeCodeExecutor()
    
    # Valid code
    valid_code = "import pandas as pd\n\ndef transform_data(df):\n    return df"
    is_valid, msg = executor.validate_code(valid_code)
    assert is_valid
    
    # Invalid code (os import)
    invalid_code = "import os\n\ndef transform_data(df):\n    return df"
    is_valid, msg = executor.validate_code(invalid_code)
    assert not is_valid
```

### 集成测试

测试完整流程：
```python
# tests/web/test_integration.py
def test_full_workflow(client, auth_token):
    # 1. Upload file
    response = client.post('/api/normalize/tasks', 
                          headers={'Authorization': f'Bearer {auth_token}'},
                          files={'file': test_csv_file})
    assert response.status_code == 201
    task_id = response.json['task_id']
    
    # 2. Chat multiple rounds
    for instruction in ["转为小写", "去除空格", "添加前缀"]:
        response = client.post(f'/api/normalize/tasks/{task_id}/chat',
                              json={'message': instruction},
                              headers={'Authorization': f'Bearer {auth_token}'})
        assert response.status_code == 200
    
    # 3. Apply transformation
    response = client.post(f'/api/normalize/tasks/{task_id}/apply',
                          headers={'Authorization': f'Bearer {auth_token}'})
    assert response.status_code == 200
    
    # 4. Download result
    response = client.get(f'/api/normalize/tasks/{task_id}/download',
                         headers={'Authorization': f'Bearer {auth_token}'})
    assert response.status_code == 200
```

---

## 七、部署清单

### 开发环境启动

```bash
# 1. 后端
pip install -r requirements-web.txt
export API_KEY=your-api-key
python -m web.app

# 2. 前端（另一个终端）
cd frontend
npm run dev
```

### 生产环境部署

```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，设置密钥和凭证

# 2. 构建并启动
docker-compose up -d

# 3. 检查健康状态
curl http://localhost:5000/api/health

# 4. 访问应用
open http://localhost:5000
```

---

## 八、总结

本实施指南提供了从零到一部署B/S架构标准化系统的详细步骤：

1. **后端**：Flask + 安全代码执行器 + 任务持久化
2. **前端**：React + 现代UI交互
3. **安全**：多层防护（白名单验证 + 受限执行 + JWT认证）
4. **部署**：Docker一键启动

关键实现要点：
- ✅ 代码安全执行机制完善
- ✅ 任务和会话持久化
- ✅ 多轮对话上下文管理
- ✅ 同步执行模式（适合≤1MB文件）
- ✅ 容器化部署方案

后续优化方向（Phase 2+）：
- 异步执行队列
- Docker容器隔离
- WebSocket实时更新
- 多组织支持

---

**下一步行动**：开始实施Phase 1（后端基础框架），完成认证和健康检查功能。

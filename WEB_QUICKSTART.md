# Web应用快速开始指南

## 启动服务

### 方法1：直接运行（推荐）

```bash
# 1. 安装依赖
pip install -r requirements-web.txt

# 2. 启动服务
python -m web.app
```

服务启动后访问：http://localhost:5000

### 方法2：使用venv（Windows）

```cmd
# 1. 激活虚拟环境
venv\Scripts\activate

# 2. 安装依赖
pip install -r requirements-web.txt

# 3. 启动服务
python -m web.app
```

### 方法3：配置环境变量后运行

```bash
# 设置环境变量
export SECRET_KEY="your-secret-key"
export ADMIN_USERNAME="admin"
export ADMIN_PASSWORD="your-password"
export API_KEY="your-openai-api-key"

# 启动服务
python -m web.app
```

## API测试示例

### 1. 健康检查

```bash
curl http://localhost:5000/api/health
```

**响应：**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-11-03T04:52:29.027974Z"
}
```

### 2. 用户登录

```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

**响应：**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 10800,
  "username": "admin"
}
```

**注意：** 将返回的 token 用于后续请求的 Authorization header

### 3. 上传CSV文件创建任务

```bash
curl -X POST http://localhost:5000/api/normalize/tasks \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@test.csv"
```

**响应：**
```json
{
  "task_id": "488d37b8-d057-4560-95e7-4b1f310d5649",
  "analysis": {
    "row_count": 3,
    "column_count": 4,
    "columns": ["Name", "Email", "Department", "Status"]
  },
  "initial_suggestion": "初始规则建议：\n列'Email'可能需要重命名为'Mail'...",
  "preview": [...]
}
```

### 4. 查看任务详情

```bash
curl -X GET http://localhost:5000/api/normalize/tasks/TASK_ID \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 5. 多轮对话修改规则

```bash
curl -X POST http://localhost:5000/api/normalize/tasks/TASK_ID/chat \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message":"将Email列转为小写并去除空格"}'
```

**响应：**
```json
{
  "updated_rule": {
    "description": "已应用规则: 将Email列转为小写并去除空格",
    "code": "def transform_data(df):...",
    "version": 2
  },
  "preview": [...],
  "conversation": [...]
}
```

### 6. 确认执行标准化

```bash
curl -X POST http://localhost:5000/api/normalize/tasks/TASK_ID/apply \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**响应：**
```json
{
  "status": "applied",
  "stats": {
    "total_rows": 3,
    "success_rows": 3,
    "error_rows": 0
  }
}
```

### 7. 下载标准化结果

```bash
curl -X GET http://localhost:5000/api/normalize/tasks/TASK_ID/download \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -o result.csv
```

### 8. 下载错误行文件（如果有）

```bash
curl -X GET http://localhost:5000/api/normalize/tasks/TASK_ID/errors \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -o errors.csv
```

## 完整工作流示例

```bash
# 1. 登录获取token
TOKEN=$(curl -s -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' \
  | grep -o '"token":"[^"]*' | sed 's/"token":"//')

echo "Token: $TOKEN"

# 2. 上传CSV文件
TASK_ID=$(curl -s -X POST http://localhost:5000/api/normalize/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test.csv" \
  | grep -o '"task_id":"[^"]*' | sed 's/"task_id":"//')

echo "Task ID: $TASK_ID"

# 3. 对话修改规则
curl -X POST http://localhost:5000/api/normalize/tasks/$TASK_ID/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message":"将Email列转为小写"}'

# 4. 确认执行
curl -X POST http://localhost:5000/api/normalize/tasks/$TASK_ID/apply \
  -H "Authorization: Bearer $TOKEN"

# 5. 下载结果
curl -X GET http://localhost:5000/api/normalize/tasks/$TASK_ID/download \
  -H "Authorization: Bearer $TOKEN" \
  -o normalized_result.csv

echo "✅ 完成！结果已保存到 normalized_result.csv"
```

## Python代码测试示例

```python
from web.app import create_app
from io import BytesIO

app = create_app()

with app.test_client() as client:
    # 1. 登录
    login_resp = client.post('/api/auth/login', 
                            json={'username': 'admin', 'password': 'admin123'})
    token = login_resp.get_json()['token']
    print(f'✓ 登录成功，Token: {token[:50]}...')
    
    # 2. 上传CSV
    with open('test.csv', 'rb') as f:
        data = {'file': (BytesIO(f.read()), 'test.csv')}
        response = client.post('/api/normalize/tasks',
                              data=data,
                              headers={'Authorization': f'Bearer {token}'},
                              content_type='multipart/form-data')
    
    task_id = response.get_json()['task_id']
    print(f'✓ 任务创建：{task_id}')
    
    # 3. 对话修改规则
    chat_resp = client.post(f'/api/normalize/tasks/{task_id}/chat',
                           json={'message': '将Email列转为小写'},
                           headers={'Authorization': f'Bearer {token}'})
    print(f'✓ 规则已更新')
    
    # 4. 确认执行
    apply_resp = client.post(f'/api/normalize/tasks/{task_id}/apply',
                            headers={'Authorization': f'Bearer {token}'})
    stats = apply_resp.get_json().get('stats')
    print(f'✓ 标准化完成：{stats}')
    
    # 5. 下载结果
    download_resp = client.get(f'/api/normalize/tasks/{task_id}/download',
                               headers={'Authorization': f'Bearer {token}'})
    print(f'✓ 结果下载成功（{len(download_resp.data)} bytes）')
```

## 配置说明

### 环境变量（可选）

在 `.env` 文件中或通过环境变量设置：

```bash
# Flask配置
FLASK_ENV=development  # 或 production
SECRET_KEY=your-secret-key-here
PORT=5000

# 管理员凭证
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123

# LLM配置
API_TYPE=openai  # 或 github, azure, custom
API_KEY=your-api-key
MODEL_NAME=gpt-4o
API_BASE_URL=  # 可选，用于自定义端点

# 文件上传限制
MAX_FILE_SIZE_MB=1

# 会话配置
SESSION_EXPIRY_HOURS=3

# 运行时目录
RUNTIME_DIR=./runtime
```

### 默认配置

如果不设置环境变量，将使用以下默认值：
- **用户名**: admin
- **密码**: admin123
- **端口**: 5000
- **文件大小限制**: 1MB
- **会话有效期**: 3小时

## 目录结构

```
github_manager/
├── web/                    # Web应用模块
│   ├── app.py             # Flask应用入口
│   ├── config.py          # 配置管理
│   ├── blueprints/        # API路由
│   ├── services/          # 业务逻辑
│   ├── middleware/        # 中间件
│   └── utils/             # 工具函数
├── runtime/               # 运行时数据（.gitignore）
│   ├── tasks/            # 任务元数据
│   ├── uploads/          # 上传文件
│   └── results/          # 标准化结果
└── requirements-web.txt   # Web依赖
```

## 常见问题

### Q: ModuleNotFoundError: No module named 'web'

**A:** 确保在项目根目录（github_manager/）运行命令，不要在 web/ 子目录中运行。

```bash
# 正确 ✓
cd /path/to/github_manager
python -m web.app

# 错误 ✗
cd /path/to/github_manager/web
python app.py
```

### Q: 如何修改管理员密码？

**A:** 方法1 - 通过环境变量：
```bash
export ADMIN_PASSWORD="your-new-password"
python -m web.app
```

方法2 - 通过API（未来实现）：
```bash
POST /api/auth/password
```

### Q: 服务重启后任务会丢失吗？

**A:** 不会。任务保存在 `runtime/tasks/` 目录的JSON文件中，服务重启后仍可访问。

### Q: 支持多用户吗？

**A:** 当前Phase 1只支持单个管理员用户。多用户支持将在未来版本实现。

### Q: 如何集成到现有系统？

**A:** 所有功能通过REST API提供，可以从任何HTTP客户端调用：
- JavaScript/TypeScript (axios, fetch)
- Python (requests)
- Java (OkHttp, RestTemplate)
- .NET (HttpClient)
- curl命令行

## 下一步

1. **实现React前端**：参考 `docs/plans/plan-bs-implementation-guide.md`
2. **Docker部署**：添加Dockerfile和docker-compose.yml
3. **功能增强**：
   - 集成真实LLM代码生成
   - 添加更多转换规则
   - 实现任务列表查询
   - 添加会话历史管理

## 帮助与支持

- 查看详细文档：`docs/BS_DEPLOYMENT_SUMMARY.md`
- 查看实施计划：`docs/plans/plan-bs-implementation-guide.md`
- 查看需求分析：`docs/requirements/req-bs-deployment-analysis.md`

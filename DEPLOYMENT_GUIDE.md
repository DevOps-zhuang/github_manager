# 完整部署和使用指南

本指南提供B/S架构标准化系统的完整部署和使用说明，包括后端API和前端React应用。

## 目录

- [快速开始](#快速开始)
- [后端API部署](#后端api部署)
- [前端React应用部署](#前端react应用部署)
- [完整使用流程](#完整使用流程)
- [API测试](#api测试)
- [常见问题](#常见问题)

---

## 快速开始

### 方式1：开发模式（推荐用于本地开发）

**1. 启动后端API**

```bash
# 安装依赖
pip install -r requirements-web.txt

# 启动服务
python -m web.app
```

后端运行在 http://localhost:5000

**2. 启动前端（新终端）**

```bash
cd frontend
npm install
npm start
```

前端运行在 http://localhost:3000

**3. 访问应用**

浏览器打开 http://localhost:3000
- 用户名: `admin`
- 密码: `admin123`

### 方式2：生产模式（仅后端API）

如果只需要API服务（不需要Web界面）：

```bash
pip install -r requirements-web.txt
python -m web.app
```

访问 http://localhost:5000 查看API文档

---

## 后端API部署

### 安装依赖

```bash
pip install -r requirements-web.txt
```

包含的依赖：
- flask >= 3.0.0
- flask-cors >= 4.0.0
- pyjwt >= 2.8.0
- pandas >= 2.0.0
- openai >= 1.0.0
- python-dotenv

### 配置环境变量

创建 `.env` 文件：

```bash
# Flask配置
FLASK_ENV=development  # 或 production
SECRET_KEY=your-secret-key-change-in-production
PORT=5000

# 管理员凭证
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123

# LLM配置
API_TYPE=openai
API_KEY=your-openai-api-key
MODEL_NAME=gpt-4o

# 可选配置
MAX_FILE_SIZE_MB=1
SESSION_EXPIRY_HOURS=3
RUNTIME_DIR=./runtime
```

### 启动服务

```bash
python -m web.app
```

服务默认运行在 http://0.0.0.0:5000

### API端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 欢迎页面（HTML/JSON） |
| GET | `/api/health` | 健康检查 |
| POST | `/api/auth/login` | 用户登录 |
| POST | `/api/normalize/tasks` | 上传CSV创建任务 |
| GET | `/api/normalize/tasks/{id}` | 获取任务详情 |
| POST | `/api/normalize/tasks/{id}/chat` | 多轮对话修改规则 |
| POST | `/api/normalize/tasks/{id}/apply` | 执行标准化 |
| GET | `/api/normalize/tasks/{id}/download` | 下载结果 |
| GET | `/api/normalize/tasks/{id}/errors` | 下载错误行 |

---

## 前端React应用部署

### 安装Node.js

确保安装了 Node.js >= 14 和 npm >= 6

### 安装依赖

```bash
cd frontend
npm install
```

### 开发模式

```bash
npm start
```

应用运行在 http://localhost:3000，API请求自动代理到 http://localhost:5000

### 生产构建

```bash
npm run build
```

构建后的文件在 `build/` 目录。

### 部署选项

#### 选项1：独立部署（推荐）

将 `build/` 目录部署到Nginx/Apache等静态文件服务器：

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        root /path/to/frontend/build;
        try_files $uri /index.html;
    }
    
    location /api {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

#### 选项2：Flask托管

将构建后的文件复制到Flask的static目录：

```bash
npm run build
mkdir -p ../web/static
cp -r build/* ../web/static/
```

然后更新 `web/app.py`，添加静态文件路由。

---

## 完整使用流程

### 1. 登录系统

访问 http://localhost:3000/login

- **用户名**: admin
- **密码**: admin123（默认）

### 2. 上传CSV文件

1. 点击"选择CSV文件"
2. 选择您的CSV文件（≤1MB）
3. 点击"开始处理"

系统会自动分析文件并生成初始规则建议。

### 3. 查看初始分析

系统会显示：
- 行数和列数
- 列名列表
- 初始规则建议
- 前20行预览

### 4. 多轮对话调整规则

在聊天框中用自然语言描述转换规则：

**示例1：转换邮箱格式**
```
将Email列转为小写并去除空格
```

**示例2：重命名列**
```
将Email列重命名为Mail
```

**示例3：添加默认值**
```
添加Organization列，默认值为MyCompany
```

**示例4：数据清洗**
```
去除Name列中的特殊字符
```

每次发送后，系统会：
- 更新转换规则
- 生成新的Python代码
- 显示新的预览结果

### 5. 查看预览

每次调整后，预览表格会实时更新，显示前20行的转换效果。

### 6. 确认执行

满意后点击"✅ 确认执行标准化"，系统会：
- 对完整数据集执行转换
- 生成标准化结果文件
- 记录错误行（如有）

### 7. 下载结果

点击"📥 下载标准化结果"获取：
- 标准化后的CSV文件
- 错误行文件（如果有错误）

### 8. 处理新文件

点击"🆕 处理新文件"开始新的标准化任务。

---

## API测试

### 使用curl测试

**1. 健康检查**

```bash
curl http://localhost:5000/api/health
```

**2. 登录**

**Linux/Mac**:
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

**Windows PowerShell（推荐）**:
```powershell
$body = '{"username":"admin","password":"admin123"}'
Invoke-RestMethod -Method Post -Uri "http://localhost:5000/api/auth/login" `
  -ContentType "application/json" -Body $body
```

**Windows CMD**:
```cmd
curl -X POST http://localhost:5000/api/auth/login -H "Content-Type: application/json" -d "{\"username\":\"admin\",\"password\":\"admin123\"}"
```

**注意**：Windows用户强烈推荐使用PowerShell的`Invoke-RestMethod`，避免引号转义问题。详见 [WINDOWS_CURL_GUIDE.md](WINDOWS_CURL_GUIDE.md)

响应示例：
```json
{
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "expires_in": 10800,
  "username": "admin"
}
```

**3. 上传文件**

```bash
TOKEN="your-token-here"

curl -X POST http://localhost:5000/api/normalize/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test.csv"
```

**4. 对话修改规则**

```bash
TASK_ID="task-id-from-upload"

curl -X POST http://localhost:5000/api/normalize/tasks/$TASK_ID/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message":"将Email列转为小写"}'
```

**5. 执行标准化**

```bash
curl -X POST http://localhost:5000/api/normalize/tasks/$TASK_ID/apply \
  -H "Authorization: Bearer $TOKEN"
```

**6. 下载结果**

```bash
curl -X GET http://localhost:5000/api/normalize/tasks/$TASK_ID/download \
  -H "Authorization: Bearer $TOKEN" \
  -o result.csv
```

---

## 常见问题

### Q1: 后端启动报错 "ModuleNotFoundError: No module named 'flask'"

**A**: 需要安装依赖：

```bash
pip install -r requirements-web.txt
```

### Q2: 前端启动报错 "Cannot find module 'react'"

**A**: 需要安装npm依赖：

```bash
cd frontend
npm install
```

### Q3: curl登录返回 "EMPTY_BODY" 或 "BAD_REQUEST"

**A**: Windows用户遇到引号转义问题。

**最佳解决方案 - 使用PowerShell的Invoke-RestMethod**:
```powershell
$body = '{"username":"admin","password":"admin123"}'
Invoke-RestMethod -Method Post -Uri "http://localhost:5000/api/auth/login" `
  -ContentType "application/json" -Body $body
```

**完整的Windows curl指南**: 参见 [WINDOWS_CURL_GUIDE.md](WINDOWS_CURL_GUIDE.md)

**其他平台**:
- **Linux/Mac**: 使用单引号
  ```bash
  curl -X POST http://localhost:5000/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username":"admin","password":"admin123"}'
  ```

- **Windows CMD**: 必须转义双引号
  ```cmd
  curl -X POST http://localhost:5000/api/auth/login -H "Content-Type: application/json" -d "{\"username\":\"admin\",\"password\":\"admin123\"}"
  ```

### Q3a: 前端npm start报错 "Invalid options object"

**错误信息**:
```
Invalid options object. Dev Server has been initialized using an options object that does not match the API schema.
 - options.allowedHosts[0] should be a non-empty string.
```

**A**: 这是react-scripts 5.x的已知问题。已包含修复：

1. 确认 `frontend/.env` 文件存在（应已自动创建）
2. 如果不存在，手动创建：
   ```bash
   cd frontend
   echo "SKIP_PREFLIGHT_CHECK=true" > .env
   echo "DANGEROUSLY_DISABLE_HOST_CHECK=true" >> .env
   ```
3. 重新运行 `npm start`

**Windows用户**:
```cmd
cd frontend
echo SKIP_PREFLIGHT_CHECK=true > .env
echo DANGEROUSLY_DISABLE_HOST_CHECK=true >> .env
npm start
```

### Q4: 前端无法连接后端API

**A**: 确保：
1. 后端服务正在运行（http://localhost:5000）
2. 检查 `frontend/package.json` 中的 `proxy` 设置
3. 重启前端开发服务器

### Q5: 如何修改管理员密码？

**A**: 设置环境变量：

```bash
export ADMIN_PASSWORD="your-new-password"
python -m web.app
```

或在 `.env` 文件中设置。

### Q6: CORS错误

**A**: 后端已配置CORS允许 localhost:3000。如果使用其他端口，需要更新 `web/app.py`:

```python
CORS(app, origins=["http://localhost:3001"])  # 改为您的端口
```

### Q7: 文件大小限制

**A**: 默认限制1MB。修改环境变量：

```bash
export MAX_FILE_SIZE_MB=5
```

### Q8: 端口冲突

**A**: 修改端口：

**后端**:
```bash
export PORT=5001
python -m web.app
```

**前端**:
```bash
PORT=3001 npm start
```

### Q9: 如何查看日志？

**A**: Flask会在控制台输出日志。生产环境建议使用日志文件：

```bash
python -m web.app > app.log 2>&1
```

### Q10: 任务数据存储在哪里？

**A**: 存储在 `runtime/` 目录：
- `runtime/tasks/` - 任务元数据（JSON）
- `runtime/uploads/` - 上传的CSV
- `runtime/results/` - 标准化结果

服务重启后数据不会丢失。

---

## 安全建议

### 生产环境部署

1. **修改默认密码**
   ```bash
   export ADMIN_PASSWORD="strong-password-here"
   ```

2. **设置强SECRET_KEY**
   ```bash
   export SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')
   ```

3. **使用HTTPS**
   - 配置Nginx/Apache使用SSL证书
   - 禁用HTTP访问

4. **限制文件大小**
   - 防止大文件攻击
   - 默认1MB已经足够

5. **定期备份**
   - 备份 `runtime/` 目录
   - 备份环境配置

6. **监控日志**
   - 检查异常访问
   - 监控API调用频率

---

## 技术支持

- **文档**: 参见 `docs/` 目录
- **快速指南**: `WEB_QUICKSTART.md`
- **部署方案**: `docs/BS_DEPLOYMENT_SUMMARY.md`
- **实施计划**: `docs/plans/plan-bs-implementation-guide.md`

---

**版本**: 1.0.0  
**最后更新**: 2025-11-03

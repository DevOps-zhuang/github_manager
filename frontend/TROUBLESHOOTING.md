# Frontend Troubleshooting Guide

## Issue 1: npm start 报错 "Invalid options object"

### 错误信息
```
Invalid options object. Dev Server has been initialized using an options object 
that does not match the API schema.
 - options.allowedHosts[0] should be a non-empty string.
```

### 解决方案

#### 方案 1: 清除缓存并重新安装（推荐）

```bash
cd frontend

# 删除 node_modules 和 package-lock.json
rm -rf node_modules
rm -f package-lock.json

# 清除 npm 缓存
npm cache clean --force

# 重新安装依赖
npm install

# 启动
npm start
```

**Windows PowerShell**:
```powershell
cd frontend

# 删除 node_modules 和 package-lock.json
Remove-Item -Recurse -Force node_modules
Remove-Item -Force package-lock.json

# 清除 npm 缓存
npm cache clean --force

# 重新安装依赖
npm install

# 启动
npm start
```

#### 方案 2: 检查 .env 文件

确保 `frontend/.env` 文件存在且包含：
```bash
SKIP_PREFLIGHT_CHECK=true
REACT_APP_API_URL=http://localhost:5000
BROWSER=none
PORT=3000
```

如果文件不存在，从 `.env.example` 复制：
```bash
cp .env.example .env
```

#### 方案 3: 降级或升级 react-scripts

如果问题持续，尝试：

```bash
# 方案 3a: 降级到 4.0.3
npm install react-scripts@4.0.3

# 方案 3b: 升级到最新版本
npm install react-scripts@latest
```

#### 方案 4: 使用 DANGEROUSLY_DISABLE_HOST_CHECK (不推荐用于生产)

在 `.env` 文件中添加：
```bash
DANGEROUSLY_DISABLE_HOST_CHECK=true
```

**警告**: 此选项仅用于开发环境，不要在生产环境使用。

### 根本原因

这个错误通常由以下原因引起：

1. **webpack-dev-server 版本兼容性问题**: react-scripts 5.x 的 webpack-dev-server 对配置更严格
2. **缓存的 node_modules**: 旧版本依赖缓存可能导致问题
3. **缺少 SKIP_PREFLIGHT_CHECK**: 该环境变量跳过某些检查

### 验证修复

启动成功后应该看到：
```
Compiled successfully!

You can now view github-manager-frontend in the browser.

  Local:            http://localhost:3000
  On Your Network:  http://192.168.x.x:3000
```

---

## Issue 2: 连接后端 API 失败

### 错误信息
```
Network Error
Failed to fetch
```

### 解决方案

1. **确认后端正在运行**:
   ```bash
   # 在另一个终端
   python -m web.app
   
   # 应该看到:
   # * Running on http://127.0.0.1:5000
   ```

2. **检查 CORS 配置**: 确保后端允许 localhost:3000 的请求

3. **测试后端健康检查**:
   ```bash
   curl http://localhost:5000/api/health
   ```

4. **检查防火墙**: 确保端口 5000 和 3000 没有被阻止

---

## Issue 3: 登录失败 "认证失败"

### 可能原因

1. **错误的凭证**: 确保使用正确的用户名和密码
   - 默认用户名: `admin`
   - 默认密码: `admin123`

2. **环境变量覆盖**: 检查是否有环境变量修改了默认凭证
   ```bash
   echo $ADMIN_USERNAME
   echo $ADMIN_PASSWORD
   ```

3. **后端配置问题**: 检查 `web/config.py` 中的配置

### 解决方案

1. **重置为默认凭证**:
   ```bash
   # 清除环境变量
   unset ADMIN_USERNAME
   unset ADMIN_PASSWORD
   
   # 重启后端
   python -m web.app
   ```

2. **设置自定义凭证**:
   ```bash
   export ADMIN_USERNAME=yourusername
   export ADMIN_PASSWORD=yourpassword
   python -m web.app
   ```

---

## Issue 4: 文件上传失败

### 可能原因

1. **文件太大**: 默认限制为 1MB
2. **文件格式不对**: 只支持 CSV 文件
3. **后端存储目录不存在**: `runtime/uploads/` 目录需要存在

### 解决方案

1. **检查文件大小**:
   ```bash
   ls -lh yourfile.csv
   ```

2. **增加文件大小限制**:
   ```bash
   export MAX_FILE_SIZE_MB=5
   python -m web.app
   ```

3. **创建必要的目录**:
   ```bash
   mkdir -p runtime/uploads
   mkdir -p runtime/tasks
   mkdir -p runtime/results
   ```

---

## Issue 5: 构建失败

### 错误信息
```
Failed to compile
```

### 解决方案

1. **检查 Node.js 版本**:
   ```bash
   node --version  # 应该是 >= 14.0.0
   npm --version   # 应该是 >= 6.0.0
   ```

2. **更新 Node.js**:
   - Windows: 从 https://nodejs.org 下载
   - Mac: `brew upgrade node`
   - Linux: `nvm install node` 或使用包管理器

3. **清理并重新构建**:
   ```bash
   rm -rf node_modules build
   npm install
   npm run build
   ```

---

## 常用命令

### 开发环境

```bash
# 后端（终端1）
cd /path/to/github_manager
pip install -r requirements-web.txt
python -m web.app

# 前端（终端2）
cd /path/to/github_manager/frontend
npm install
npm start
```

### 生产构建

```bash
# 构建前端
cd frontend
npm run build

# 构建将生成在 frontend/build/ 目录
# 可以用 Flask 直接托管这些静态文件
```

### 完全重置

```bash
# 前端
cd frontend
rm -rf node_modules package-lock.json build
npm cache clean --force
npm install

# 后端
rm -rf runtime/
mkdir -p runtime/{tasks,uploads,results}

# 重启服务
python -m web.app
```

---

## 获取帮助

如果以上方案都无法解决问题：

1. **检查日志**:
   - 后端日志：查看终端输出
   - 前端日志：打开浏览器开发者工具 (F12)

2. **查看详细文档**:
   - [DEPLOYMENT_GUIDE.md](../DEPLOYMENT_GUIDE.md)
   - [WINDOWS_CURL_GUIDE.md](../WINDOWS_CURL_GUIDE.md)

3. **提供以下信息**:
   - 操作系统版本
   - Node.js 和 npm 版本
   - Python 版本
   - 完整的错误信息
   - 操作步骤

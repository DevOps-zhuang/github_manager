# Frontend - React应用

AI辅助CSV标准化的Web前端界面。

## 功能

- 🔐 用户登录（JWT认证）
- 📁 CSV文件上传
- 💬 多轮对话式规则调整
- 📊 实时预览（前20行）
- ✅ 执行标准化
- 📥 下载结果文件

## 开发环境

### 前提条件

- Node.js >= 14
- npm >= 6

### 安装依赖

```bash
cd frontend
npm install
```

### 启动开发服务器

```bash
npm start
```

应用将在 http://localhost:3000 打开。后端API请求会自动代理到 http://localhost:5000。

### 构建生产版本

```bash
npm run build
```

构建后的文件在 `build/` 目录中。

## 使用说明

### 1. 启动后端服务

```bash
# 在项目根目录
python -m web.app
```

后端服务运行在 http://localhost:5000

### 2. 启动前端开发服务器

```bash
# 在frontend目录
npm start
```

前端服务运行在 http://localhost:3000

### 3. 登录

- 默认用户名: `admin`
- 默认密码: `admin123`

### 4. 使用流程

1. **上传CSV文件** - 选择您要标准化的CSV文件
2. **查看分析结果** - 系统自动分析文件结构并提供初始建议
3. **对话调整规则** - 用自然语言描述您需要的转换规则（例如："将Email列转为小写"）
4. **查看预览** - 每次调整后查看前20行的转换结果
5. **确认执行** - 满意后点击"确认执行标准化"
6. **下载结果** - 下载标准化后的CSV文件

## 项目结构

```
frontend/
├── public/
│   └── index.html           # HTML模板
├── src/
│   ├── api/
│   │   └── client.js        # API客户端（axios配置）
│   ├── utils/
│   │   └── auth.js          # 认证工具函数
│   ├── pages/
│   │   ├── LoginPage.js     # 登录页面
│   │   ├── LoginPage.css
│   │   ├── DashboardPage.js # 主工作界面
│   │   └── DashboardPage.css
│   ├── App.js               # 应用路由
│   ├── index.js             # 应用入口
│   └── index.css            # 全局样式
├── package.json             # 依赖配置
└── README.md                # 本文件
```

## API集成

前端通过axios与后端API通信，所有请求自动包含JWT令牌。

API端点：
- `POST /api/auth/login` - 登录
- `POST /api/normalize/tasks` - 上传文件
- `GET /api/normalize/tasks/{id}` - 获取任务
- `POST /api/normalize/tasks/{id}/chat` - 对话
- `POST /api/normalize/tasks/{id}/apply` - 执行
- `GET /api/normalize/tasks/{id}/download` - 下载

详见 `src/api/client.js`

## 环境变量

可选的环境变量（在`.env`文件中配置）：

```
REACT_APP_API_BASE=/api
```

## 技术栈

- React 18
- React Router 6
- Axios
- CSS3（自定义样式，无UI框架）

## 故障排除

### 端口冲突

如果3000端口被占用，可以设置环境变量：

```bash
PORT=3001 npm start
```

### 代理问题

如果API请求失败，确保：
1. 后端服务正在运行（http://localhost:5000）
2. package.json中的proxy设置正确

### CORS错误

后端已配置CORS允许localhost:3000，如果使用其他端口，需要在`web/app.py`中更新CORS配置。

## 部署

### 方法1：独立部署

构建后将`build/`目录部署到静态文件服务器（如Nginx）。

### 方法2：与后端集成

将构建后的文件复制到后端的`static/`目录：

```bash
npm run build
cp -r build/* ../web/static/
```

然后Flask会自动托管前端文件。

## 许可证

与主项目相同

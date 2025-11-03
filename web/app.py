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
    
    # Root route - API welcome page
    @app.route('/')
    def index():
        """Welcome page with API information."""
        from flask import request
        
        # Check if request is from browser (Accept header contains text/html)
        if 'text/html' in request.headers.get('Accept', ''):
            # Return HTML page for browsers
            return '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI辅助CSV标准化Web服务</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            max-width: 900px;
            margin: 50px auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 {
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }
        h2 {
            color: #34495e;
            margin-top: 30px;
        }
        .status {
            display: inline-block;
            padding: 5px 15px;
            background: #27ae60;
            color: white;
            border-radius: 20px;
            font-size: 14px;
        }
        .endpoint {
            background: #ecf0f1;
            padding: 10px 15px;
            margin: 10px 0;
            border-left: 4px solid #3498db;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
        }
        .method {
            color: #e74c3c;
            font-weight: bold;
        }
        .path {
            color: #16a085;
        }
        .description {
            color: #7f8c8d;
            margin-left: 10px;
        }
        a {
            color: #3498db;
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
        }
        .info-box {
            background: #fff3cd;
            border: 1px solid #ffc107;
            padding: 15px;
            border-radius: 4px;
            margin: 20px 0;
        }
        code {
            background: #2c3e50;
            color: #ecf0f1;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 AI辅助CSV标准化Web服务</h1>
        <p><span class="status">● 运行中</span> <strong>版本:</strong> 1.0.0</p>
        
        <p>提供AI辅助的CSV数据标准化服务，支持多轮对话式规则定制</p>
        
        <div class="info-box">
            📚 <strong>快速开始文档:</strong> 
            <a href="https://github.com/DevOps-zhuang/github_manager/blob/main/WEB_QUICKSTART.md" target="_blank">
                WEB_QUICKSTART.md
            </a>
        </div>
        
        <h2>📡 API端点</h2>
        
        <h3>认证</h3>
        <div class="endpoint">
            <span class="method">POST</span> 
            <span class="path">/api/auth/login</span>
            <span class="description">- 用户登录</span>
        </div>
        
        <h3>健康检查</h3>
        <div class="endpoint">
            <span class="method">GET</span> 
            <span class="path">/api/health</span>
            <span class="description">- 服务健康检查</span>
        </div>
        
        <h3>标准化任务</h3>
        <div class="endpoint">
            <span class="method">POST</span> 
            <span class="path">/api/normalize/tasks</span>
            <span class="description">- 上传CSV创建任务</span>
        </div>
        <div class="endpoint">
            <span class="method">GET</span> 
            <span class="path">/api/normalize/tasks/{id}</span>
            <span class="description">- 获取任务详情</span>
        </div>
        <div class="endpoint">
            <span class="method">POST</span> 
            <span class="path">/api/normalize/tasks/{id}/chat</span>
            <span class="description">- 多轮对话修改规则</span>
        </div>
        <div class="endpoint">
            <span class="method">POST</span> 
            <span class="path">/api/normalize/tasks/{id}/apply</span>
            <span class="description">- 执行标准化</span>
        </div>
        <div class="endpoint">
            <span class="method">GET</span> 
            <span class="path">/api/normalize/tasks/{id}/download</span>
            <span class="description">- 下载标准化结果</span>
        </div>
        <div class="endpoint">
            <span class="method">GET</span> 
            <span class="path">/api/normalize/tasks/{id}/errors</span>
            <span class="description">- 下载错误行</span>
        </div>
        
        <h2>🔧 快速测试</h2>
        <p>测试登录接口:</p>
        <pre style="background: #2c3e50; color: #ecf0f1; padding: 15px; border-radius: 4px; overflow-x: auto;">curl -X POST http://127.0.0.1:5000/api/auth/login \\
  -H "Content-Type: application/json" \\
  -d '{"username":"admin","password":"admin123"}'</pre>
        
        <h2>📖 更多信息</h2>
        <ul>
            <li>完整API文档: <a href="https://github.com/DevOps-zhuang/github_manager/blob/main/WEB_QUICKSTART.md">WEB_QUICKSTART.md</a></li>
            <li>部署方案: <a href="https://github.com/DevOps-zhuang/github_manager/blob/main/docs/BS_DEPLOYMENT_SUMMARY.md">BS_DEPLOYMENT_SUMMARY.md</a></li>
            <li>JSON格式: <a href="/?format=json">/?format=json</a></li>
        </ul>
    </div>
</body>
</html>
'''
        
        # Return JSON for API clients
        return jsonify({
            'name': 'AI辅助CSV标准化Web服务',
            'version': '1.0.0',
            'description': '提供AI辅助的CSV数据标准化服务，支持多轮对话式规则定制',
            'endpoints': {
                'health': 'GET /api/health - 健康检查',
                'login': 'POST /api/auth/login - 用户登录',
                'tasks': {
                    'create': 'POST /api/normalize/tasks - 上传CSV创建任务',
                    'get': 'GET /api/normalize/tasks/{id} - 获取任务详情',
                    'chat': 'POST /api/normalize/tasks/{id}/chat - 多轮对话修改规则',
                    'apply': 'POST /api/normalize/tasks/{id}/apply - 执行标准化',
                    'download': 'GET /api/normalize/tasks/{id}/download - 下载结果',
                    'errors': 'GET /api/normalize/tasks/{id}/errors - 下载错误行'
                }
            },
            'documentation': 'https://github.com/DevOps-zhuang/github_manager/blob/main/WEB_QUICKSTART.md',
            'status': 'running'
        })
    
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

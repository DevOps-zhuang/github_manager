"""Authentication blueprint."""

from flask import Blueprint, request, jsonify, current_app
from web.utils.session_manager import SessionManager

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['POST'])
def login():
    """Admin login."""
    # Try multiple methods to parse the request data
    data = None
    
    # Method 1: Try get_json (works for properly formatted JSON)
    data = request.get_json(silent=True)
    
    # Method 2: If that fails, try parsing request.data manually
    if not data and request.data:
        try:
            import json as json_lib
            data = json_lib.loads(request.data.decode('utf-8'))
        except:
            pass
    
    # Method 3: Try form data
    if not data:
        data = request.form.to_dict() if request.form else None
    
    # Method 4: Try to parse as URL parameters
    if not data:
        data = request.args.to_dict() if request.args else None
    
    if not data:
        return jsonify({
            'error': '请求体不能为空或格式不正确',
            'code': 'EMPTY_BODY',
            'hint': '请使用JSON格式: {"username":"admin","password":"admin123"}'
        }), 400
    
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': '用户名和密码不能为空', 'code': 'MISSING_CREDENTIALS'}), 400
    
    # Validate credentials
    if (username == current_app.config['ADMIN_USERNAME'] and 
        password == current_app.config['ADMIN_PASSWORD']):
        
        # Create session token
        session_mgr = SessionManager(
            current_app.config['SECRET_KEY'],
            current_app.config['SESSION_EXPIRY_HOURS']
        )
        token = session_mgr.create_token(username)
        
        return jsonify({
            'token': token,
            'expires_in': current_app.config['SESSION_EXPIRY_HOURS'] * 3600,
            'username': username
        }), 200
    else:
        return jsonify({'error': '认证失败', 'code': 'AUTH_FAILED'}), 401


@auth_bp.route('/password', methods=['POST'])
def change_password():
    """Change admin password (requires authentication)."""
    # TODO: Implement password change with token verification
    return jsonify({'error': 'Not implemented yet', 'code': 'NOT_IMPLEMENTED'}), 501

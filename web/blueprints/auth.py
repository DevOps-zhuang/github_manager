"""Authentication blueprint."""

from flask import Blueprint, request, jsonify, current_app
from web.utils.session_manager import SessionManager

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['POST'])
def login():
    """Admin login."""
    data = request.get_json()
    if not data:
        return jsonify({'error': '请求体不能为空', 'code': 'EMPTY_BODY'}), 400
    
    username = data.get('username')
    password = data.get('password')
    
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

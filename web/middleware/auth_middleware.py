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
        session_mgr = SessionManager(
            current_app.config['SECRET_KEY'],
            current_app.config['SESSION_EXPIRY_HOURS']
        )
        payload = session_mgr.verify_token(token)
        
        if not payload:
            return jsonify({'error': '令牌无效或已过期', 'code': 'INVALID_TOKEN'}), 401
        
        # Attach user info to request
        request.user = payload
        
        return f(*args, **kwargs)
    
    return decorated_function

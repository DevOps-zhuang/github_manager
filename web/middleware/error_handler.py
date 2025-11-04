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

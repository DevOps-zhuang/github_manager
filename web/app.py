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

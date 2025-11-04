"""Application configuration."""

import os
from pathlib import Path


class Config:
    """Base configuration."""
    
    # Flask
    ENV = os.environ.get('FLASK_ENV', 'development')
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Admin credentials
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')
    
    # Session
    SESSION_EXPIRY_HOURS = int(os.environ.get('SESSION_EXPIRY_HOURS', '3'))
    
    # File upload
    MAX_FILE_SIZE_MB = int(os.environ.get('MAX_FILE_SIZE_MB', '1'))
    MAX_CONTENT_LENGTH = MAX_FILE_SIZE_MB * 1024 * 1024
    ALLOWED_EXTENSIONS = {'csv'}
    
    # Runtime storage
    RUNTIME_DIR = Path(os.environ.get('RUNTIME_DIR', './runtime'))
    
    # LLM (inherit from existing env vars)
    API_TYPE = os.environ.get('API_TYPE', 'openai')
    API_KEY = os.environ.get('API_KEY') or os.environ.get('GITHUB_TOKEN')
    MODEL_NAME = os.environ.get('MODEL_NAME', 'gpt-4o')
    API_BASE_URL = os.environ.get('API_BASE_URL')

"""Session management with JWT."""

import jwt
from datetime import datetime, timedelta
from typing import Optional


class SessionManager:
    """JWT-based session manager."""
    
    def __init__(self, secret_key: str, expiry_hours: int = 3):
        self.secret_key = secret_key
        self.expiry_hours = expiry_hours
    
    def create_token(self, username: str) -> str:
        """Create JWT token."""
        payload = {
            'username': username,
            'exp': datetime.utcnow() + timedelta(hours=self.expiry_hours),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def verify_token(self, token: str) -> Optional[dict]:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(
                token, self.secret_key, algorithms=['HS256']
            )
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

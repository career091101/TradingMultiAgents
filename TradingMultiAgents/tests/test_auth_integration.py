"""
Integration tests for authentication system
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from webui.utils.auth import AuthManager


class TestAuthManager:
    """Test authentication manager"""
    
    def test_authenticate_valid_user(self):
        """Test authentication with valid credentials"""
        auth = AuthManager()
        
        # Test valid user
        assert auth.authenticate("user", "user123") is True
        assert auth.authenticate("admin", "admin123") is True
    
    def test_authenticate_invalid_user(self):
        """Test authentication with invalid credentials"""
        auth = AuthManager()
        
        # Test invalid username
        assert auth.authenticate("invalid", "password") is False
        
        # Test invalid password
        assert auth.authenticate("user", "wrongpass") is False
        
        # Test empty credentials
        assert auth.authenticate("", "") is False
    
    def test_create_session(self):
        """Test session creation"""
        auth = AuthManager()
        
        # Create session
        session_id = auth.create_session("user")
        
        # Session ID should be a string
        assert isinstance(session_id, str)
        assert len(session_id) > 0
    
    def test_get_user_role(self):
        """Test getting user role"""
        auth = AuthManager()
        
        # Test roles
        assert auth.get_user_role("admin") == "admin"
        assert auth.get_user_role("user") == "user"
        assert auth.get_user_role("invalid") is None
    
    def test_is_admin(self):
        """Test admin check"""
        auth = AuthManager()
        
        # Admin session info
        admin_info = {"role": "admin", "username": "admin"}
        assert auth.is_admin(admin_info) is True
        
        # User session info
        user_info = {"role": "user", "username": "user"}
        assert auth.is_admin(user_info) is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
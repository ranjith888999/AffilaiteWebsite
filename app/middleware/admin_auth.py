"""
Admin Authentication Middleware
Protects all /admin/* endpoints with password authentication.
"""
from fastapi import Request, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
import os
from typing import Optional
import secrets
import hashlib


class AdminSecurityConfig:
    """Configuration for admin panel security."""
    
    @staticmethod
    def get_admin_username() -> str:
        """Get the admin username."""
        return os.getenv("ADMIN_USERNAME", "admin")
    
    @staticmethod
    def get_admin_password() -> str:
        """Get the admin password."""
        return os.getenv("ADMIN_PASSWORD", "")
    
    @staticmethod
    def is_admin_auth_enabled() -> bool:
        """Check if admin authentication is enabled."""
        # Admin auth is enabled if password is set
        return bool(AdminSecurityConfig.get_admin_password())
    
    @staticmethod
    def get_session_secret() -> str:
        """Get the session secret key."""
        return os.getenv("SECRET_KEY", "default-secret-key")
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password for secure comparison."""
        return hashlib.sha256(password.encode()).hexdigest()


def verify_admin_credentials(username: str, password: str) -> bool:
    """Verify admin username and password."""
    expected_username = AdminSecurityConfig.get_admin_username()
    expected_password = AdminSecurityConfig.get_admin_password()
    
    # If no password is set, authentication is disabled (dev mode)
    if not expected_password:
        return True
    
    # Verify both username and password
    return username == expected_username and password == expected_password


def generate_admin_token(username: str) -> str:
    """Generate a secure session token for admin."""
    secret = AdminSecurityConfig.get_session_secret()
    data = f"{username}:{secret}"
    return hashlib.sha256(data.encode()).hexdigest()


def verify_admin_token(token: str, username: str) -> bool:
    """Verify an admin session token."""
    expected_token = generate_admin_token(username)
    return secrets.compare_digest(token, expected_token)


# Simple HTML login page
LOGIN_PAGE_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Login - Affiliate Website</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .login-container {
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
            width: 100%;
            max-width: 400px;
        }
        
        .login-header {
            text-align: center;
            margin-bottom: 30px;
        }
        
        .login-header h1 {
            color: #333;
            font-size: 28px;
            margin-bottom: 10px;
        }
        
        .login-header p {
            color: #666;
            font-size: 14px;
        }
        
        .lock-icon {
            font-size: 60px;
            margin-bottom: 20px;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        .form-group label {
            display: block;
            color: #333;
            font-weight: 500;
            margin-bottom: 8px;
            font-size: 14px;
        }
        
        .form-group input {
            width: 100%;
            padding: 12px 15px;
            border: 2px solid #e0e0e0;
            border-radius: 5px;
            font-size: 14px;
            transition: all 0.3s ease;
        }
        
        .form-group input:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .login-btn {
            width: 100%;
            padding: 12px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 5px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s ease;
        }
        
        .login-btn:hover {
            transform: translateY(-2px);
        }
        
        .login-btn:active {
            transform: translateY(0);
        }
        
        .error-message {
            background: #fee;
            color: #c33;
            padding: 12px;
            border-radius: 5px;
            margin-bottom: 20px;
            font-size: 14px;
            display: none;
        }
        
        .error-message.show {
            display: block;
        }
        
        .info-message {
            background: #e3f2fd;
            color: #1976d2;
            padding: 12px;
            border-radius: 5px;
            margin-top: 20px;
            font-size: 13px;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="login-header">
            <div class="lock-icon">🔒</div>
            <h1>Admin Login</h1>
            <p>Enter your credentials to access the admin panel</p>
        </div>
        
        <div id="errorMessage" class="error-message"></div>
        
        <form id="loginForm" method="POST" action="/admin/login">
            <div class="form-group">
                <label for="username">Username</label>
                <input type="text" id="username" name="username" required autofocus>
            </div>
            
            <div class="form-group">
                <label for="password">Password</label>
                <input type="password" id="password" name="password" required>
            </div>
            
            <button type="submit" class="login-btn">Login</button>
        </form>
        
        <div class="info-message">
            💡 Default credentials are set via environment variables
        </div>
    </div>
    
    <script>
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.get('error') === 'invalid') {
            const errorMsg = document.getElementById('errorMessage');
            errorMsg.textContent = '❌ Invalid username or password';
            errorMsg.classList.add('show');
        }
    </script>
</body>
</html>
"""


async def admin_authentication_middleware(request: Request, call_next):
    """
    Middleware to protect /admin/* endpoints with authentication.
    
    Requires admin username and password to access admin pages.
    Uses session cookies to maintain authentication.
    """
    
    # Check if this is an admin endpoint
    is_admin_endpoint = request.url.path.startswith("/admin")
    
    if not is_admin_endpoint:
        # Not an admin request, proceed normally
        return await call_next(request)
    
    # Allow login page and login POST endpoint
    if request.url.path in ["/admin/login", "/admin/logout"]:
        return await call_next(request)
    
    # Check if admin authentication is enabled
    if not AdminSecurityConfig.is_admin_auth_enabled():
        # No password set, allow access (development mode)
        return await call_next(request)
    
    # Check for session cookie
    admin_token = request.cookies.get("admin_session")
    admin_username = request.cookies.get("admin_username")
    
    if admin_token and admin_username:
        # Verify the session token
        if verify_admin_token(admin_token, admin_username):
            # Valid session, allow access
            return await call_next(request)
    
    # No valid session, redirect to login page
    # Save the original URL to redirect back after login
    redirect_url = f"/admin/login?next={request.url.path}"
    return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)

"""
API Documentation Security Middleware
Protects /docs and /redoc endpoints based on environment and authentication.
"""
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
import os
from typing import Optional, List


class APIDocsSecurityConfig:
    """Configuration for API documentation security."""
    
    @staticmethod
    def is_production() -> bool:
        """Check if running in production environment."""
        return (
            os.getenv("ENVIRONMENT", "").lower() == "production" or
            os.getenv("PRODUCTION", "").lower() == "true" or
            os.getenv("EASYPANEL") == "true" or
            os.getenv("RAILWAY_ENVIRONMENT") or
            os.getenv("RENDER") or
            os.getenv("DYNO")  # Heroku
        )
    
    @staticmethod
    def docs_enabled() -> bool:
        """Check if API docs should be enabled."""
        # Allow explicit override
        docs_enabled = os.getenv("ENABLE_API_DOCS", "").lower()
        if docs_enabled == "false":
            return False
        if docs_enabled == "true":
            return True
        
        # By default, disable in production
        return not APIDocsSecurityConfig.is_production()
    
    @staticmethod
    def get_api_docs_key() -> Optional[str]:
        """Get the API docs access key if configured."""
        return os.getenv("API_DOCS_KEY")
    
    @staticmethod
    def get_allowed_ips() -> List[str]:
        """Get list of allowed IP addresses for API docs access."""
        ips = os.getenv("API_DOCS_ALLOWED_IPS", "")
        if ips:
            return [ip.strip() for ip in ips.split(",") if ip.strip()]
        return []
    
    @staticmethod
    def allow_localhost() -> bool:
        """Check if localhost should be allowed."""
        return os.getenv("API_DOCS_ALLOW_LOCALHOST", "true").lower() == "true"


async def api_docs_security_middleware(request: Request, call_next):
    """
    Middleware to protect API documentation endpoints.
    
    Security levels:
    1. Environment-based: Disable completely in production
    2. Key-based: Require API_DOCS_KEY header or query parameter
    3. IP-based: Restrict to specific IP addresses
    """
    
    # Check if this is a docs-related endpoint
    docs_paths = ["/docs", "/redoc", "/openapi.json"]
    is_docs_request = any(request.url.path.startswith(path) for path in docs_paths)
    
    if not is_docs_request:
        # Not a docs request, proceed normally
        return await call_next(request)
    
    # Check if docs are enabled
    if not APIDocsSecurityConfig.docs_enabled():
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "detail": "API documentation is disabled in production. Set ENABLE_API_DOCS=true to enable.",
                "hint": "For security reasons, API documentation is not available in production environments."
            }
        )
    
    # Check IP whitelist if configured
    allowed_ips = APIDocsSecurityConfig.get_allowed_ips()
    if allowed_ips:
        client_ip = request.client.host
        
        # Allow localhost if configured
        localhost_ips = ["127.0.0.1", "::1", "localhost"]
        is_localhost = client_ip in localhost_ips
        
        if not (client_ip in allowed_ips or (is_localhost and APIDocsSecurityConfig.allow_localhost())):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "detail": f"Access denied. Your IP ({client_ip}) is not whitelisted.",
                    "hint": "Add your IP to API_DOCS_ALLOWED_IPS environment variable."
                }
            )
    
    # Check API docs key if configured
    api_docs_key = APIDocsSecurityConfig.get_api_docs_key()
    if api_docs_key:
        # Check header
        provided_key = request.headers.get("X-API-Docs-Key")
        
        # Also check query parameter as fallback
        if not provided_key:
            provided_key = request.query_params.get("api_docs_key")
        
        if provided_key != api_docs_key:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "detail": "Invalid or missing API documentation access key.",
                    "hint": "Provide the key via X-API-Docs-Key header or ?api_docs_key=YOUR_KEY query parameter."
                }
            )
    
    # All checks passed, allow access
    return await call_next(request)

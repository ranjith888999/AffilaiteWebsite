import os
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from authlib.integrations.starlette_client import OAuth
from authlib.common.security import generate_token
from app.models.database import User
from app.database import get_db
from app.config import Config
from datetime import datetime
import json

router = APIRouter()

# OAuth setup - Optimized for performance
oauth = OAuth()
google = oauth.register(
    name='google',
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    access_token_url='https://oauth2.googleapis.com/token',
    jwks_uri='https://www.googleapis.com/oauth2/v3/certs',
    userinfo_endpoint='https://www.googleapis.com/oauth2/v2/userinfo',
    client_kwargs={
        'scope': 'openid email profile',
        'prompt': 'select_account'  # Pre-configure for account selection
    }
)

@router.get("/config")
async def auth_config():
    """Get authentication configuration (for debugging/admin purposes)"""
    config = Config.get_auth_config_summary()
    return {
        "status": "success",
        "config": config,
        "message": "Authentication configuration retrieved successfully"
    }

@router.get("/login")
async def login(request: Request):
    """Initiate Google OAuth login with account selection - Fast redirect"""
    # Use the configuration module to get the redirect URI
    redirect_uri = Config.get_google_redirect_uri()
    
    # Log the configuration for debugging (in development)
    if os.getenv("DEBUG", "False").lower() == "true":
        print(f"🔐 Google OAuth Redirect URI: {redirect_uri}")
    
    # Optimized for fastest possible redirect
    return await google.authorize_redirect(
        request, 
        redirect_uri,
        prompt='select_account',
        access_type='offline',
        include_granted_scopes='true'
    )

@router.get("/callback")
async def auth_callback(request: Request, db: Session = Depends(get_db)):
    """Handle Google OAuth callback"""
    try:
        # Get the authorization token
        token = await google.authorize_access_token(request)
        
        # Get user info from Google userinfo endpoint
        user_resp = await google.get('https://www.googleapis.com/oauth2/v2/userinfo', token=token)
        user_info = user_resp.json()
        
        if not user_info or not user_info.get('id'):
            raise HTTPException(status_code=400, detail="Failed to get user information")
        
        # Check if user exists in our database
        user = db.query(User).filter(User.google_id == user_info['id']).first()
        
        if not user:
            # Create new user
            user = User(
                google_id=user_info['id'],
                email=user_info['email'],
                name=user_info['name'],
                picture=user_info.get('picture', ''),
                last_login=datetime.utcnow()
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            # Update last login
            user.last_login = datetime.utcnow()
            db.commit()
        
        # Create session data
        session_data = {
            'user_id': user.id,
            'google_id': user.google_id,
            'email': user.email,
            'name': user.name,
            'picture': user.picture
        }
        
        # Create response and redirect to home
        response = RedirectResponse(url="/")
        
        # Store user session in cookie (secure for production)
        is_production = os.getenv("ENVIRONMENT") == "production"
        response.set_cookie(
            key="user_session",
            value=json.dumps(session_data),
            max_age=86400 * 7,  # 7 days
            httponly=True,
            secure=is_production,  # True for HTTPS in production
            samesite="lax",
            domain=".couponscover.com" if is_production else None
        )
        
        return response
        
    except Exception as e:
        print(f"Authentication error: {e}")
        raise HTTPException(status_code=400, detail="Authentication failed")

@router.get("/logout")
async def logout():
    """Logout user"""
    response = RedirectResponse(url="/")
    is_production = os.getenv("ENVIRONMENT") == "production"
    response.delete_cookie(
        "user_session",
        domain=".couponscover.com" if is_production else None
    )
    return response

@router.get("/user")
async def get_current_user(request: Request, db: Session = Depends(get_db)):
    """Get current authenticated user"""
    try:
        user_session = request.cookies.get("user_session")
        if not user_session:
            return {"authenticated": False}
        
        session_data = json.loads(user_session)
        user_id = session_data.get('user_id')
        
        if not user_id:
            return {"authenticated": False}
        
        # Verify user still exists and is active
        user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
        if not user:
            return {"authenticated": False}
        
        return {
            "authenticated": True,
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "picture": user.picture
            }
        }
        
    except Exception as e:
        print(f"User verification error: {e}")
        return {"authenticated": False}

def get_current_user_dependency(request: Request, db: Session = Depends(get_db)):
    """Dependency to get current user for protected routes"""
    try:
        user_session = request.cookies.get("user_session")
        if not user_session:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        session_data = json.loads(user_session)
        user_id = session_data.get('user_id')
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid session")
        
        user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        return user
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=401, detail="Invalid session data")
    except Exception as e:
        raise HTTPException(status_code=401, detail="Authentication failed")

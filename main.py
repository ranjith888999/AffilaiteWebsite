from fastapi import FastAPI, Request, Depends, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
from app.database import get_db, create_tables, db_available
from app.controllers import campaigns_controller, offers_controller, chat_controller, links_controller, auth_controller, images_controller, health_controller, seo_controller, admin_images_controller, top_deals_controller
from app.models.database import Offer
from app.config import Config, validate_environment, print_env_status
from app.middleware import (
    api_docs_security_middleware, 
    APIDocsSecurityConfig,
    admin_authentication_middleware,
    AdminSecurityConfig,
    verify_admin_credentials,
    generate_admin_token,
    LOGIN_PAGE_HTML
)
import os
import time
from dotenv import load_dotenv
import logging
from contextlib import asynccontextmanager

load_dotenv()

# Setup logging for production
if os.getenv("DEBUG", "False").lower() != "true":
    try:
        # Create logs directory outside the app directory to avoid file watcher issues
        logs_dir = os.path.join(os.path.dirname(os.getcwd()), 'app-logs')
        os.makedirs(logs_dir, exist_ok=True)
        log_file = os.path.join(logs_dir, 'affiliate-website.log')
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
    except (OSError, IOError) as e:
        # Fallback to console-only logging if file logging fails
        print(f"Warning: Could not set up file logging: {e}")
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler()]
        )

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        print("🚀 Starting Affiliate Website Application...")
        
        # Validate environment variables
        print_env_status()
        validate_environment()
        
        # Show authentication configuration
        Config.print_auth_config()
        
        # Show API docs security configuration
        print("\n🔒 API Documentation Security:")
        print(f"   Environment: {'Production' if APIDocsSecurityConfig.is_production() else 'Development'}")
        print(f"   Docs Enabled: {'✅ Yes' if APIDocsSecurityConfig.docs_enabled() else '❌ No (disabled in production)'}")
        if APIDocsSecurityConfig.get_api_docs_key():
            print(f"   Access Key: ✅ Required (X-API-Docs-Key header or ?api_docs_key parameter)")
        allowed_ips = APIDocsSecurityConfig.get_allowed_ips()
        if allowed_ips:
            print(f"   IP Whitelist: ✅ Enabled ({len(allowed_ips)} IPs allowed)")
        if APIDocsSecurityConfig.allow_localhost():
            print(f"   Localhost: ✅ Allowed")
        print()
        
        # Show admin security configuration
        print("🔐 Admin Panel Security:")
        if AdminSecurityConfig.is_admin_auth_enabled():
            print(f"   Authentication: ✅ Enabled")
            print(f"   Username: {AdminSecurityConfig.get_admin_username()}")
            print(f"   Password: ✅ Configured")
            print(f"   Login URL: /admin/login")
        else:
            print(f"   Authentication: ⚠️  Disabled (set ADMIN_PASSWORD to enable)")
            print(f"   Warning: Admin pages are accessible without authentication!")
        print()
        if APIDocsSecurityConfig.allow_localhost():
            print(f"   Localhost: ✅ Allowed")
        print()
        
        print("🔄 Initializing database connection...")
        start_time = time.time()
        
        # Force database initialization
        from app.database import initialize_database
        initialize_database()
        
        # Create tables
        create_tables()
        
        startup_time = time.time() - start_time
        print(f"✅ Database initialized and tables created/verified in {startup_time:.2f}s")
        
    except Exception as e:
        print(f"⚠️ Database startup error: {e}")
        print("⚠️ Application will continue but database features may not work.")
        # Don't fail startup - allow app to run without database
    yield
    # Shutdown
    print("Application shutdown complete.")

# Determine if docs should be enabled based on environment
docs_enabled = APIDocsSecurityConfig.docs_enabled()

app = FastAPI(
    title="Affiliate Website",
    description="A comprehensive affiliate marketing website with Cuelinks API integration",
    version="1.0.0",
    debug=os.getenv("DEBUG", "False").lower() == "true",
    lifespan=lifespan,
    # Conditionally enable/disable docs
    docs_url="/docs" if docs_enabled else None,
    redoc_url="/redoc" if docs_enabled else None,
    openapi_url="/openapi.json" if docs_enabled else None,
)

# Add Session middleware for OAuth (MUST be added before other middleware)
app.add_middleware(
    SessionMiddleware, 
    secret_key=os.getenv('SECRET_KEY', 'your-secret-key-here')
)

# Add admin authentication middleware (protects /admin/* endpoints)
app.middleware("http")(admin_authentication_middleware)

# Add API docs security middleware (if docs are enabled)
if docs_enabled:
    app.middleware("http")(api_docs_security_middleware)

# Add CORS middleware to handle caching and cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add middleware to prevent caching of API responses
@app.middleware("http")
async def add_cache_control_header(request: Request, call_next):
    response = await call_next(request)
    # Add cache control headers to prevent browser caching of API responses
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
# Mount images separately to handle /images/placeholder.jpg requests
app.mount("/images", StaticFiles(directory="static/images"), name="images")

# Templates
templates = Jinja2Templates(directory="templates")

# Health check endpoint for deployment platforms
@app.get("/health")
async def health_check():
    """Health check endpoint for deployment platforms like Easypanel, Render, etc."""
    try:
        # Test database connection
        db_status = db_available()
        return {
            "status": "healthy",
            "database": "connected" if db_status else "disconnected",
            "timestamp": time.time()
        }
    except Exception as e:
        return {
            "status": "unhealthy", 
            "error": str(e),
            "timestamp": time.time()
        }

# Health check endpoint for Render
@app.get("/", response_class=HTMLResponse)
async def homepage(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/offers", response_class=HTMLResponse)
async def offers_page(request: Request):
    return templates.TemplateResponse("offers.html", {"request": request})

@app.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})

@app.get("/categories", response_class=HTMLResponse)
async def categories_page(request: Request):
    return templates.TemplateResponse("categories.html", {"request": request})

@app.get("/link-generator", response_class=HTMLResponse)
async def link_generator_page(request: Request):
    return templates.TemplateResponse("link_generator.html", {"request": request})

@app.get("/admin/sync", response_class=HTMLResponse)
async def sync_admin_page(request: Request):
    """Admin interface for managing offers sync"""
    return templates.TemplateResponse("offers_sync_admin.html", {"request": request})

@app.get("/health")
async def health_check_detailed():
    return {"status": "ok", "timestamp": time.time()}

# Include routers
app.include_router(campaigns_controller.router)
app.include_router(offers_controller.router)
app.include_router(chat_controller.router, prefix="/api")
app.include_router(links_controller.router)
app.include_router(auth_controller.router, prefix="/auth")
app.include_router(images_controller.router, prefix="/api")
app.include_router(admin_images_controller.router)  # Admin image upload routes
app.include_router(top_deals_controller.router)  # Top deals routes
app.include_router(health_controller.router)  # Health monitoring endpoints
app.include_router(seo_controller.router)

# Include feedback router
try:
    from app.controllers.feedback_controller import router as feedback_router
    app.include_router(feedback_router)
    print("✅ Feedback routes loaded successfully")
except ImportError as e:
    print(f"⚠️ Could not load feedback routes: {e}")

# Include new sync and scheduler routers
try:
    from app.controllers.offers_sync_controller import router as offers_sync_router
    from app.controllers.scheduler_controller import router as scheduler_router
    from app.controllers.semantic_chat_controller import router as semantic_chat_router
    app.include_router(offers_sync_router)
    app.include_router(scheduler_router)
    app.include_router(semantic_chat_router)
    print("✅ Sync, scheduler, and semantic chat routes loaded successfully")
except ImportError as e:
    print(f"⚠️ Could not load additional routes: {e}")
    print("⚠️ Advanced features may not be available")

# Create database tables on startup
# Moved to lifespan event

# Root route - Homepage
@app.get("/", response_class=HTMLResponse)
async def homepage(request: Request, db: Session = Depends(get_db)):
    # Get featured offers for homepage (optimized query)
    featured_offers = []
    if db is not None:
        try:
            featured_offers = db.query(Offer).filter(
                Offer.status == "live"
            ).order_by(Offer.created_at.desc()).limit(6).all()
        except Exception as e:
            print(f"⚠️ Database query warning: {e}")
            featured_offers = []  # Fallback to empty list
    else:
        print("⚠️ Database not available, using empty offers list.")
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "featured_offers": featured_offers
    })

# Offers page
@app.get("/offers", response_class=HTMLResponse)
async def offers_page(request: Request):
    return templates.TemplateResponse("offers.html", {"request": request})

# Categories page
@app.get("/categories", response_class=HTMLResponse)
async def categories_page(request: Request):
    return templates.TemplateResponse("categories.html", {"request": request})

# Link generator page
@app.get("/link-generator", response_class=HTMLResponse)
async def link_generator_page(request: Request):
    return templates.TemplateResponse("link_generator.html", {"request": request})

# Chat page
@app.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})

# Test Chat API page (for debugging)
@app.get("/test-chat", response_class=HTMLResponse)
async def test_chat_page(request: Request):
    return templates.TemplateResponse("test_chat_api.html", {"request": request})

# Admin login page
@app.get("/admin/login", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    """Display admin login page."""
    return HTMLResponse(content=LOGIN_PAGE_HTML)

# Admin login handler
@app.post("/admin/login")
async def admin_login(request: Request, username: str = Form(...), password: str = Form(...)):
    """Handle admin login form submission."""
    # Verify credentials
    if verify_admin_credentials(username, password):
        # Generate session token
        token = generate_admin_token(username)
        
        # Get the redirect URL (where user was trying to go)
        next_url = request.query_params.get("next", "/admin/sync")
        
        # Create response with redirect
        response = RedirectResponse(url=next_url, status_code=303)
        
        # Set secure cookies
        response.set_cookie(
            key="admin_session",
            value=token,
            httponly=True,
            max_age=86400,  # 24 hours
            samesite="lax"
        )
        response.set_cookie(
            key="admin_username",
            value=username,
            httponly=True,
            max_age=86400,
            samesite="lax"
        )
        
        return response
    else:
        # Invalid credentials, redirect back to login with error
        return RedirectResponse(url="/admin/login?error=invalid", status_code=303)

# Admin logout
@app.get("/admin/logout")
async def admin_logout(request: Request):
    """Handle admin logout."""
    response = RedirectResponse(url="/admin/login", status_code=303)
    response.delete_cookie("admin_session")
    response.delete_cookie("admin_username")
    return response

# Admin feedback page
@app.get("/admin/feedback", response_class=HTMLResponse)
async def admin_feedback_page(request: Request):
    return templates.TemplateResponse("admin_feedback.html", {"request": request})

# Admin user feedback page
@app.get("/admin/user-feedback", response_class=HTMLResponse)
async def admin_user_feedback_page(request: Request):
    return templates.TemplateResponse("user_feedback_admin.html", {"request": request})

if __name__ == "__main__":
    import uvicorn
    
    # Detect if we're in a production/deployment environment
    is_production = (
        os.getenv("ENVIRONMENT") == "production" or
        os.getenv("EASYPANEL") == "true" or
        os.getenv("EASYPANEL_PROJECT") or  # Easypanel sets this
        os.getenv("RAILWAY_ENVIRONMENT") or
        os.getenv("RENDER") or
        os.getenv("DYNO") or  # Heroku
        os.path.exists("/.dockerenv") or  # Running in Docker
        not os.getenv("DEBUG", "False").lower() == "true"
    )
    
    if is_production:
        print("🚀 Starting server in production mode...")
        uvicorn.run(
            "main:app", 
            host="0.0.0.0", 
            port=int(os.getenv("PORT", 8000)), 
            reload=False
        )
    else:
        print("🚀 Starting server in debug mode with auto-reload...")
        uvicorn.run(
            "main:app", 
            host="0.0.0.0", 
            port=8000, 
            reload=True,
            reload_dirs=["."],  # Only watch the current directory
            reload_excludes=["*.log", "*.pyc", "__pycache__/*", "logs/*", ".git/*"]
        )
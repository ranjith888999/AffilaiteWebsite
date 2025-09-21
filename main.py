from fastapi import FastAPI, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
from app.database import get_db, create_tables, db_available
from app.controllers import campaigns_controller, offers_controller, chat_controller, links_controller, auth_controller, images_controller
from app.models.database import Offer
from app.config import Config, validate_environment, print_env_status
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
        print("� Starting Affiliate Website Application...")
        
        # Validate environment variables
        print_env_status()
        validate_environment()
        
        # Show authentication configuration
        Config.print_auth_config()
        
        print("�🔄 Initializing database connection...")
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

app = FastAPI(
    title="Affiliate Website",
    description="A comprehensive affiliate marketing website with Cuelinks API integration",
    version="1.0.0",
    debug=os.getenv("DEBUG", "False").lower() == "true",
    lifespan=lifespan
)

# Add Session middleware for OAuth (MUST be added before other middleware)
app.add_middleware(
    SessionMiddleware, 
    secret_key=os.getenv('SECRET_KEY', 'your-secret-key-here')
)

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

# Admin feedback page
@app.get("/admin/feedback", response_class=HTMLResponse)
async def admin_feedback_page(request: Request):
    return templates.TemplateResponse("admin_feedback.html", {"request": request})

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
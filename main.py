from fastapi import FastAPI, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
from app.database import get_db, create_tables
from app.controllers import campaigns_controller, offers_controller, chat_controller, links_controller, auth_controller, images_controller
from app.models.database import Offer
import os
import time
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="Affiliate Website",
    description="A comprehensive affiliate marketing website with Cuelinks API integration",
    version="1.0.0"
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

# Create database tables on startup
@app.on_event("startup")
async def startup_event():
    try:
        start_time = time.time()
        create_tables()
        startup_time = time.time() - start_time
        print(f"✅ Database tables created/verified in {startup_time:.2f}s")
    except Exception as e:
        print(f"⚠️ Database startup warning: {e}")
        # Don't fail startup if tables already exist

# Root route - Homepage
@app.get("/", response_class=HTMLResponse)
async def homepage(request: Request, db: Session = Depends(get_db)):
    # Get featured offers for homepage (optimized query)
    try:
        featured_offers = db.query(Offer).filter(
            Offer.status == "live"
        ).order_by(Offer.created_at.desc()).limit(6).all()
    except Exception as e:
        print(f"⚠️ Database query warning: {e}")
        featured_offers = []  # Fallback to empty list
    
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
    print("🚀 Starting server in debug mode with auto-reload...")
    uvicorn.run("main:app", host="0.0.0.0", port=8003, reload=True)

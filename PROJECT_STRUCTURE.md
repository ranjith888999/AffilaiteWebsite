# Project Structure - Clean Version

## Core Application Files
```
├── main.py                     # FastAPI application entry point
├── init_render_database.py     # Database initialization for Render
├── requirements.txt            # All dependencies
├── requirements-core.txt       # Core web framework dependencies
├── requirements-ml.txt         # Machine learning dependencies
└── render.yaml                 # Render deployment configuration
```

## Application Code
```
app/
├── __init__.py
├── database.py                 # Database configuration and connection
├── controllers/                # API endpoints and page routes
│   ├── campaigns_controller.py
│   ├── offers_controller.py
│   ├── chat_controller.py
│   ├── links_controller.py
│   ├── auth_controller.py
│   └── images_controller.py
├── models/                     # Database models
│   └── database.py
└── services/                   # Business logic
    ├── cuelinks_service.py
    ├── semantic_search_service.py
    ├── rag_service.py
    └── advanced_rag_service.py
```

## Frontend
```
templates/                     # Jinja2 HTML templates
├── base.html
├── index.html                 # Homepage
├── offers.html                # Offers listing
├── chat.html                  # Chat interface
├── categories.html            # Categories page
├── link_generator.html        # Link generator tool
└── admin_feedback.html        # Admin interface

static/                        # CSS, JS, and images
├── css/
├── js/
└── images/
```

## Essential Scripts
```
scripts/
├── check_db.py               # Database connectivity check
├── check_data.py             # Data verification
├── initialize_database.py     # Database setup
├── fetch_and_embed_all_offers.py  # Data import
├── generate_complete_embeddings.py # ML embeddings
├── optimize_embeddings.py     # Performance optimization
└── regenerate_embeddings.py   # ML model refresh
```

## Deployment
```
├── Dockerfile.render          # Optimized Docker image for Render
├── startup_optimized.sh       # Application startup script
├── init-pgvector.sql          # PostgreSQL vector extension
└── .dockerignore              # Docker build exclusions
```

## Documentation
```
├── README.md                  # Main project documentation
├── DOCKER_DEPLOYMENT.md       # Docker deployment guide
├── RENDER_DEPLOYMENT_GUIDE.md # Render-specific deployment
├── RENDER_DOCKER_DEPLOYMENT.md # Docker on Render guide
├── RENDER_ENV_VARIABLES.md    # Environment variables
└── POSTGRESQL_EXTENSIONS.md   # Database extensions info
```

## Configuration
```
├── .env                       # Environment variables (not in git)
├── .gitignore                 # Git exclusions
└── .dockerignore              # Docker exclusions
```

## What Was Removed

### Test Files
- All `test_*.py` files (moved to development-only)
- `api_test.py`, `simple_test.py`
- Performance test files

### Batch Files
- All `*.bat` files (Windows-specific, not needed for cloud deployment)

### Redundant Docker Files
- `Dockerfile` (keeping `Dockerfile.render`)
- `docker-compose.yml` (not needed for Render)
- `Dockerfile.optimized` (consolidated into `Dockerfile.render`)

### Development/Debug Scripts
- All `fix_*.py`, `debug_*.py`, `diagnose_*.py` files
- Migration and reset scripts
- Verification and update scripts

### Temporary Documentation
- Performance analysis files
- Troubleshooting guides
- Fix summaries

### Platform-Specific Files
- Vercel configuration (`vercel.json`)
- Local environment files

## Benefits of Cleanup

1. **Reduced Repository Size**: ~40+ files removed
2. **Cleaner Deployments**: Faster Docker builds
3. **Better Maintenance**: Easier to navigate and understand
4. **Focused Codebase**: Only production-ready files remain
5. **Security**: No sensitive debug or test data exposed

## Development Workflow

For local development, you can still create test files as needed, but they won't be committed to the repository thanks to the updated `.gitignore`.

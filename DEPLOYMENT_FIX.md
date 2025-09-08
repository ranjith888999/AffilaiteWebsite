# Deployment Fix for Keras/TensorFlow Conflicts

## Problem
The deployment was failing due to conflicts between:
- Keras 3 (latest version)
- transformers library (requires Keras 2.x or tf-keras)
- sentence-transformers (depends on transformers)

## Solution Applied

### 1. Updated Requirements
- Added `tf-keras==2.17.0` to `requirements.txt` for full ML functionality
- `requirements-core.txt` excludes ML dependencies for stable deployment
- `requirements-hostinger.txt` uses lightweight dependencies

### 2. Lazy Loading Implementation
- Modified `semantic_chat_service.py` and `cuelinks_offers_service.py` 
- ML libraries are only imported when actually needed
- Application starts successfully even if ML libraries fail to load
- Graceful fallback to text-based search when ML is unavailable

### 3. Error Handling
- `main.py` already has try/catch for optional controllers
- Services provide fallback functionality when ML is unavailable
- Clear logging of what features are available/unavailable

## Deployment Options

### Option 1: Core Deployment (Recommended for Production)
```bash
# Use requirements-core.txt (no ML dependencies)
pip install -r requirements-core.txt
```
- ✅ Fast startup, stable deployment
- ✅ Core website functionality works
- ❌ Semantic search disabled (falls back to text search)
- ❌ AI chat responses disabled (shows simple messages)

### Option 2: Full ML Deployment
```bash
# Use requirements.txt with tf-keras fix
pip install -r requirements.txt
```
- ✅ Full semantic search with embeddings
- ✅ AI-powered chat responses
- ⚠️ Larger memory footprint
- ⚠️ Slower startup time

### Option 3: Hostinger Deployment
```bash
# Use requirements-hostinger.txt (optimized for hosting)
pip install -r requirements-hostinger.txt
```
- ✅ Balanced approach
- ✅ Essential features included
- ❌ Some ML features may be limited

## Files Modified
- `requirements.txt` - Added tf-keras
- `app/services/semantic_chat_service.py` - Lazy loading
- `app/services/cuelinks_offers_service.py` - Lazy loading
- `Dockerfile.production` - Core requirements only
- This documentation file

## Testing
After deployment, check logs for:
- `✅ sentence-transformers loaded successfully` (ML available)
- `⚠️ Warning: sentence-transformers not available` (fallback mode)

Both scenarios should result in a working application.

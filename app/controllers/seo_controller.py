from fastapi import APIRouter, Request, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.database import Offer, Campaign
from datetime import datetime

router = APIRouter()

@router.get("/robots.txt", include_in_schema=False)
async def robots_txt(request: Request):
    """Serve robots.txt to guide search engine crawlers"""
    content = """User-agent: *
Allow: /

# Sitemap location
Sitemap: {scheme}://{netloc}/sitemap.xml

# Disallow admin pages
Disallow: /admin/
Disallow: /api/admin/
""".format(scheme=request.url.scheme, netloc=request.url.netloc)
    return Response(content=content, media_type="text/plain")

@router.get("/sitemap.xml", include_in_schema=False)
async def sitemap(request: Request, db: Session = Depends(get_db)):
    """Generate dynamic XML sitemap with all pages, offers, and campaigns"""
    
    base_url = f"{request.url.scheme}://{request.url.netloc}"
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Static pages with high priority
    static_pages = [
        {"url": "/", "priority": "1.0", "changefreq": "daily"},
        {"url": "/offers", "priority": "0.9", "changefreq": "daily"},
        {"url": "/chat", "priority": "0.8", "changefreq": "weekly"},
        {"url": "/categories", "priority": "0.8", "changefreq": "weekly"},
    ]
    
    urlset = []
    
    # Add static pages
    for page in static_pages:
        urlset.append(f"""
    <url>
        <loc>{base_url}{page['url']}</loc>
        <lastmod>{today}</lastmod>
        <changefreq>{page['changefreq']}</changefreq>
        <priority>{page['priority']}</priority>
    </url>""")
    
    # Add dynamic offer pages if database is available
    if db is not None:
        try:
            # Get all active offers (limited to prevent huge sitemaps)
            offers = db.query(Offer).filter(
                Offer.status == "live"
            ).order_by(Offer.created_at.desc()).limit(1000).all()
            
            for offer in offers:
                last_modified = offer.updated_at.strftime('%Y-%m-%d') if offer.updated_at else today
                urlset.append(f"""
    <url>
        <loc>{base_url}/offers?search={offer.title.replace(' ', '+')}</loc>
        <lastmod>{last_modified}</lastmod>
        <changefreq>weekly</changefreq>
        <priority>0.7</priority>
    </url>""")
            
            # Add category pages
            categories = db.query(Offer.categories).distinct().limit(50).all()
            for cat_tuple in categories:
                if cat_tuple and cat_tuple[0]:
                    try:
                        import json
                        cat_dict = json.loads(cat_tuple[0]) if isinstance(cat_tuple[0], str) else cat_tuple[0]
                        for category in cat_dict.values():
                            if category:
                                urlset.append(f"""
    <url>
        <loc>{base_url}/offers?category={category.replace(' ', '%20')}</loc>
        <lastmod>{today}</lastmod>
        <changefreq>daily</changefreq>
        <priority>0.8</priority>
    </url>""")
                    except:
                        pass
                        
        except Exception as e:
            print(f"Error generating dynamic sitemap: {e}")
    
    sitemap_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">
{''.join(urlset)}
</urlset>"""
    
    return Response(content=sitemap_content, media_type="application/xml")

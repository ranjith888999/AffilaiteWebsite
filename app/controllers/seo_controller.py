from fastapi import APIRouter, Request, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.database import Offer, Campaign
from datetime import datetime
from html import escape
from urllib.parse import quote
import logging

router = APIRouter(tags=["SEO"])
logger = logging.getLogger(__name__)

@router.get("/robots.txt", include_in_schema=False, response_class=Response)
async def robots_txt(request: Request):
    """
    Serve robots.txt to guide search engine crawlers.
    This endpoint is ALWAYS public and accessible without authentication.
    """
    content = """User-agent: *
Allow: /

# Sitemap location
Sitemap: {scheme}://{netloc}/sitemap.xml

# Disallow admin pages
Disallow: /admin/
Disallow: /api/admin/

# Crawl-delay (optional - be nice to servers)
Crawl-delay: 1
""".format(scheme=request.url.scheme, netloc=request.url.netloc)
    
    # Return with appropriate headers for public access and caching
    return Response(
        content=content, 
        media_type="text/plain",
        headers={
            "Cache-Control": "public, max-age=86400",  # Cache for 24 hours
            "X-Robots-Tag": "noindex",  # Don't index robots.txt itself
        }
    )

@router.get("/sitemap.xml", include_in_schema=False, response_class=Response)
async def sitemap(request: Request, db: Session = Depends(get_db)):
    """
    Generate dynamic XML sitemap with all pages, offers, and campaigns.
    This endpoint is ALWAYS public and accessible without authentication.
    Required for SEO and search engine indexing.
    """
    
    try:
        base_url = f"{request.url.scheme}://{request.url.netloc}"
        today = datetime.now().strftime('%Y-%m-%d')
        
        logger.info(f"Generating sitemap for {base_url}")
        
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
                    # Properly escape special characters for XML
                    safe_title = quote(offer.title, safe='')
                    urlset.append(f"""
    <url>
        <loc>{base_url}/offers?search={safe_title}</loc>
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
                                    # Properly URL encode category names
                                    safe_category = quote(str(category), safe='')
                                    urlset.append(f"""
    <url>
        <loc>{base_url}/offers?category={safe_category}</loc>
        <lastmod>{today}</lastmod>
        <changefreq>daily</changefreq>
        <priority>0.8</priority>
    </url>""")
                        except:
                            pass
                            
            except Exception as e:
                logger.error(f"Error generating dynamic sitemap content: {e}")
                # Continue with static pages only
        
        sitemap_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">
{''.join(urlset)}
</urlset>"""
        
        logger.info(f"Sitemap generated successfully with {len(urlset)} URLs")
        
        # Return with proper headers for public access, caching, and SEO
        return Response(
            content=sitemap_content, 
            media_type="application/xml",
            headers={
                "Cache-Control": "public, max-age=3600",  # Cache for 1 hour
                "X-Robots-Tag": "noindex",  # Don't index sitemap.xml itself
                "Content-Type": "application/xml; charset=utf-8",
            }
        )
        
    except Exception as e:
        logger.error(f"Critical error generating sitemap: {e}")
        # Return minimal sitemap with just homepage
        minimal_sitemap = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>{request.url.scheme}://{request.url.netloc}/</loc>
        <lastmod>{datetime.now().strftime('%Y-%m-%d')}</lastmod>
        <changefreq>daily</changefreq>
        <priority>1.0</priority>
    </url>
</urlset>"""
        
        return Response(
            content=minimal_sitemap,
            media_type="application/xml",
            headers={
                "Cache-Control": "public, max-age=300",  # Cache for 5 minutes only on error
                "X-Robots-Tag": "noindex",
            }
        )

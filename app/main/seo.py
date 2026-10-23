'''
Search-engine plumbing for Jambo: robots.txt, sitemap.xml, and the
template helpers (canonical URL, absolute URLs, verification tags) that
base.html uses to build its <head>.

SITE_URL can be overridden with an environment variable; it defaults to
the live site so canonical URLs and the sitemap are always absolute and
always https, regardless of how nginx/Docker forwards the request.
'''
import os
from xml.sax.saxutils import escape

from flask import Blueprint, Response, has_request_context, request

from app.models.roommodel import Rooms

seo = Blueprint('seo', __name__)

SITE_URL_DEFAULT = "https://jambo.tbossci.com"

# Public pages worth indexing: (path, priority, change frequency)
STATIC_PAGES = [
    ("/", "1.0", "daily"),
    ("/room", "0.9", "daily"),
    ("/behost", "0.7", "monthly"),
    ("/about", "0.5", "monthly"),
    ("/contact", "0.4", "yearly"),
    ("/payment-policy", "0.3", "yearly"),
    ("/terms-of-use", "0.3", "yearly"),
    ("/booking-policy", "0.3", "yearly"),
]

# Everything private, transactional or state-changing. Crawling these
# wastes crawl budget and can surface account pages in results.
DISALLOWED = [
    "/admin/", "/api/", "/chat/", "/conversation/",
    "/udashboard", "/mybookings", "/mylistings", "/myreviews", "/profile",
    "/earnings", "/refunds", "/host/", "/rate-guest/", "/request-withdrawal",
    "/rooms/map-locations", "/set-notification-channel",
    "/login", "/signup", "/logout", "/reset_password", "/verify-email/",
    "/resend-verification", "/delete-account",
    "/booknow/", "/checkout/", "/payment/", "/paysuccess/", "/bookconfirm/",
    "/bookcancel", "/cancel-booking/", "/host-cancel-booking/", "/check-voucher",
    "/roomextra/", "/room/", "/update_roompics/", "/review/",
    "/set-language/", "/set-currency/", "/roomsearch",
]


def site_url():
    return os.getenv("SITE_URL", SITE_URL_DEFAULT).rstrip("/")


def absolute_url(url):
    '''Turns "/static/x.png" into a full URL; leaves full URLs (Cloudinary) alone.'''
    if not url:
        return ""
    if url.startswith(("http://", "https://")):
        return url
    return site_url() + (url if url.startswith("/") else "/" + url)


@seo.app_context_processor
def inject_seo():
    canonical = site_url() + "/"
    if has_request_context():
        path = request.path or "/"
        if path == "/home":
            path = "/"
        query = ""
        # Only the paginated room list carries a meaningful query string.
        page = request.args.get("page", type=int)
        if path == "/room" and page and page > 1:
            query = f"?page={page}"
        canonical = site_url() + path + query
    return dict(
        site_url=site_url(),
        canonical_url=canonical,
        abs_url=absolute_url,
        google_site_verification=os.getenv("GOOGLE_SITE_VERIFICATION", ""),
        bing_site_verification=os.getenv("BING_SITE_VERIFICATION", ""),
    )


@seo.route("/robots.txt")
def robots_txt():
    lines = ["User-agent: *", "Allow: /static/"]
    lines += [f"Disallow: {p}" for p in DISALLOWED]
    lines += ["", f"Sitemap: {site_url()}/sitemap.xml", ""]
    resp = Response("\n".join(lines), mimetype="text/plain")
    resp.headers["Cache-Control"] = "public, max-age=3600"
    return resp


@seo.route("/sitemap.xml")
def sitemap_xml():
    base = site_url()
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']

    for path, priority, freq in STATIC_PAGES:
        out.append(
            f"<url><loc>{escape(base + path)}</loc>"
            f"<changefreq>{freq}</changefreq><priority>{priority}</priority></url>")

    # Only rooms guests can actually book. Hidden/Maintenance rooms are
    # excluded (soft-deleted listings are set to 'Hidden').
    rooms = (Rooms.query.filter_by(status="Available")
             .with_entities(Rooms.id, Rooms.updated_at)
             .order_by(Rooms.id).limit(50000).all())  # 50,000 = sitemap protocol cap
    for room_id, updated in rooms:
        lastmod = f"<lastmod>{updated.date().isoformat()}</lastmod>" if updated else ""
        out.append(
            f"<url><loc>{escape(f'{base}/roomdetail/{room_id}')}</loc>{lastmod}"
            f"<changefreq>weekly</changefreq><priority>0.8</priority></url>")

    out.append("</urlset>")
    resp = Response("\n".join(out), mimetype="application/xml")
    resp.headers["Cache-Control"] = "public, max-age=3600"
    return resp

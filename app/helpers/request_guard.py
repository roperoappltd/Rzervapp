'''
Cross-site request guard for the few routes that still change state on a
plain GET (logout, language and currency switches). Their links live in
the page header on every template, so turning them into POST forms means
editing dozens of links; this check gives the same protection without it.

A request is accepted when the browser says it comes from our own site
(Sec-Fetch-Site: same-origin) or was typed/bookmarked (none). Browsers
without that header fall back to comparing the Referer/Origin host. If a
browser sends neither, it is allowed, so privacy extensions do not break
the site.
'''
from urllib.parse import urlparse
from flask import request


def is_same_origin_request():
    site = request.headers.get("Sec-Fetch-Site")
    if site:
        return site in ("same-origin", "none")
    origin = request.headers.get("Origin") or request.headers.get("Referer")
    if origin:
        return urlparse(origin).netloc == request.host
    return True

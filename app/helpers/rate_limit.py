'''
Small in-memory rate limiter -- no extra package needed.

Why this exists: some endpoints can be hit by anyone with no login and
cost real money or send real email (the AI assistant calls the paid
Anthropic API). Gunicorn runs ONE worker (see Dockerfile), so a plain
in-process counter is accurate. If you ever raise --workers, each worker
keeps its own counters (limits become per worker) -- move to Redis
(or Flask-Limiter with a Redis backend) at that point.

Two layers are used together on purpose:
  * per client (IP, or user id when logged in) -- stops one visitor
    hammering the endpoint;
  * one GLOBAL counter for the whole endpoint -- a spend ceiling that
    still holds if someone rotates IP addresses or spoofs headers.
'''
import time
from collections import defaultdict, deque

from flask import request

_hits = defaultdict(deque)
_MAX_KEYS = 20000  # safety valve so the dict can never grow without bound


def client_ip():
    '''Best available real client IP behind Cloudflare / Nginx Proxy Manager.
    request.remote_addr would be the proxy for EVERY visitor, so it is
    only the last resort. Headers can be forged by a client that reaches
    the app directly -- which is why callers also use a global limit.'''
    return (request.headers.get('CF-Connecting-IP')
            or request.headers.get('X-Real-IP')
            or (request.headers.get('X-Forwarded-For', '').split(',')[-1].strip())
            or request.remote_addr
            or 'unknown')


def check_rate_limit(bucket, key, limit, window_seconds):
    '''Records one hit and returns (allowed, retry_after_seconds).
    A blocked call is NOT recorded, so waiting out the window always works.'''
    now = time.monotonic()
    cutoff = now - window_seconds

    if len(_hits) > _MAX_KEYS:
        for k in [k for k, q in _hits.items() if not q or q[-1] <= cutoff]:
            _hits.pop(k, None)

    q = _hits[(bucket, key)]
    while q and q[0] <= cutoff:
        q.popleft()

    if len(q) >= limit:
        return False, int(q[0] + window_seconds - now) + 1

    q.append(now)
    return True, 0

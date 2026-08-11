from urllib.parse import urlparse
# from datetime import datetime, timedelta

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 5

def is_safe_redirect_url(target):
    '''Only allow redirecting to a relative, same-site path -- rejects
    anything with a scheme or netloc (i.e. a full URL to another domain),
    which is what makes the open-redirect attack possible.'''
    if not target:
        return False
    parsed = urlparse(target)
    return parsed.scheme == '' and parsed.netloc == '' and target.startswith('/') and not target.startswith('//')

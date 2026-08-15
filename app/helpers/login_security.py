from urllib.parse import urlparse
# from datetime import datetime, timedelta

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 5

# A real, valid bcrypt hash used ONLY for timing-safety when no user
# exists for the submitted email -- running a real bcrypt check even in
# that case keeps response time consistent, so an attacker can't tell
# "wrong password" apart from "no such account" by how fast the reply
# comes back. Any password will fail against this hash, which is the
# point -- it's never meant to match anything.
# FIXED: previously '$2b$12$' + 'x'*53, a synthetic string that merely
# looked hash-shaped but wasn't valid -- bcrypt's underlying library
# rejected it and crashed every login attempt for a non-existent email.
DUMMY_HASH_FOR_TIMING_SAFETY = '$2b$12$t7L674Z//M.PYzL74HYR/..h3GFjM72Oi.4r6XXxDW2i8/Pd7OcYq'

def is_safe_redirect_url(target):
    '''Only allow redirecting to a relative, same-site path -- rejects
    anything with a scheme or netloc (i.e. a full URL to another domain),
    which is what makes the open-redirect attack possible.'''
    if not target:
        return False
    parsed = urlparse(target)
    return parsed.scheme == '' and parsed.netloc == '' and target.startswith('/') and not target.startswith('//')
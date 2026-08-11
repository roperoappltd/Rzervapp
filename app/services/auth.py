from functools import wraps
from flask import abort, render_template
from flask_login import current_user


# custom decorators to restrict access to routes based on the user’s role
def role_required(*roles):
    def wrapper(func):
        @wraps(func)
        def decorated_view(*args, **kwargs):
            if not current_user.is_authenticated:
                return render_template('errors/403.html'), 403

            # User.role was replaced by User.is_admin -- 'admin' is the
            # only role that ever really existed, so treat any
            # role_required('admin') call as an is_admin check. This is a
            # drop-in fix ONLY if every existing call site uses 'admin'
            # and nothing else -- see the flag below.
            if 'admin' in roles and not current_user.is_admin:
                return render_template('errors/403.html'), 403

            return func(*args, **kwargs)
        return decorated_view
    return wrapper
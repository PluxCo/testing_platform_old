from functools import wraps

from flask import session, redirect, url_for


def fusionauth_login_required(view_func):
    @wraps(view_func)
    def decorated_view(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return view_func(*args, **kwargs)

    return decorated_view

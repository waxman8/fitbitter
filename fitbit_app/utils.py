from functools import wraps
from flask import session, redirect, url_for, request, jsonify

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "oauth_token" not in session:
            if request.path.startswith('/api/'):
                return jsonify({"error": "authentication_required"}), 401
            return redirect(url_for("login", source="dashboard" if request.path.startswith('/api/') else None))
        return f(*args, **kwargs)
    return decorated_function
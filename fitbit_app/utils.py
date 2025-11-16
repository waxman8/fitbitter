from functools import wraps
from flask import session, redirect, url_for, request, jsonify
from oauthlib.oauth2 import TokenExpiredError, MissingTokenError
from fitbit_app.api_client import get_fitbit_session

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "oauth_token" not in session:
            if request.path.startswith('/api/'):
                return jsonify({"error": "authentication_required"}), 401
            return redirect(url_for("login", source="dashboard" if request.path.startswith('/api/') else None))
        
        try:
            fitbit = get_fitbit_session()
            # Make a lightweight API call to check token validity and trigger auto-refresh
            fitbit.get("https://api.fitbit.com/1/user/-/profile.json")
        except (TokenExpiredError, MissingTokenError):
            # If token is expired or missing and refresh fails, redirect to login
            session.clear()
            if request.path.startswith('/api/'):
                return jsonify({"error": "authentication_required"}), 401
            return redirect(url_for("login"))
            
        return f(*args, **kwargs)
    return decorated_function
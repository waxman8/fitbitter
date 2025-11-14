import os
from dotenv import load_dotenv

load_dotenv()

# Flask App Configuration
SECRET_KEY = os.urandom(24)
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'None'
SESSION_COOKIE_DOMAIN = None

# CORS Configuration
CORS_ORIGIN = os.getenv("CORS_ORIGIN", "http://127.0.0.1:3000")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://127.0.0.1:3000")

# Cache Configuration
REDIS_URL = os.getenv("REDIS_URL")

# Fitbit OAuth 2.0 configuration
CLIENT_ID = os.getenv("FITBIT_CLIENT_ID")
CLIENT_SECRET = os.getenv("FITBIT_CLIENT_SECRET")
REDIRECT_URI = os.getenv("FITBIT_REDIRECT_URI", "http://127.0.0.1:5001/callback")
AUTHORIZATION_BASE_URL = "https://www.fitbit.com/oauth2/authorize"
TOKEN_URL = "https://api.fitbit.com/oauth2/token"
SCOPE = ["activity", "heartrate", "location", "nutrition", "profile", "settings", "sleep", "social", "weight"]
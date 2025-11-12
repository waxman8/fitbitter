import os
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, redirect, request, session, url_for, render_template
from flask_cors import CORS
from flask.json import jsonify
import plotly
import pandas as pd
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import TokenExpiredError
from oauthlib.oauth2.rfc6749.errors import MissingTokenError
from dotenv import load_dotenv

from fitbit_app import config
from fitbit_app.api_client import (
    get_fitbit_session,
    fetch_daily_heart_rate,
    fetch_intraday_heart_rate,
    fetch_sleep_logs,
)
from fitbit_app.processor import (
    process_sleep_data,
    process_sleep_data_for_api,
)
from fitbit_app.utils import login_required

load_dotenv()

app = Flask(__name__, template_folder='../templates')
app.secret_key = config.SECRET_KEY

# Session cookie configuration
app.config.update(
    SESSION_COOKIE_SECURE=config.SESSION_COOKIE_SECURE,
    SESSION_COOKIE_HTTPONLY=config.SESSION_COOKIE_HTTPONLY,
    SESSION_COOKIE_SAMESITE=config.SESSION_COOKIE_SAMESITE,
    SESSION_COOKIE_DOMAIN=config.SESSION_COOKIE_DOMAIN
)

# elaborate CORS configuration
CORS(app, 
     resources={
         r"/api/*": {
             "origins": [config.CORS_ORIGIN],
             "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
             "allow_headers": ["Content-Type", "Authorization", "Accept"],
             "supports_credentials": True,
             "expose_headers": ["Content-Type", "Authorization"]
         }
     },
     supports_credentials=True
)

# Log CORS info for each request - TODO: Remove in production
@app.before_request
def log_cors_info():
    if request.path.startswith('/api/'):
        app.logger.info(f"🌐 CORS Request - Origin: {request.headers.get('Origin')}")
        app.logger.info(f"🌐 CORS Request - Method: {request.method}")
        app.logger.info(f"🌐 CORS_ORIGIN configured as: {config.CORS_ORIGIN}")

# Log configuration values - TODO: Remove in production
app.logger.info(f"CORS_ORIGIN configured as: {config.CORS_ORIGIN}")
app.logger.info(f"FRONTEND_URL configured as: {config.FRONTEND_URL}")

# Log each incoming request's origin and path TODO: Remove in production
@app.before_request
def log_request_info():
    origin = request.headers.get('Origin')
    app.logger.info(f"Request from origin: {origin}")
    app.logger.info(f"Request path: {request.path}")
    app.logger.info(f"Request method: {request.method}")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login")
def login():
    source = request.args.get('source')
    fitbit = OAuth2Session(config.CLIENT_ID, redirect_uri=config.REDIRECT_URI, scope=config.SCOPE)
    authorization_url, state = fitbit.authorization_url(config.AUTHORIZATION_BASE_URL)
    session["oauth_state"] = state
    session["login_source"] = source if source else "backend"
    return redirect(authorization_url)

@app.route("/callback")
def callback():
    try:
        if "error" in request.args:
            error_message = request.args.get("error_description", "Unknown error.")
            app.logger.error(f"Fitbit authorization failed: {request.args.get('error')} - {error_message}")
            session.clear()
            return redirect(url_for("login"))

        fitbit = OAuth2Session(config.CLIENT_ID, state=session.get("oauth_state"), redirect_uri=config.REDIRECT_URI)
        
        # Use the authorization code from the request to fetch the token
        code = request.args.get('code')
        token = fitbit.fetch_token(
            config.TOKEN_URL,
            client_secret=config.CLIENT_SECRET,
            code=code
        )
        
        session["oauth_token"] = token
        # Redirect based on the source of the login
        if session.get("login_source") == "dashboard":
            return redirect(f"{config.FRONTEND_URL}/dashboard")
        else:
            return redirect(url_for("profile"))
    
    except MissingTokenError as e:
        app.logger.error(f"MissingTokenError in Fitbit callback: {e}")
        session.clear()
        return redirect(url_for("login"))
    except TokenExpiredError as e:
        app.logger.error(f"TokenExpiredError in Fitbit callback: {e}")
        session.clear()
        return redirect(url_for("login"))
    except Exception as e:
        app.logger.error(f"An unexpected error occurred in Fitbit callback: {e}")
        session.clear()
        return redirect(url_for("login"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/profile")
@login_required
def profile():
    fitbit = get_fitbit_session()
    try:
        response = fitbit.get("https://api.fitbit.com/1/user/-/devices.json")
        
        if response.status_code == 200:
            devices = response.json()
        else:
            devices = None

        return render_template("profile.html", devices=devices)
    except (TokenExpiredError, MissingTokenError):
        session.pop("oauth_token", None)
        return redirect(url_for("login"))

@app.route("/raw-heart-rate-data")
@login_required
def raw_heart_rate_data():
    print("............. fetching")
    fitbit = get_fitbit_session()
    try:
        # Get today's date
        today = datetime.now().date()
        # Get the date 7 days ago
        seven_days_ago = today - timedelta(days=7)
        
        # Format dates for the API endpoint
        today_str = today.strftime('%Y-%m-%d')
        seven_days_ago_str = seven_days_ago.strftime('%Y-%m-%d')
        
        api_url = f"https://api.fitbit.com/1/user/-/activities/heart/date/{seven_days_ago_str}/{today_str}.json"
        
        response = fitbit.get(api_url)
        
        if response.status_code == 200:
            raw_heart_rate_data = response.json()
            
            # Process data to extract resting heart rate
            resting_heart_rate_list = []
            if raw_heart_rate_data and 'activities-heart' in raw_heart_rate_data:
                for day_data in raw_heart_rate_data['activities-heart']:
                    date = day_data.get('dateTime')
                    value_data = day_data.get('value', {})
                    resting_heart_rate = value_data.get('restingHeartRate', 'N/A')
                    resting_heart_rate_list.append({'date': date, 'resting_heart_rate': resting_heart_rate})
            
            heart_rate_data = resting_heart_rate_list
        else:
            heart_rate_data = None

        return render_template("raw_heart_rate.html", heart_rate_data=heart_rate_data)
    except (TokenExpiredError, MissingTokenError):
        session.pop("oauth_token", None)
        return redirect(url_for("login"))

@app.route("/detailed_heart_rate")
@login_required
def detailed_heart_rate():
    fitbit = get_fitbit_session()
    try:
        start_datetime_str = request.args.get('start_datetime')
        end_datetime_str = request.args.get('end_datetime')

        if start_datetime_str and end_datetime_str:
            start_time = datetime.strptime(start_datetime_str, '%Y-%m-%dT%H:%M')
            end_time = datetime.strptime(end_datetime_str, '%Y-%m-%dT%H:%M')
        else:
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=23)

        start_date_str = start_time.strftime('%Y-%m-%d')
        end_date_str = end_time.strftime('%Y-%m-%d')
        start_time_str = start_time.strftime('%H:%M')
        end_time_str = end_time.strftime('%H:%M')

        api_url = (
            f"https://api.fitbit.com/1/user/-/activities/heart/date/{start_date_str}/{end_date_str}/1min/"
            f"time/{start_time_str}/{end_time_str}.json"
        )
        response = fitbit.get(api_url)

        if response.status_code == 200:
            intraday_data = response.json()
        else:
            intraday_data = None
            app.logger.error(f"Fitbit API request failed with status code {response.status_code}: {response.text}")

        return render_template(
            "detailed_heart_rate.html",
            heart_rate_data=intraday_data,
            start_datetime=start_time.strftime('%Y-%m-%dT%H:%M'),
            end_datetime=end_time.strftime('%Y-%m-%dT%H:%M')
        )
    except (TokenExpiredError, MissingTokenError):
        session.pop("oauth_token", None)
        return redirect(url_for("login"))

@app.route("/detailed-sleep-data")
@login_required
def detailed_sleep_data():
    fitbit = get_fitbit_session()
    try:
        start_datetime_str = request.args.get('start_datetime')
        end_datetime_str = request.args.get('end_datetime')

        if start_datetime_str and end_datetime_str:
            start_datetime = datetime.strptime(start_datetime_str, '%Y-%m-%dT%H:%M')
            end_datetime = datetime.strptime(end_datetime_str, '%Y-%m-%dT%H:%M')
        else:
            end_datetime = datetime.now()
            start_datetime = end_datetime - timedelta(hours=23)

        heart_rate_data = fetch_intraday_heart_rate(fitbit, start_datetime, end_datetime)
        all_sleep_logs = fetch_sleep_logs(fitbit, start_datetime, end_datetime)

        graphJSON, total_awake_time = process_sleep_data(all_sleep_logs, heart_rate_data, start_datetime, end_datetime)

        return render_template(
            "detailed_sleep_data.html",
            graphJSON=graphJSON,
            total_awake_time=total_awake_time,
            start_datetime=start_datetime.strftime('%Y-%m-%dT%H:%M'),
            end_datetime=end_datetime.strftime('%Y-%m-%dT%H:%M')
        )
    except (TokenExpiredError, MissingTokenError):
        session.pop("oauth_token", None)
        return redirect(url_for("login"))

@app.route("/api/v1/sleep-data")
@login_required
def api_sleep_data():
    fitbit = get_fitbit_session()
    try:
        start_datetime_str = request.args.get('start_datetime')
        end_datetime_str = request.args.get('end_datetime')

        if start_datetime_str and end_datetime_str:
            # Use strptime for robust ISO 8601 parsing across Python versions
            start_datetime = datetime.strptime(start_datetime_str, "%Y-%m-%dT%H:%M:%S.%f%z")
            end_datetime = datetime.strptime(end_datetime_str, "%Y-%m-%dT%H:%M:%S.%f%z")
        else:
            # Default to a sensible range if not provided
            end_datetime = datetime.now()
            start_datetime = end_datetime - timedelta(hours=12)

        heart_rate_data = fetch_intraday_heart_rate(fitbit, start_datetime, end_datetime)
        daily_heart_rate_data = fetch_daily_heart_rate(fitbit, start_datetime.date(), end_datetime.date())
        all_sleep_logs = fetch_sleep_logs(fitbit, start_datetime, end_datetime)

        processed_data = process_sleep_data_for_api(all_sleep_logs, heart_rate_data, daily_heart_rate_data, start_datetime, end_datetime)

        return jsonify(processed_data)

    except (TokenExpiredError, MissingTokenError):
        return jsonify({"error": "authentication_required"}), 401
    except Exception as e:
        app.logger.error(f"An error occurred in /api/v1/sleep-data: {e}")
        return jsonify({"error": "internal_server_error"}), 500

@app.route("/api/v1/auth-status")
@login_required
def auth_status():
    """A lightweight endpoint to check if the user has an active session."""
    return jsonify({"isAuthenticated": True})

# CORS handling for all responses
@app.after_request
def after_request(response):
    origin = request.headers.get('Origin')
    if origin == config.CORS_ORIGIN:
        response.headers.add('Access-Control-Allow-Origin', origin)
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,Accept')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

# Preflight handling for auth-status endpoint
@app.route('/api/v1/auth-status', methods=['OPTIONS'])
def auth_status_options():
    return '', 200

if __name__ == "__main__":
    # This allows us to use a plain HTTP callback
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    port = int(os.environ.get("PORT", 5001))
    app.run(debug=True, host="0.0.0.0", port=port)
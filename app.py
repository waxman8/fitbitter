import os
from datetime import datetime, timedelta
from flask import Flask, redirect, request, session, url_for, render_template
from flask.json import jsonify
import requests
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import TokenExpiredError
from oauthlib.oauth2.rfc6749.errors import MissingTokenError
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Fitbit OAuth 2.0 configuration
client_id = os.getenv("FITBIT_CLIENT_ID")
client_secret = os.getenv("FITBIT_CLIENT_SECRET")
redirect_uri = "http://127.0.0.1:5000/callback"
authorization_base_url = "https://www.fitbit.com/oauth2/authorize"
token_url = "https://api.fitbit.com/oauth2/token"
scope = ["activity", "heartrate", "location", "nutrition", "profile", "settings", "sleep", "social", "weight"]

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login")
def login():
    fitbit = OAuth2Session(client_id, redirect_uri=redirect_uri, scope=scope)
    authorization_url, state = fitbit.authorization_url(authorization_base_url)
    session["oauth_state"] = state
    return redirect(authorization_url)

@app.route("/callback")
def callback():
    try:
        if "error" in request.args:
            error_message = request.args.get("error_description", "Unknown error.")
            app.logger.error(f"Fitbit authorization failed: {request.args.get('error')} - {error_message}")
            session.clear()
            return redirect(url_for("login"))

        fitbit = OAuth2Session(client_id, state=session.get("oauth_state"), redirect_uri=redirect_uri)
        
        # Use the authorization code from the request to fetch the token
        code = request.args.get('code')
        token = fitbit.fetch_token(
            token_url,
            client_secret=client_secret,
            code=code
        )
        
        session["oauth_token"] = token
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

def token_updater(token):
    session["oauth_token"] = token

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/profile")
def profile():
    if "oauth_token" not in session:
        return redirect(url_for("login"))

    fitbit = OAuth2Session(
        client_id,
        token=session["oauth_token"],
        auto_refresh_url=token_url,
        auto_refresh_kwargs={
            "client_id": client_id,
            "client_secret": client_secret,
        },
        token_updater=token_updater,
    )

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
def raw_heart_rate_data():
    if "oauth_token" not in session:
        return redirect(url_for("login"))

    fitbit = OAuth2Session(
        client_id,
        token=session["oauth_token"],
        auto_refresh_url=token_url,
        auto_refresh_kwargs={
            "client_id": client_id,
            "client_secret": client_secret,
        },
        token_updater=token_updater,
    )
    
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

@app.route("/heart_rate_intraday")
def heart_rate_intraday():
    if "oauth_token" not in session:
        return redirect(url_for("login"))

    fitbit = OAuth2Session(
        client_id,
        token=session["oauth_token"],
        auto_refresh_url=token_url,
        auto_refresh_kwargs={
            "client_id": client_id,
            "client_secret": client_secret,
        },
        token_updater=token_updater,
    )

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
            "heart_rate_intraday.html",
            heart_rate_data=intraday_data,
            start_datetime=start_time.strftime('%Y-%m-%dT%H:%M'),
            end_datetime=end_time.strftime('%Y-%m-%dT%H:%M')
        )
    except (TokenExpiredError, MissingTokenError):
        session.pop("oauth_token", None)
        return redirect(url_for("login"))


@app.route("/detailed-sleep-data")
def detailed_sleep_data():
    if "oauth_token" not in session:
        return redirect(url_for("login"))

    fitbit = OAuth2Session(
        client_id,
        token=session["oauth_token"],
        auto_refresh_url=token_url,
        auto_refresh_kwargs={
            "client_id": client_id,
            "client_secret": client_secret,
        },
        token_updater=token_updater,
    )

    try:
        # Get yesterday's date
        yesterday = datetime.now().date() - timedelta(days=1)
        yesterday_str = yesterday.strftime('%Y-%m-%d')
        
        api_url = f"https://api.fitbit.com/1.2/user/-/sleep/date/{yesterday_str}.json"
        
        response = fitbit.get(api_url)
        
        if response.status_code == 200:
            sleep_data = response.json()
            # Get the first sleep log
            sleep_log = sleep_data['sleep'][0] if sleep_data.get('sleep') else None
        else:
            sleep_log = None
            app.logger.error(f"Fitbit API request for sleep failed with status code {response.status_code}: {response.text}")

        heart_rate_data = None
        if sleep_log:
            start_time_str = sleep_log['startTime']
            end_time_str = sleep_log['endTime']
            
            # Parse the datetime strings
            start_time = datetime.fromisoformat(start_time_str)
            end_time = datetime.fromisoformat(end_time_str)

            start_date_str = start_time.strftime('%Y-%m-%d')
            end_date_str = end_time.strftime('%Y-%m-%d')
            start_time_str_req = start_time.strftime('%H:%M')
            end_time_str_req = end_time.strftime('%H:%M')

            hr_api_url = (
                f"https://api.fitbit.com/1/user/-/activities/heart/date/{start_date_str}/{end_date_str}/1min/"
                f"time/{start_time_str_req}/{end_time_str_req}.json"
            )
            hr_response = fitbit.get(hr_api_url)

            if hr_response.status_code == 200:
                heart_rate_data = hr_response.json()
            else:
                app.logger.error(f"Fitbit API request for heart rate failed with status code {hr_response.status_code}: {hr_response.text}")


        return render_template("detailed_sleep_data.html", sleep_data=sleep_log, heart_rate_data=heart_rate_data)
    except (TokenExpiredError, MissingTokenError):
        session.pop("oauth_token", None)
        return redirect(url_for("login"))


if __name__ == "__main__":
    # This allows us to use a plain HTTP callback
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    app.run(debug=True)
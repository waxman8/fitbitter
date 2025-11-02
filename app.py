import os
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, redirect, request, session, url_for, render_template
from flask.json import jsonify
import plotly
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import json
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import TokenExpiredError
from oauthlib.oauth2.rfc6749.errors import MissingTokenError
from dotenv import load_dotenv
from fitbit_utils import get_fitbit_session

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


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "oauth_token" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

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


def fetch_intraday_heart_rate(fitbit, start_datetime, end_datetime):
    hr_start_date_str = start_datetime.strftime('%Y-%m-%d')
    hr_end_date_str = end_datetime.strftime('%Y-%m-%d')
    hr_start_time_str = start_datetime.strftime('%H:%M')
    hr_end_time_str = end_datetime.strftime('%H:%M')

    hr_api_url = (
        f"https://api.fitbit.com/1/user/-/activities/heart/date/{hr_start_date_str}/{hr_end_date_str}/1min/"
        f"time/{hr_start_time_str}/{hr_end_time_str}.json"
    )
    print(f"Fetching heart rate data from URL: {hr_api_url}")
    hr_response = fitbit.get(hr_api_url)
    return hr_response.json() if hr_response.status_code == 200 else None

def process_sleep_data(all_sleep_logs, heart_rate_data, start_datetime, end_datetime):
    graphJSON = {}
    total_awake_time = 0
    if all_sleep_logs and heart_rate_data:
        all_sleep_df = pd.DataFrame()
        for sleep_log in all_sleep_logs:
            log_start_time = datetime.fromisoformat(sleep_log['startTime'])
            log_end_time = datetime.fromisoformat(sleep_log['endTime'])
            if log_start_time < end_datetime and log_end_time > start_datetime:
                sleep_df = pd.DataFrame(sleep_log['levels']['data'])
                sleep_df['startTime'] = pd.to_datetime(sleep_df['dateTime'])
                sleep_df['endTime'] = sleep_df.apply(lambda row: row['startTime'] + timedelta(seconds=row['seconds']), axis=1)
                all_sleep_df = pd.concat([all_sleep_df, sleep_df])

        if not all_sleep_df.empty:
            hr_df = pd.DataFrame()
            if heart_rate_data and 'activities-heart-intraday' in heart_rate_data:
                intraday_dataset = heart_rate_data['activities-heart-intraday']['dataset']
                if intraday_dataset:
                    hr_df = pd.DataFrame(intraday_dataset)
                    
                    start_date_str = heart_rate_data['activities-heart'][0]['dateTime']
                    current_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                    
                    timestamps = []
                    last_time = None
                    for t_str in hr_df['time']:
                        time_obj = datetime.strptime(t_str, '%H:%M:%S').time()
                        if last_time and time_obj < last_time:
                            current_date += timedelta(days=1)
                        timestamps.append(datetime.combine(current_date, time_obj))
                        last_time = time_obj
                    
                    hr_df['time'] = timestamps

            if not hr_df.empty:
                hr_df = hr_df[(hr_df['time'] >= start_datetime) & (hr_df['time'] <= end_datetime)]
                if not hr_df.empty:
                    hr_df['smoothed_value'] = hr_df['value'].rolling(window=9, center=True).mean()
                else:
                    hr_df['smoothed_value'] = pd.Series(dtype='float64')

            fig = make_subplots(specs=[[{"secondary_y": True}]])
            sleep_stage_map = {
                'wake': {'order': 4, 'color': 'YELLOW', 'label': 'WAKE'},
                'rem': {'order': 3, 'color': 'PURPLE', 'label': 'REM'},
                'light': {'order': 2, 'color': 'BLUE', 'label': 'LIGHT'},
                'deep': {'order': 1, 'color': 'BLACK', 'label': 'DEEP'}
            }
            heart_rate_color = 'rgba(219, 86, 86, 0.9)'
            all_sleep_df['order'] = all_sleep_df['level'].map(lambda x: sleep_stage_map.get(x, {}).get('order'))

            for level, data in all_sleep_df.groupby('level'):
                info = sleep_stage_map.get(level, {})
                if not info: continue
                for i, row in data.iterrows():
                    fig.add_trace(
                        go.Scatter(
                            x=[row['startTime'], row['endTime']], y=[info['order'], info['order']],
                            mode='lines', line=dict(width=20, color=info['color']),
                            name=info['label'], showlegend=(i == 0)
                        ),
                        secondary_y=False,
                    )

            if not hr_df.empty and 'smoothed_value' in hr_df.columns:
                fig.add_trace(
                    go.Scatter(x=hr_df['time'], y=hr_df['smoothed_value'], mode='lines', name='Heart Rate', line=dict(color=heart_rate_color)),
                    secondary_y=True,
                )
            
            fig.update_yaxes(
                title_text="Sleep Stage", secondary_y=False,
                tickvals=[1, 2, 3, 4], ticktext=['DEEP', 'LIGHT', 'REM', 'WAKE'],
                range=[0.5, 4.5]
            )
            fig.update_yaxes(title_text="Heart Rate (bpm)", secondary_y=True)
            graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
            total_awake_time = all_sleep_df[all_sleep_df['level'] == 'wake']['seconds'].sum()
    return graphJSON, total_awake_time

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
        
        all_sleep_logs = []
        current_date = start_datetime.date()
        while current_date <= end_datetime.date():
            date_str = current_date.strftime('%Y-%m-%d')
            sleep_api_url = f"https://api.fitbit.com/1.2/user/-/sleep/date/{date_str}.json"
            sleep_response = fitbit.get(sleep_api_url)
            if sleep_response.status_code == 200:
                sleep_data = sleep_response.json()
                if sleep_data.get('sleep'):
                    all_sleep_logs.extend(sleep_data['sleep'])
            current_date += timedelta(days=1)

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


if __name__ == "__main__":
    # This allows us to use a plain HTTP callback
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    app.run(debug=True)
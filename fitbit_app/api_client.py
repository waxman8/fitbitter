from flask import current_app, session, redirect, url_for
from datetime import timedelta
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import TokenExpiredError
from oauthlib.oauth2.rfc6749.errors import MissingTokenError
from . import config

def get_fitbit_session():
    """Creates and returns an OAuth2Session for the Fitbit API."""
    token = session.get("oauth_token")
    if not token:
        # This should be handled by a login_required decorator,
        # but as a fallback, we can redirect.
        # Note: This will raise a RuntimeError if called outside of a request context.
        return redirect(url_for("login"))

    return OAuth2Session(
        config.CLIENT_ID,
        token=token,
        auto_refresh_url=config.TOKEN_URL,
        auto_refresh_kwargs={
            "client_id": config.CLIENT_ID,
            "client_secret": config.CLIENT_SECRET,
        },
        token_updater=lambda t: session.update({"oauth_token": t}),
    )

# The data fetching functions have been moved to the FitbitService class
# in fitbit_app/service.py. This file now only contains the session setup.
def fetch_daily_heart_rate(fitbit, start_date, end_date):
    """Fetches daily heart rate data, including resting heart rate, for a given date range."""
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
    
    api_url = f"https://api.fitbit.com/1/user/-/activities/heart/date/{start_date_str}/{end_date_str}.json"
    
    response = fitbit.get(api_url)
    
    if response.status_code == 200:
        return response.json()
    else:
        current_app.logger.error(f"Fitbit API request for daily heart rate failed with status code {response.status_code}: {response.text}")
        return None

def fetch_intraday_heart_rate(fitbit, start_datetime, end_datetime):
    """Fetches intraday heart rate data for a given datetime range."""
    hr_start_date_str = start_datetime.strftime('%Y-%m-%d')
    hr_end_date_str = end_datetime.strftime('%Y-%m-%d')
    hr_start_time_str = start_datetime.strftime('%H:%M')
    hr_end_time_str = end_datetime.strftime('%H:%M')

    hr_api_url = (
        f"https://api.fitbit.com/1/user/-/activities/heart/date/{hr_start_date_str}/{hr_end_date_str}/1min/"
        f"time/{hr_start_time_str}/{hr_end_time_str}.json"
    )
    current_app.logger.info(f"Fetching heart rate data from URL: {hr_api_url}")
    hr_response = fitbit.get(hr_api_url)
    return hr_response.json() if hr_response.status_code == 200 else None

def fetch_sleep_logs(fitbit, start_datetime, end_datetime):
    """Fetches all sleep logs for a given datetime range."""
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
        else:
            current_app.logger.error(f"Fitbit sleep API request failed: {sleep_response.status_code} {sleep_response.text}")
        current_date += timedelta(days=1)
    return all_sleep_logs

def fetch_spo2_intraday(fitbit, start_datetime, end_datetime):
    """Fetches intraday SpO2 data for a given datetime range."""
    start_date_str = start_datetime.strftime('%Y-%m-%d')
    end_date_str = end_datetime.strftime('%Y-%m-%d')

    # The SpO2 intraday API seems to work best when fetching single days.
    # We will loop through the date range and aggregate the results.
    all_spo2_data = []
    current_date = start_datetime.date()
    while current_date <= end_datetime.date():
        date_str = current_date.strftime('%Y-%m-%d')
        api_url = f"https://api.fitbit.com/1/user/-/spo2/date/{date_str}/all.json"
        current_app.logger.info(f"Fetching SpO2 data from URL: {api_url}")
        
        response = fitbit.get(api_url)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('minutes'):
                all_spo2_data.extend(data['minutes'])
        else:
            current_app.logger.error(f"Fitbit SpO2 API request for {date_str} failed with status code {response.status_code}: {response.text}")
        
        current_date += timedelta(days=1)
        
    return {"minutes": all_spo2_data}
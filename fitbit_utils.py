import os
from flask import session
from requests_oauthlib import OAuth2Session

client_id = os.getenv("FITBIT_CLIENT_ID")
client_secret = os.getenv("FITBIT_CLIENT_SECRET")
token_url = "https://api.fitbit.com/oauth2/token"

def token_updater(token):
    session["oauth_token"] = token

def get_fitbit_session():
    return OAuth2Session(
        client_id,
        token=session.get("oauth_token"),
        auto_refresh_url=token_url,
        auto_refresh_kwargs={
            "client_id": client_id,
            "client_secret": client_secret,
        },
        token_updater=token_updater,
    )
import os
from flask import Flask, redirect, request, session, url_for, render_template
from flask.json import jsonify
import requests
from requests_oauthlib import OAuth2Session
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
    if "oauth_token" in session:
        return redirect(url_for("profile"))
    return render_template("index.html")

@app.route("/login")
def login():
    fitbit = OAuth2Session(client_id, redirect_uri=redirect_uri, scope=scope)
    authorization_url, state = fitbit.authorization_url(authorization_base_url)
    session["oauth_state"] = state
    return redirect(authorization_url)

@app.route("/callback")
def callback():
    fitbit = OAuth2Session(client_id, state=session["oauth_state"])
    token = fitbit.fetch_token(token_url, client_secret=client_secret, authorization_response=request.url)
    session["oauth_token"] = token
    return redirect(url_for("profile"))

@app.route("/profile")
def profile():
    if "oauth_token" not in session:
        return redirect(url_for("login"))

    fitbit = OAuth2Session(client_id, token=session["oauth_token"])
    response = fitbit.get("https://api.fitbit.com/1/user/-/devices.json")
    
    if response.status_code == 200:
        devices = response.json()
    else:
        devices = None

    return render_template("profile.html", devices=devices)

if __name__ == "__main__":
    # This allows us to use a plain HTTP callback
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    app.run(debug=True)
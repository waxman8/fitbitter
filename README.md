# Fitbitter

A simple Python Flask application to connect to the Fitbit API using OAuth 2.0 and display user device information.

## Prerequisites

- Python 3.6+
- An existing Python virtual environment

## Setup and Installation

1.  **Clone the repository (or download the files):**
    ```bash
    git clone <repository-url>
    cd fitbitter
    ```

2.  **Activate your virtual environment:**
    Replace `/path/to/your/venv/bin/activate` with the actual path to your virtual environment's activation script.
    ```bash
    source /path/to/your/venv/bin/activate
    ```

3.  **Install the dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *(Note: We will create the `requirements.txt` file in the next step.)*

## Fitbit Application Registration

To use this application, you need to register a new application on the Fitbit Developer site.

1.  Go to [https://dev.fitbit.com/](https://dev.fitbit.com/) and log in with your Fitbit account.
2.  Click on **"MANAGE" -> "Register An App"**.
3.  Fill out the application registration form:
    -   **Application Name:** `Fitbitter` (or any name you prefer)
    -   **Description:** A simple app to view my Fitbit data.
    -   **Application Website:** `http://127.0.0.1:5000`
    -   **Organization:** Your name or organization
    -   **Organization Website:** `http://127.0.0.1:5000`
    -   **OAuth 2.0 Application Type:** `Personal`
    -   **Callback URL:** `http://127.0.0.1:5000/callback`
    -   **Default Access Type:** `Read-Only`
4.  Agree to the terms of service and click **"Register"**.

You will now see your application's details, including the **"OAuth 2.0 Client ID"** and **"Client Secret"**.

## Configuration

1.  Rename the `.env.example` file to `.env`. *(We will create this file.)*
2.  Open the `.env` file and replace `YOUR_CLIENT_ID` and `YOUR_CLIENT_SECRET` with the credentials you obtained from the Fitbit Developer site.

    ```
    FITBIT_CLIENT_ID='YOUR_CLIENT_ID'
    FITBIT_CLIENT_SECRET='YOUR_CLIENT_SECRET'
    ```

## Running the Application

1.  Make sure your virtual environment is activated.
2.  Run the Flask application:
    ```bash
    python app.py
    ```
3.  Open your web browser and go to `http://127.0.0.1:5000`.
4.  Click the "Login with Fitbit" link and authorize the application.

You should be redirected back to the application and see a list of your Fitbit devices as well as a few menu items for querying some data from Fitbit. 

## Dashboard

This project includes a Next.js dashboard to visualize your Fitbit data.

### Running the Dashboard

1.  **Navigate to the dashboard directory:**
    ```bash
    cd dashboard
    ```

2.  **Install the dependencies:**
    ```bash
    npm install
    ```

3.  **Run the development server:**
    ```bash
    npm run dev
    ```

4.  Open your web browser and go to `http://localhost:3000`.
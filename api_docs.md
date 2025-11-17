# API Documentation

This document provides details on the available API endpoints for the Fitbitter application.

---

## Authentication

All API endpoints require authentication. The client must have a valid session cookie, which is obtained through the OAuth2 login flow. If the session is not valid, the API will return a `401 Unauthorized` error.

---

## Endpoints

### 1. Authentication Status

A lightweight endpoint to check if the user has an active and authenticated session.

-   **URL**: `/api/v1/auth-status`
-   **Method**: `GET`
-   **Authentication**: Required.

**Success Response (200 OK)**

Returns a JSON object indicating the user is authenticated.

```json
{
  "isAuthenticated": true
}
```

**Error Response (401 Unauthorized)**

Returned if the user does not have a valid session.

```json
{
  "error": "authentication_required"
}
```

---

### 2. Sleep Data

Fetches and processes sleep and heart rate data for a specified time range.

-   **URL**: `/api/v1/sleep-data`
-   **Method**: `GET`
-   **Authentication**: Required.

**Query Parameters**

| Parameter        | Type   | Description                                                                                                 | Required |
| ---------------- | ------ | ----------------------------------------------------------------------------------------------------------- | -------- |
| `start_datetime` | string | The start of the time range in ISO 8601 format (`YYYY-MM-DDTHH:MM:SS.ffffffZ`). | Yes      |
| `end_datetime`   | string | The end of the time range in ISO 8601 format (`YYYY-MM-DDTHH:MM:SS.ffffffZ`).   | Yes      |

**Success Response (200 OK)**

Returns a JSON object containing processed sleep and heart rate data.

```json
{
  "metadata": {
    "startTime": "2023-10-27T00:00:00+00:00",
    "endTime": "2023-10-27T08:00:00+00:00",
    "totalAwakeTimeMinutes": 30
  },
  "sleepStages": [
    {
      "level": "wake",
      "startTime": "2023-10-27T00:00:00+00:00",
      "endTime": "2023-10-27T00:05:00+00:00",
      "durationSeconds": 300
    },
    {
      "level": "light",
      "startTime": "2023-10-27T00:05:00+00:00",
      "endTime": "2023-10-27T01:30:00+00:00",
      "durationSeconds": 5100
    }
  ],
  "heartRate": [
    {
      "time": "2023-10-27T00:00:00+00:00",
      "value": 65
    },
    {
      "time": "2023-10-27T00:01:00+00:00",
      "value": 64
    }
  ],
  "restingHeartRate": 60
}
```

**Error Responses**

-   **401 Unauthorized**: Returned if the user does not have a valid session.
    ```json
    {
      "error": "authentication_required"
    }
    ```
-   **500 Internal Server Error**: Returned if an unexpected error occurs on the server.
    ```json
    {
      "error": "internal_server_error"
    }
    ```
---

### 3. Resting Heart Rate

Retrieves the daily resting heart rate for a specified date range.

-   **URL**: `/api/v1/resting-heart-rate`
-   **Method**: `GET`
-   **Authentication**: Required.

**Query Parameters**

| Parameter    | Type   | Description                               | Required |
|--------------|--------|-------------------------------------------|----------|
| `start_date` | string | The start of the date range in `YYYY-MM-DD`. | Yes      |
| `end_date`   | string | The end of the date range in `YYYY-MM-DD`.   | Yes      |

**Success Response (200 OK)**

Returns a JSON array of objects, each containing a date and the resting heart rate for that day.

```json
[
  {
    "date": "2024-01-01",
    "restingHeartRate": 60
  },
  {
    "date": "2024-01-02",
    "restingHeartRate": 61
  }
]
```

**Error Responses**

-   **400 Bad Request**: Returned if `start_date` or `end_date` are missing or in an invalid format.
    ```json
    {
      "error": "Invalid date format. Please use YYYY-MM-DD."
    }
    ```
-   **401 Unauthorized**: Returned if the user does not have a valid session.
    ```json
    {
      "error": "authentication_required"
    }
    ```
-   **500 Internal Server Error**: Returned if an unexpected error occurs on the server.
    ```json
    {
      "error": "internal_server_error"
    }
    ```
---

### 4. Intraday SpO2 Data

Fetches intraday SpO2 (blood oxygen saturation) data for a specified time range.

-   **URL**: `/api/v1/spo2-intraday`
-   **Method**: `GET`
-   **Authentication**: Required.

**Query Parameters**

| Parameter        | Type   | Description                                                                                                 | Required |
| ---------------- | ------ | ----------------------------------------------------------------------------------------------------------- | -------- |
| `start_datetime` | string | The start of the time range in ISO 8601 format (`YYYY-MM-DDTHH:MM:SS.ffffffZ`). | Yes      |
| `end_datetime`   | string | The end of the time range in ISO 8601 format (`YYYY-MM-DDTHH:MM:SS.ffffffZ`).   | Yes      |

**Success Response (200 OK)**

Returns a JSON object containing the intraday SpO2 data.

```json
{
  "minutes": [
    {
      "minute": "2023-10-27T00:00:00",
      "value": 95.5
    },
    {
      "minute": "2023-10-27T00:01:00",
      "value": 96.0
    }
  ]
}
```

**Error Responses**

-   **400 Bad Request**: Returned if `start_datetime` or `end_datetime` are missing or in an invalid format.
    ```json
    {
      "error": "start_datetime and end_datetime parameters are required"
    }
    ```
-   **401 Unauthorized**: Returned if the user does not have a valid session.
    ```json
    {
      "error": "authentication_required"
    }
    ```
-   **500 Internal Server Error**: Returned if an unexpected error occurs on the server.
    ```json
    {
      "error": "internal_server_error"
    }

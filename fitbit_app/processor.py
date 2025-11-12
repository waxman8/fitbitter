import pandas as pd
import plotly
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from datetime import datetime, timedelta, timezone

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

def process_sleep_data_for_api(all_sleep_logs, heart_rate_data, daily_heart_rate_data, start_datetime, end_datetime):
    """Processes sleep and heart rate data and returns it in a structured JSON format for an API."""
    processed_data = {
        "metadata": {
            "startTime": start_datetime.isoformat(),
            "endTime": end_datetime.isoformat(),
            "totalAwakeTimeMinutes": 0
        },
        "sleepStages": [],
        "heartRate": [],
        "restingHeartRate": None
    }
    total_awake_time_seconds = 0

    if not all_sleep_logs:
        return processed_data

    # Process sleep stages
    all_sleep_df = pd.DataFrame()
    for sleep_log in all_sleep_logs:
        log_start_time = datetime.fromisoformat(sleep_log['startTime']).replace(tzinfo=timezone.utc)
        log_end_time = datetime.fromisoformat(sleep_log['endTime']).replace(tzinfo=timezone.utc)
        if log_start_time < end_datetime and log_end_time > start_datetime:
            sleep_df = pd.DataFrame(sleep_log['levels']['data'])
            # Ensure parsed datetimes are timezone-aware (UTC)
            sleep_df['startTime'] = pd.to_datetime(sleep_df['dateTime']).dt.tz_localize('utc')
            sleep_df['endTime'] = sleep_df.apply(lambda row: row['startTime'] + timedelta(seconds=row['seconds']), axis=1)
            all_sleep_df = pd.concat([all_sleep_df, sleep_df])

    if not all_sleep_df.empty:
        for index, row in all_sleep_df.iterrows():
            processed_data["sleepStages"].append({
                "level": row["level"],
                "startTime": row["startTime"].isoformat(),
                "endTime": row["endTime"].isoformat(),
                "durationSeconds": row["seconds"]
            })
        total_awake_time_seconds = all_sleep_df[all_sleep_df['level'] == 'wake']['seconds'].sum()
        processed_data["metadata"]["totalAwakeTimeMinutes"] = round(total_awake_time_seconds / 60)


    # Process heart rate
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
                # Make the timestamp timezone-aware (UTC)
                aware_timestamp = datetime.combine(current_date, time_obj).replace(tzinfo=timezone.utc)
                timestamps.append(aware_timestamp)
                last_time = time_obj
            
            hr_df['time'] = timestamps
            hr_df = hr_df[(hr_df['time'] >= start_datetime) & (hr_df['time'] <= end_datetime)]

            for index, row in hr_df.iterrows():
                processed_data["heartRate"].append({
                    "time": row["time"].isoformat(),
                    "value": row["value"]
                })

    # Process resting heart rate for the start date
    if daily_heart_rate_data and 'activities-heart' in daily_heart_rate_data and daily_heart_rate_data['activities-heart']:
        first_day_data = daily_heart_rate_data['activities-heart'][0]
        rhr = first_day_data.get('value', {}).get('restingHeartRate')
        if rhr is not None:
            processed_data["restingHeartRate"] = rhr

    return processed_data
import os
import streamlit as st
import pandas as pd
import pytz
import plotly.graph_objects as go
from pymongo import MongoClient
import time
import random
from datetime import ( datetime )
from weather_api import ( WeatherApi )

client = MongoClient(st.secrets.database.mongodb_uri)
db = client['FarmCast']
collection = db['readings']
claimCollection = db['claims']

city = "Kolkata"
api_connection = WeatherApi(city)
weather_data = api_connection.get_current_weather()
next_3_day_data = api_connection.get_three_days_weather()

def format_datetime(dt):
    return dt.strftime('%Y-%m-%d %H:%M:%S')

def get_random_document():
    most_recent_doc = collection.find().sort([("_id", -1)]).limit(1)
    return most_recent_doc[0] if most_recent_doc else None


def load_data():
    document = get_random_document()
    print(document['temperatureDHT'])
    return document

def is_crop_in_danger(data):
    if (data['temperatureDHT'] > 30 or data['humidity'] > 80):
        return True
    return False

def get_claims():
    claims = claimCollection.find()
    return list(claims)

def change_claim_status(claim_id, status):
    updatedCollection = claimCollection.find_one_and_update({"_id": claim_id}, {'$set': {'status': status}})

    get_claims()

    if status == 'APPROVED':
        st.success(f"Claim {status} successfully!")

    if status == 'REJECTED':
        st.error(f"Claim rejected")

    return updatedCollection

def display_card(claim, show_verify=False, show_reject=False):
    st.markdown(
        f"""
        <div style="border-radius: 10px; padding: 1em; margin:1em; background-color: #f0f0f0;">
            <h3>{claim['reason']}</h3>
            <p>From: {format_datetime(claim['fromTime'])}</p>
            <p>To: {format_datetime(claim['toTime'])}</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    m = st.markdown("""
    <style>
    .stButton>button {
        border-radius: 5px;
        padding: 1em 2em;
        margin-right: 10px;
        font-weight: 900;
        font-size: 1em;
    }
    </style>
    """, unsafe_allow_html=True)

    if show_verify or show_reject:
        if show_verify and show_reject:
            col1, col2 = st.columns(2)
            with col1:
                if st.button('Reject', key='reject'+claim['_id'].__str__()):
                    change_claim_status(claim['_id'], 'REJECTED')
            with col2:
                if st.button('Verify', key='verify'+claim['_id'].__str__()):
                    change_claim_status(claim['_id'], 'APPROVED')
        elif show_verify:
            if st.button('Verify', key='verify'+claim['_id'].__str__()):
                change_claim_status(claim['_id'], 'APPROVED')

    st.markdown(
        f"""
        <hr>
        """,
        unsafe_allow_html=True
    )


def main():
    st.title('FarmCast')
    st.sidebar.title('FarmCast')
    st.sidebar.markdown('Welcome to FarmCast! Monitor your farm with real-time data.')
    
    # Create a sidebar with two tabs: Dashboard and Weather Forecast
    tabs = st.sidebar.radio('Navigation', ['Dashboard', 'Weather Forecast','Claims'])

    if tabs == 'Dashboard':
        st.subheader('Local Farm Parameters')

        col1, col2, col3 = st.columns(3)
        temp_metric = col1.empty()
        hum_metric = col2.empty()
        soil_metric = col3.empty()

        col1, col2, col3 = st.columns(3)
        temp_warning = col1.empty()
        hum_warning = col2.empty()
        soil_warning = col3.empty()

        col1, col2,col3 = st.columns(3)
        wind_dir_metric = col1.empty()
        wind_speed_metric = col2.empty()
        press_metric = col3.empty()

        col1, col2 = st.columns(2)
        alt_warning = col1.empty()
        press_warning = col2.empty()

        rainfall_metric = st.empty()
        crop_warning = st.empty()

        while True:
            data = load_data()
            
            # Update temperature metric and warning
            temp_metric.metric("Temperature", data['temperatureDHT'], "°C")
            temp_warning.warning("High" if data['temperatureDHT'] > 30 else "Low")

            # Update humidity metric and warning
            hum_metric.metric("Humidity", data['humidity'], "%")
            hum_warning.warning("High" if data['humidity'] > 80 else "Low")

            # Update soil moisture metric and warning
            soil_metric.metric("Soil Moisture", data['soilMoisture'], "%")
            soil_warning.warning("High" if data['soilMoisture'] > 50 else "Low")

            # Update altitude metric and warning
            wind_dir_metric.metric("Wind Direction", data['windDirection'], "")
            # alt_warning.warning("High" if data['windDirection'].iloc[-1] > 3000 else "Low")
            
            wind_speed_metric.metric("Wind Speed", data['windSpeed'], "kmph")
            # alt_warning.warning("High" if data['windDirection'].iloc[-1] > 3000 else "Low")

            # Update air pressure metric and warning
            press_metric.metric("Air Pressure", data['pressure'], "hPa")
            # press_warning.warning("High" if data['pressure'] > 1000 else "Low")

            # Update rainfall metric
            rainfall_metric.metric("Rainfall", "Yes" if data['isRaining'] else "No")

            # Update crop warning
            if is_crop_in_danger(data):
                crop_warning.warning('Your crop is in danger!')
            else:
                crop_warning.success('Your crop is safe!')

            time.sleep(10)

    elif tabs == 'Weather Forecast':
        st.subheader('Current Weather')
        st.markdown(f"""
            The current weather is <b>{weather_data["current_weather"]}</b> °C,
            with wind speed of <b>{weather_data["wind_speed"]}</b> kph.
            The current wind direction is <b>{weather_data["wind_direction"]}</b>.
            """,
            unsafe_allow_html=True
        )
        st.markdown(
            f'Weather condition: <b>{weather_data["temp_condition"]}</b>',
            unsafe_allow_html=True
        )

        st.subheader('Next 3 day forecast')

        time_now = datetime.now()
        IST = pytz.timezone('Asia/Kolkata')
        ist_time_now = datetime.now(IST)

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=next_3_day_data['date'],
                y=next_3_day_data['temp_c'],
                mode='lines',
                name='Hourly Temp (°C)'
            )
        )

        fig.add_trace(
                        go.Scatter(
                            x=next_3_day_data['date'],
                            y=next_3_day_data['feels_like'],
                            mode='lines',
                            name='Feels Like (°C)'
                        )
                    )

        fig.add_vline(
                x=ist_time_now,
                line_color="green",
                opacity=0.4
            )

        fig.update_layout(
                title="Hourly Weather Forecast",
                xaxis_title="Date",
                yaxis_title="Temperature °C",
                hovermode="x"
            )

        st.plotly_chart(fig, use_container_width=True)

        st.write('')  # Add an empty line to create space between the chart and the table

        st.write(next_3_day_data)
    else:
        st.subheader('Claims')
        claims = get_claims()
        if len(claims) > 0:
            pending_claims = [claim for claim in claims if claim['status'] == 'PENDING']
            approved_claims = [claim for claim in claims if claim['status'] == 'APPROVED']
            rejected_claims = [claim for claim in claims if claim['status'] == 'REJECTED']

            st.sidebar.title('Claims')
            status = st.sidebar.radio('Choose a status', ('Pending', 'Approved','Rejected'))

            if status == 'Pending':
                for claim in pending_claims:
                    display_card(claim, show_verify=True, show_reject=True)
            elif status == 'Approved':
                for claim in approved_claims:
                    display_card(claim)
            else:
                for claim in rejected_claims:
                    display_card(claim)
        else:
            st.write('No claims yet!')

    

if __name__ == '__main__':
    main()

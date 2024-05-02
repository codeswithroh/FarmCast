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
collection = db['crops']

city = "Kolkata"
api_connection = WeatherApi(city)
weather_data = api_connection.get_current_weather()
next_3_day_data = api_connection.get_three_days_weather()

def get_random_document():
    random_doc = collection.aggregate([{ '$sample': { 'size': 1 } }])
    return random_doc.next()


def load_data():
    document = get_random_document()
    data = pd.DataFrame(document['data'])
    data['timestamp'] = pd.to_datetime(data['timestamp'])
    return data

def is_crop_in_danger(data):
    return any(data['airTemperature'] > 30) or any(data['airHumidity'] > 80)

def main():
    st.title('FarmCast')
    st.sidebar.title('FarmCast')
    st.sidebar.markdown('Welcome to FarmCast! Monitor your farm with real-time data.')
    
    # Create a sidebar with two tabs: Dashboard and Weather Forecast
    tabs = st.sidebar.radio('Navigation', ['Dashboard', 'Weather Forecast'])

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

        col1, col2 = st.columns(2)
        alt_metric = col1.empty()
        press_metric = col2.empty()

        col1, col2 = st.columns(2)
        alt_warning = col1.empty()
        press_warning = col2.empty()

        rainfall_metric = st.empty()
        crop_warning = st.empty()

        while True:
            data = load_data()
            
            # Update temperature metric and warning
            temp_metric.metric("Temperature", round(data['airTemperature'].iloc[-1],2), "°C")
            temp_warning.warning("High" if data['airTemperature'].iloc[-1] > 30 else "Low")

            # Update humidity metric and warning
            hum_metric.metric("Humidity", round(data['airHumidity'].iloc[-1],2), "%")
            hum_warning.warning("High" if data['airHumidity'].iloc[-1] > 80 else "Low")

            # Update soil moisture metric and warning
            soil_metric.metric("Soil Moisture", round(data['soilMoisture'].iloc[-1],2), "%")
            soil_warning.warning("High" if data['soilMoisture'].iloc[-1] > 50 else "Low")

            # Update altitude metric and warning
            alt_metric.metric("Altitude", round(data['altitude'].iloc[-1],2), "m")
            alt_warning.warning("High" if data['altitude'].iloc[-1] > 3000 else "Low")

            # Update air pressure metric and warning
            press_metric.metric("Air Pressure", round(data['airPressure'].iloc[-1],2), "hPa")
            press_warning.warning("High" if data['airPressure'].iloc[-1] > 1000 else "Low")

            # Update rainfall metric
            rainfall_metric.metric("Rainfall", "Yes" if data['rainfall'].iloc[-1] else "No")

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


    

if __name__ == '__main__':
    main()

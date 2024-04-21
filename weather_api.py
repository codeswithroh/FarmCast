import os
import pytz
import requests
import streamlit as st
import pandas as pd
from datetime import ( datetime )
from dataclasses import ( dataclass )
from time import ( strftime, localtime )

@dataclass
class WeatherData:
    date: datetime
    temp_c: float
    feels_like: float
    weather_condition: str
    wind_kph: float
    wind_dir: str

class WeatherApi():

    def __init__(self, place):
        self.query = place
        self.dt = datetime.now().date()
        self._key = self.get_api_key()
        self.api_url = "http://api.weatherapi.com/v1/"
        self.query_key = f"key={self._key}&q={self.query}"

    def get_api_key(self):
        """
        Returns the API key from environment variable.
        """
        # API_KEY = os.environ.get('WEATHER_API')
        API_KEY = st.secrets.api_keys.weather_api
        if not API_KEY:
            raise ValueError('API key is not available.')
        else:
            return API_KEY

    def convert_gmt_time_to_ist(self, epoch_time):
        formatted_time = strftime('%Y-%m-%d %H:%M:%S', localtime(epoch_time))
        # Define the GMT timezone
        gmt_timezone = pytz.timezone('GMT')
        # Create a datetime object from the formatted time
        gmt_datetime = datetime.strptime(formatted_time, '%Y-%m-%d %H:%M:%S')
        # Set the timezone to IST
        ist_timezone = pytz.timezone('Asia/Kolkata')
        ist_datetime = gmt_timezone.localize(gmt_datetime).astimezone(ist_timezone)
        # Format the IST datetime as a string
        formatted_ist_time = ist_datetime.strftime('%Y-%m-%d %H:%M:%S')
        return formatted_ist_time

    def get_current_weather(self):
        """
        Method to Make a call to weather API
        """
        url = f"{self.api_url}current.json?{self.query_key}&dt={self.dt}"
        resp = requests.get(url=url)

        if resp.status_code == 200:
            data = resp.json()
            json_data = {
                'place': data['location']['name'],
                'current_weather': data['current']['temp_c'],
                'wind_speed': data['current']['wind_kph'],
                'wind_direction': data['current']['wind_dir'],
                'temp_condition': data['current']['condition']['text']
            }
            return json_data
        else:
            return 'Uh ooh, something went wrong while retriving data. Please check your input'

    def get_three_days_weather(self):
        """
        Method to get next 3 days forecast data
        """
        url = f"{self.api_url}forecast.json?{self.query_key}&days=3"
        resp = requests.get(url)

        # weather data list
        weather_data_list = []

        # return the JSON data if status code is 200
        if resp.status_code == 200:
            data = resp.json()['forecast']['forecastday']
            for forecast in data:
                for hour_data in forecast['hour']:
                    weather_data = WeatherData(
                        date = self.convert_gmt_time_to_ist(hour_data['time_epoch']),
                        temp_c = hour_data['temp_c'],
                        feels_like = hour_data['feelslike_c'],
                        weather_condition = hour_data['condition']['text'],
                        wind_kph = hour_data['wind_kph'],
                        wind_dir = hour_data['wind_dir']
                    )
                    weather_data_list.append(weather_data)
            weather_df = pd.DataFrame(
                [weather_data.__dict__ for weather_data in weather_data_list]
            )
            return weather_df
        else:
            return 'Uh ooh, something went wrong while retriving data. Please check your input.'
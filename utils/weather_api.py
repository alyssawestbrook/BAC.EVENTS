# utils/weather_api.py
import requests
from datetime import datetime
# Chat GPT assisted in the creation of this module (2025-12).

class WeatherAPI:
    """
    Retrieves weather forecasts for a given location and date using OpenWeatherMap API.
    """

    def __init__(self, api_key, city="Belmont,NC,US"):
        """
        Initialize the WeatherAPI with your API key and city.
        :param api_key: Your OpenWeatherMap API key
        :param city: City name, e.g., "Belmont,NC,US"
        """
        self.api_key = api_key
        self.city = city

    def get_forecast(self, date_str):
        """
        Get the forecast for a given date (YYYY-MM-DD).
        Returns a string with temperature and conditions, e.g., "72°F, Clear".
        """
        url = f"http://api.openweathermap.org/data/2.5/forecast/daily?q={self.city}&cnt=7&appid={self.api_key}&units=imperial"

        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            event_date = datetime.strptime(date_str, "%Y-%m-%d").date()

            for day in data.get("list", []):
                day_date = datetime.fromtimestamp(day["dt"]).date()
                if day_date == event_date:
                    temp = day["temp"]["day"]
                    conditions = day["weather"][0]["description"].capitalize()
                    return f"{temp:.0f}°F, {conditions}"
        except Exception as e:
            print("Weather API error:", e)
        return "No forecast available"
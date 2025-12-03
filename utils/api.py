# utils/api.py
# Queries Open-Meteo for daily forecasts for each event date and stores results in api_data.
# No API key required for Open-Meteo (https://open-meteo.com/).

import requests
import sqlite3
import json
from datetime import datetime
from collections import defaultdict

# Default coordinates for Belmont Abbey (change if you have a better lat/lon)
WEATHER_LAT = 35.26143   
WEATHER_LON = -81.036361 
OPEN_METEO_BASE = "https://api.open-meteo.com/v1/forecast"

class WeatherAPI:
    def __init__(self, db_path='db/campusconnect.db', lat=WEATHER_LAT, lon=WEATHER_LON):
        self.db_path = db_path
        self.lat = lat
        self.lon = lon

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        return conn, conn.cursor()

    def _format_date(self, iso_date):
        """
        Ensure date is YYYY-MM-DD; if iso_date empty return None.
        """
        if not iso_date:
            return None
        # Already YYYY-MM-DD? Accept it
        try:
            datetime.strptime(iso_date, "%Y-%m-%d")
            return iso_date
        except:
            # try parsing other formats (fallback)
            try:
                dt = datetime.fromisoformat(iso_date)
                return dt.strftime("%Y-%m-%d")
            except:
                return None

    def fetch_weather_for_date(self, date_iso):
        """
        Query Open-Meteo for a single date (daily fields).
        Returns parsed dict or None.
        """
        sd = date_iso
        ed = date_iso
        params = {
            "latitude": self.lat,
            "longitude": self.lon,
            "daily": "temperature_2m_max,temperature_2m_min,weathercode",
            "timezone": "America/New_York",
            "start_date": sd,
            "end_date": ed
        }
        resp = requests.get(OPEN_METEO_BASE, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        # Extract the day (first element)
        try:
            temp_max = data['daily']['temperature_2m_max'][0]
            temp_min = data['daily']['temperature_2m_min'][0]
            weather_code = data['daily']['weathercode'][0]
            # Simple mapping for common weather codes (Open-Meteo numeric codes)
            weather_text = self._weather_text_from_code(weather_code)
            return {
                "temp_max": temp_max,
                "temp_min": temp_min,
                "weather_code": weather_code,
                "weather_text": weather_text,
                "raw": data
            }
        except Exception as e:
            print("Open-Meteo parsing error:", e)
            return None

    def _weather_text_from_code(self, code):
        """
        Minimal mapping of weathercode to text (common cases).
        See Open-Meteo docs for full codes.
        """
        code = int(code)
        if code == 0:
            return "Clear"
        if code in [1,2,3]:
            return "Partly Cloudy"
        if 45 <= code <= 48:
            return "Fog"
        if 51 <= code <= 67:
            return "Rain"
        if 71 <= code <= 77:
            return "Snow/Ice"
        if 80 <= code <= 82:
            return "Rain Showers"
        if 95 <= code:
            return "Thunderstorm"
        return "Unknown"

    def fetch_and_store_for_events(self):
        """
        Query all distinct event dates in external_events and fetch weather per date,
        then insert into api_data (linking to events where possible).
        """
        conn, cursor = self._connect()
        cursor.execute('SELECT id, date FROM external_events WHERE date IS NOT NULL AND date != ""')
        rows = cursor.fetchall()
        if not rows:
            print("No event dates found to enrich with weather.")
            conn.close()
            return

        # Group event ids by date to later link event_id in api_data
        events_by_date = {}
        for event_id, date_iso in rows:
            if date_iso:
                events_by_date.setdefault(date_iso, []).append(event_id)

        inserted = 0
        for date_iso, event_ids in events_by_date.items():
            formatted = self._format_date(date_iso)
            if not formatted:
                print("Skipping invalid date:", date_iso)
                continue
            result = self.fetch_weather_for_date(formatted)
            if not result:
                continue
            # Insert one api_data row per event linked to this date
            for eid in event_ids:
                try:
                    cursor.execute('''
                        INSERT INTO api_data (event_id, date, provider, temp_max, temp_min, weather_code, weather_text, raw_json)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (eid, formatted, 'open-meteo', result['temp_max'], result['temp_min'], result['weather_code'], result['weather_text'], json.dumps(result['raw'])))
                    inserted += 1
                except Exception as e:
                    print("DB insert error (api_data):", e)
        conn.commit()
        conn.close()
        print(f"Weather API: inserted {inserted} api_data rows via Open-Meteo.")
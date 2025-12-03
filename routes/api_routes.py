# routes/api_routes.py
from flask import Blueprint, render_template
import sqlite3
from utils.api import WeatherAPI

api_routes = Blueprint('api_routes', __name__)

@api_routes.route('/api')
def api_page():
    api_client = WeatherAPI()
    try:
        api_client.fetch_and_store_for_events()
    except Exception as e:
        print("Weather fetch error:", e)

    conn = sqlite3.connect('db/campusconnect.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, event_id, date, provider, temp_max, temp_min, weather_code, weather_text FROM api_data ORDER BY date DESC, id DESC')
    api_data = cursor.fetchall()
    conn.close()

    return render_template('api.html', api_data=api_data)
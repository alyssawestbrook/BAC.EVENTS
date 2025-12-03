# routes/event_routes.py
from flask import Blueprint, render_template
import sqlite3
from utils.event_scraper import CampusEventScraper

event_routes = Blueprint('event_routes', __name__)

@event_routes.route('/events')
def events():
    # 1) Scrape both calendars (safe: exceptions are printed but will not crash)
    scraper = CampusEventScraper()
    try:
        scraper.scrape_all()
    except Exception as e:
        print("Error while scraping calendars:", e)

    # 2) Query DB for external_events & internal_events (if provided by starter)
    conn = sqlite3.connect('db/campusconnect.db')
    cursor = conn.cursor()

    # external events
    cursor.execute('SELECT id, title, date, time, location, description, source, url FROM external_events ORDER BY date DESC, id DESC')
    external_events = cursor.fetchall()

    # internal events (starter content) - safe fallback
    try:
        cursor.execute('SELECT id, title, date, time, location, description FROM internal_events')
        internal_events = cursor.fetchall()
    except Exception:
        internal_events = []

    conn.close()
    # Pass to template (templates expect sequence of tuples)
    return render_template('events.html', internal_events=internal_events, external_events=external_events)
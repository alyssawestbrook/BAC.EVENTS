"""
BAC.Events Web Scraper with Weather Integration

This module contains the CampusEventScraper class, which collects:
- Academic calendar events from Belmont Abbey College
- Athletics events from Abbey Athletics
- Weather data for each event day from AccuWeather
- Stores all collected data in the external_events SQLite table

Classes:
    CampusEventScraper:
        Attributes:
            db_path (str): Path to the SQLite database.

        Methods:
            _connect(): Opens a database connection.
            _clean(text): Cleans raw text for parsing.
            _parse_date(text, default_year): Converts text to ISO date string.
            _parse_time(text): Extracts event times.
            scrape_academic_calendar(url): Scrapes academic events.
            scrape_athletics_calendar(url): Scrapes athletics events.
            scrape_weather(): Retrieves weather for all event dates.
            scrape_all(academic_url, athletics_url): Runs all scrapers.
"""

import requests
from bs4 import BeautifulSoup
import sqlite3
import re
from datetime import datetime

ACADEMIC_CAL_URL = "https://belmontabbeycollege.edu/academics/calendar/#fall-2025"
ATHLETICS_CAL_URL = "https://abbeyathletics.com/calendar?date=12/2/2025&vtype=month"
WEATHER_URL = "https://www.accuweather.com/en/us/belmont/28012/weather-forecast/334866"

MONTHS = r"(January|February|March|April|May|June|July|August|September|October|November|December)"

class CampusEventScraper:
    def __init__(self, db_path='db/campusconnect.db'):
        """
        Initializes the scraper with the database path.

        Parameters:
            db_path (str): SQLite database file path.
        """
        self.db_path = db_path

    def _connect(self):
        """
        Creates a database connection and cursor.

        Returns:
            tuple: (connection, cursor)
        """
        conn = sqlite3.connect(self.db_path)
        return conn, conn.cursor()

    def _clean(self, txt):
        """
        Cleans whitespace from text.

        Parameters:
            txt (str): Raw text.

        Returns:
            str: Cleaned text.
        """
        if not txt:
            return ''
        return re.sub(r'\s+', ' ', txt).strip()

    def _parse_date(self, text, default_year=None):
        """
        Converts a text string into ISO date format YYYY-MM-DD.

        Parameters:
            text (str): Text containing date information.
            default_year (int, optional): Year to use if not present.

        Returns:
            str or None: ISO date string or None if parsing fails.
        """
        m = re.search(rf'{MONTHS}\s+(\d{{1,2}})(?:,\s*(\d{{4}}))?', text)
        if m:
            month_name = m.group(1)
            day = int(m.group(2))
            year = int(m.group(3)) if m.group(3) else (default_year or datetime.now().year)
            try:
                dt = datetime.strptime(f"{month_name} {day} {year}", "%B %d %Y")
                return dt.strftime("%Y-%m-%d")
            except Exception:
                return None
        m2 = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', text)
        if m2:
            month, day, year = int(m2.group(1)), int(m2.group(2)), int(m2.group(3))
            try:
                dt = datetime(year, month, day)
                return dt.strftime("%Y-%m-%d")
            except:
                return None
        return None

    def _parse_time(self, text):
        """
        Extracts time or time range from text.

        Parameters:
            text (str): Text containing time.

        Returns:
            str: Extracted time or empty string.
        """
        m = re.search(r'(\d{1,2}:\d{2}\s*(?:am|pm))\s*-\s*(\d{1,2}:\d{2}\s*(?:am|pm))', text, re.I)
        if m:
            return f"{m.group(1)} - {m.group(2)}"
        m2 = re.search(r'(\d{1,2}:\d{2}\s*(?:am|pm))', text, re.I)
        if m2:
            return m2.group(1)
        return ''

    def scrape_academic_calendar(self, url=ACADEMIC_CAL_URL):
        """
        Scrapes Belmont Abbey College academic calendar events.

        Parameters:
            url (str): URL of the academic calendar page.

        Returns:
            None — inserts events into external_events table.
        """
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')

        candidate = soup.find('div', class_='region-content') or soup.find('div', id='content') or soup
        items = []

        for tag in candidate.find_all(['p', 'li', 'div'], recursive=True):
            txt = self._clean(tag.get_text(separator=' ', strip=True))
            if not txt:
                continue
            if re.search(rf'{MONTHS}\s+\d{{1,2}}', txt) or re.search(r'\d{1,2}/\d{1,2}/\d{4}', txt) or '@' in txt:
                items.append(txt)

        conn, cursor = self._connect()
        inserted = 0
        for line in items:
            iso_date = self._parse_date(line)
            time = self._parse_time(line)
            title = line
            location = ''
            description = line
            try:
                cursor.execute('''
                    INSERT INTO external_events (title, date, time, location, description, source, url)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (title, iso_date or '', time, location, description, 'belmont_academic', url))
                inserted += 1
            except Exception as e:
                print("DB insert error (academic):", e)
        conn.commit()
        conn.close()
        print(f"Academic calendar: inserted {inserted} rows from {url}")

    def scrape_athletics_calendar(self, url=ATHLETICS_CAL_URL):
        """
        Scrapes Abbey Athletics calendar events.

        Parameters:
            url (str): URL of athletics calendar page.

        Returns:
            None — inserts events into external_events table.
        """
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')

        candidate = soup.find('div', id='calendar') or soup.find('div', class_='calendar') or soup
        items = []

        for a in candidate.find_all('a', href=True):
            text = self._clean(a.get_text(" ", strip=True))
            if text:
                if re.search(r'\d{1,2}:\d{2}', text) or re.search(r'\d{1,2}/\d{1,2}/\d{4}', text) or re.search(rf'{MONTHS}\s+\d{{1,2}}', text, re.I):
                    items.append((text, a.get('href')))
                else:
                    parent_text = self._clean(a.parent.get_text(" ", strip=True))
                    if parent_text and (re.search(r'\d{1,2}:\d{2}', parent_text) or re.search(rf'{MONTHS}\s+\d{{1,2}}', parent_text, re.I)):
                        items.append((parent_text, a.get('href')))

        if not items:
            for tag in candidate.find_all(['p', 'li', 'div']):
                txt = self._clean(tag.get_text(" ", strip=True))
                if txt and (re.search(r'\d{1,2}:\d{2}', txt) or re.search(rf'{MONTHS}\s+\d{{1,2}}', txt, re.I) or re.search(r'\d{1,2}/\d{1,2}/\d{4}', txt)):
                    items.append((txt, ''))

        conn, cursor = self._connect()
        inserted = 0
        for text, href in items:
            iso_date = self._parse_date(text)
            time = self._parse_time(text)
            title = text
            location = ''
            description = text
            try:
                cursor.execute('''
                    INSERT INTO external_events (title, date, time, location, description, source, url)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (title, iso_date or '', time, location, description, 'abbey_athletics', href or url))
                inserted += 1
            except Exception as e:
                print("DB insert error (athletics):", e)
        conn.commit()
        conn.close()
        print(f"Athletics calendar: inserted {inserted} rows from {url}")

    def scrape_weather(self):
        """
        Adds weather forecast data for each event in external_events.
        Uses AccuWeather for Belmont, NC.
        Note: Currently retrieves daily forecast summary heuristically.

        Returns:
            None — updates external_events table with weather summary.
        """
        conn, cursor = self._connect()
        cursor.execute("SELECT date, title FROM external_events WHERE date != ''")
        events = cursor.fetchall()
        for date, title in events:
            try:
                # Simple heuristic: scrape forecast summary from AccuWeather main page
                resp = requests.get(WEATHER_URL, timeout=10)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, 'html.parser')
                forecast = soup.find('div', class_='forecast-card') or soup.find('div', class_='current-weather-card')
                summary = forecast.get_text(" ", strip=True) if forecast else 'No forecast available'
                cursor.execute('''
                    UPDATE external_events
                    SET description = description || ' | Weather: ' || ?
                    WHERE title = ? AND date = ?
                ''', (summary, title, date))
            except Exception as e:
                print("Weather update failed:", e)
        conn.commit()
        conn.close()
        print(f"Weather data added for {len(events)} events")

    def scrape_all(self, academic_url=None, athletics_url=None):
        """
        Convenience method to scrape both calendars and update weather.

        Parameters:
            academic_url (str, optional): Academic calendar URL.
            athletics_url (str, optional): Athletics calendar URL.

        Returns:
            None
        """
        if academic_url:
            self.scrape_academic_calendar(academic_url)
        else:
            self.scrape_academic_calendar()
        if athletics_url:
            self.scrape_athletics_calendar(athletics_url)
        else:
            self.scrape_athletics_calendar()
        self.scrape_weather()
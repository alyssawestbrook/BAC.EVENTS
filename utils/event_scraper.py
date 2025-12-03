# utils/event_scraper.py
# Scraper for Belmont Abbey College academic calendar and Abbey Athletics calendar.
# - Targets two URLs (academic calendar and athletics calendar).
# - Parses text heuristically and inserts rows into external_events.
# Some text automatically corrected by copilot (2025-12).
# Patterns and parsing suggested and corrected with assistance from ChatGPT (2025-12).

import requests
from bs4 import BeautifulSoup
import sqlite3
import re
from datetime import datetime

ACADEMIC_CAL_URL = "https://belmontabbeycollege.edu/academics/calendar/#fall-2025"
ATHLETICS_CAL_URL = "https://abbeyathletics.com/calendar?date=12/2/2025&vtype=month"

MONTHS = r"(January|February|March|April|May|June|July|August|September|October|November|December)"

class CampusEventScraper:
    def __init__(self, db_path='db/campusconnect.db'):
        self.db_path = db_path

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        return conn, conn.cursor()

    def _clean(self, txt):
        if not txt:
            return ''
        return re.sub(r'\s+', ' ', txt).strip()

    def _parse_date(self, text, default_year=None):
        """
        Attempts to extract a date from text.
        Returns ISO date string YYYY-MM-DD or None.
        """
        # Try patterns like "December 2, 2025" or "December 2"
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
        # Try numeric date formats (MM/DD/YYYY)
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
        Extracts a time range like '11:00 am - 12:00 pm'.
        """
        m = re.search(r'(\d{1,2}:\d{2}\s*(?:am|pm))\s*-\s*(\d{1,2}:\d{2}\s*(?:am|pm))', text, re.I)
        if m:
            return f"{m.group(1)} - {m.group(2)}"
        # single time e.g. '11:00 am'
        m2 = re.search(r'(\d{1,2}:\d{2}\s*(?:am|pm))', text, re.I)
        if m2:
            return m2.group(1)
        return ''

    def scrape_academic_calendar(self, url=ACADEMIC_CAL_URL):
        """
        Scrapes the Belmont Abbey academic calendar page.
        Heuristics:
         - Finds main content block and looks for list items, paragraphs, or blocks that look like an event.
         - Extracts date (month/day or Month name day), time if present, and uses the line as description/title.
        """
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')

        # Try to find the content block that contains the calendar text.
        candidate = soup.find('div', class_='region-content') or soup.find('div', id='content') or soup
        items = []

        # Collect likely event lines from paragraphs, list items, and divs
        for tag in candidate.find_all(['p', 'li', 'div'], recursive=True):
            txt = self._clean(tag.get_text(separator=' ', strip=True))
            if not txt:
                continue
            # Heuristic: look for "Month Day" or date-like text or '@' time
            if re.search(rf'{MONTHS}\s+\d{{1,2}}', txt) or re.search(r'\d{1,2}/\d{1,2}/\d{4}', txt) or '@' in txt:
                items.append(txt)

        conn, cursor = self._connect()
        inserted = 0
        for line in items:
            iso_date = self._parse_date(line)
            time = self._parse_time(line)
            title = line
            location = ''  # not always present on the academic calendar
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
        Scrapes AbbeyAthletics calendar (abbeyathletics.com).
        Heuristics:
         - Finds event blocks (links and time strings).
         - Extracts date/time and event name.
        """
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')

        # The athletics calendar tends to place events in blocks; look for links and text lines
        candidate = soup.find('div', id='calendar') or soup.find('div', class_='calendar') or soup
        items = []

        # Collect anchor texts and sibling text lines
        for a in candidate.find_all('a', href=True):
            text = self._clean(a.get_text(" ", strip=True))
            if text:
                # if text looks like a time or contains digits/date, include
                if re.search(r'\d{1,2}:\d{2}', text) or re.search(r'\d{1,2}/\d{1,2}/\d{4}', text) or re.search(rf'{MONTHS}\s+\d{{1,2}}', text, re.I):
                    items.append((text, a.get('href')))
                else:
                    # sometimes name-only anchor; capture a bit more: parent text
                    parent_text = self._clean(a.parent.get_text(" ", strip=True))
                    if parent_text and (re.search(r'\d{1,2}:\d{2}', parent_text) or re.search(rf'{MONTHS}\s+\d{{1,2}}', parent_text, re.I)):
                        items.append((parent_text, a.get('href')))

        # If none found via anchors, fall back to scanning paragraphs
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

    def scrape_all(self, academic_url=None, athletics_url=None):
        """
        Convenience method to scrape both calendars.
        """
        if academic_url:
            self.scrape_academic_calendar(academic_url)
        else:
            self.scrape_academic_calendar()
        if athletics_url:
            self.scrape_athletics_calendar(athletics_url)
        else:
            self.scrape_athletics_calendar()
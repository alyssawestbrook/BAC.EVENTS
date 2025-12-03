# BAC.EVENTS

A Python based web scraping project that uses API to gather information about campus events, processes structured data, and displays results through a Flask web application.

## GitHub copilot helped to format README.md (2025-12)

## Real college event scraping  

Scraped my college’s public events webpage and created structured event data into a new table called `external_events`.

## Public API integration  

Chose a public API, stored the results in a table called `api_data`, and rendered the data on the `/api` webpage.

This project simulates real backend work: reading an already existing codebase, extending it, creating and adding new features, and managing an SQL database.

---

## Features Implemented

### **Backend Web Scraper Class**

- Requests HTML from my college events webpage  
- Uses BeautifulSoup to get titles, dates, descriptions, and locations  
- Cleans data using regex  
- Stores data in `external_events` table  

### **API Integration Class**

- Sends GET request to the public API
- Cleans and formats fields  
- Inserts data into the `api_data` table  

### **Updated Flask Routes**

- `/events` now shows both internal and the real external scraped events  
- `/api` now shows formatted API data  

### **Database Enhancements**

- Added `external_events` table  
- Added `api_data` table  
- Updated `seed_data.py` for testing  

---

## Technologies Used [Helped after initial write by GitHub Copilot to make sure specific technologies used weren't missed (2025-12)]

- **Python 3**
- **Flask**
- **SQLite3**
- **BeautifulSoup (bs4)**
- **Requests**
- **Regex**
- **HTML/Jinja Templates (not modified, only used)**

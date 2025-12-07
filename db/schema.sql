-- db/schema.sql
-- Keep existing starter SQL content if present. Append or replace the following blocks.

-- Table for scraped external events
CREATE TABLE IF NOT EXISTS external_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    date TEXT,           -- ISO date YYYY-MM-DD when possible
    time TEXT,           -- time or time range if available
    location TEXT,
    description TEXT,
    source TEXT,         -- which site it came from
    url TEXT             -- optional link to the original event page
);

-- Table for API/weather data (api_data)
CREATE TABLE IF NOT EXISTS api_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER,    -- optional FK to external_events.id (may be NULL)
    date TEXT,           -- ISO date the forecast applies to
    provider TEXT,       -- API provider (e.g., Open-Meteo)
    temp_max REAL,
    temp_min REAL,
    weather_code INTEGER,
    weather_text TEXT,
    raw_json TEXT,       -- store raw JSON (string) for debugging
    FOREIGN KEY(event_id) REFERENCES external_events(id)
);
ALTER TABLE external_events ADD COLUMN weather_forecast TEXT;
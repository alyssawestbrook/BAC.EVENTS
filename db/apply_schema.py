import sqlite3

# Apply schema to the database
conn = sqlite3.connect('db/campusconnect.db')
with open('db/schema.sql', 'r') as f:
    schema = f.read()
    conn.executescript(schema)
conn.commit()
conn.close()
print('Schema applied successfully!')

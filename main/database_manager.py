import sqlite3
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_name="network_events.db"):
        self.db_name = db_name
        self._create_table()

    def _create_table(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS network_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip_address TEXT NOT NULL,
            event_type TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
        """)

        conn.commit()
        conn.close()

    def log_event(self, ip_address, event_type):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("""
        INSERT INTO network_events (ip_address, event_type, timestamp)
        VALUES (?, ?, ?)
        """, (ip_address, event_type, timestamp))

        conn.commit()
        conn.close()

"""
DatabaseManager - Persistence Layer
Handles the local storage of security events using a SQLite database. 
This module provides a permanent audit trail of all detected network 
activities, including authorized logins and unauthorized intrusions.
"""

import sqlite3
from datetime import datetime


class DatabaseManager:
    def __init__(self, db_name="network_events.db"):
        """
        Initializes the database connection and ensures the schema exists.

        Args:
            db_name (str): The filename of the SQLite database.
        """
        self.db_name = db_name
        self._create_table()

    def _create_table(self):
        """
        Initializes the database schema if it has not been created yet.
        Defines the 'network_events' table structure.
        """
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        # The schema tracks unique IDs, IPs, the nature of the event, and the time.
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
        """
        Inserts a new security event record into the database.

        Args:
            ip_address (str): The IP address of the detected device.
            event_type (str): Description of the event (e.g., 'UNAUTHORIZED (ACTIVE)').
        """
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        # Generate a standardized ISO-8601-like timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("""
        INSERT INTO network_events (ip_address, event_type, timestamp)
        VALUES (?, ?, ?)
        """, (ip_address, event_type, timestamp))

        conn.commit()
        conn.close()

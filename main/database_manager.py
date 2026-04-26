"""
DatabaseManager - Persistence Layer
Handles the local storage of security events using a SQLite database. 
This module provides a permanent audit trail of all detected network 
activities, including authorized logins and unauthorized intrusions.
"""

import sqlite3
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_path="robot_gatekeeper.db"):
        try:
            # Ensure the attribute name is exactly 'self.conn'
            self.conn = sqlite3.connect(db_path, check_same_thread=False)
            self._create_table()
            print("[DB] Connected to database.")
        except Exception as e:
            print(f"[DB ERROR] Initialization failed: {e}")

    def _create_table(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS security_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                ip TEXT,
                description TEXT
            )
        ''')
        self.conn.commit()

    def log_event(self, ip, description):
        try:
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO security_events (ip, description) VALUES (?, ?)", (ip, description))
            self.conn.commit()
        except Exception as e:
            print(f"[DB ERROR] Failed to log event: {e}")

    def query_logs(self, limit=20):
        """Fetches latest events and sorts them so the newest is at the bottom."""
        try:
            cursor = self.conn.cursor()
            # We still grab the latest entries using DESC
            query = "SELECT timestamp, ip, description FROM security_events ORDER BY id DESC LIMIT ?"
            cursor.execute(query, (limit,))
            rows = cursor.fetchall()
            
            # Reversing the list: Newest goes from index [0] to the last index
            return rows[::-1] 
            
        except Exception as e:
            print(f"[DB ERROR] Query failed: {e}")
            return []

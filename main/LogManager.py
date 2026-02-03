
import datetime
import os

# --- CLASS 1: LOG MANAGER ---
# Handles Requirement: Accessing the File System
class LogManager:
    def __init__(self, filename="security_log.txt"):
        self.filename = filename
        # Create file if it doesn't exist
        if not os.path.exists(self.filename):
            with open(self.filename, "w") as f:
                f.write("Aegis-FTC Security Log Initialized\n")

    def log_event(self, message):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.filename, "a") as f:
            f.write(f"[{timestamp}] {message}\n")
        print(f"Log Updated: {message}")
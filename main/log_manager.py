"""
LogManager - Diagnostic & Security Logging
This module handles real-time text logging for the RobotGateKeeper system. 
It provides a sequential, human-readable record of system events, 
initialization statuses, and security alerts both to a local file and 
the standard console output.
"""

import datetime
import os


class LogManager:
    def __init__(self, filename):
        """
        Initializes the logging system and ensures the log file exists.

        Args:
            filename (str): The path to the text file where logs will be stored.
        """
        self.filename = filename

        # Ensure the log file exists to prevent append errors;
        # initialize with a header if creating a new file.
        if not os.path.exists(self.filename):
            with open(self.filename, "w", encoding="utf-8") as f:
                f.write("Aegis-FTC Security Log Initialized\n")
                f.write("-" * 40 + "\n")

    def log(self, message):
        """
        Records a timestamped message to the log file and prints it to the console.

        Args:
            message (str): The event description or alert to be recorded.
        """
        # Generate a high-precision timestamp for event sequencing
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Append the message to the file with UTF-8 encoding to support emojis or special chars
        with open(self.filename, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")

        # Echo the log to the terminal for real-time monitoring by the operator
        print(f"[LOG] {message}")

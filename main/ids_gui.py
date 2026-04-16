"""
SecurityGUI - The IDS Command Center
This module provides a real-time graphical user interface for the RobotGateKeeper.
It utilizes a multi-threaded approach to host a local secure socket server that
listens for encrypted alerts from the monitoring service (ids_engine) and displays them
with color-coded priority levels.
"""

import socket
import threading
import time
import tkinter as tk
from secure_socket import SecureSocket
from config import SECRET_KEY, SERVER_PORT


class IdsGUI:
    def __init__(self, root):
        """
        Initializes the GUI window, styling, and background server thread.

        Args:
            root (tk.Tk): The main Tkinter root window instance.
        """
        self.root = root
        self.root.title("Aegis-FTC Command Center")

        # --- UI Component Setup ---
        tk.Label(self.root, text="LIVE NETWORK MONITOR",
                 font=("Arial", 16, "bold")).pack(pady=5)

        # Terminal-style display for security logs
        self.monitor_log = tk.Text(
            self.root, height=15, width=70,
            state='disabled', bg="black", fg="white",
            font=("Consolas", 10)
        )
        self.monitor_log.pack(padx=10, pady=10)

        # --- Visual Priority Tags ---
        # Defines how specific text types appear in the log (Color Coding)
        self.monitor_log.tag_config(
            "ACTIVE", foreground="lime")        # Safe/Verified
        self.monitor_log.tag_config(
            "STALE", foreground="orange")      # Re-connecting
        self.monitor_log.tag_config(
            "UNAUTH", foreground="red", font=("Consolas", 10, "bold"))  # ALERT

    

    def update_status(self, robot_id="SYSTEM", text=None): 
        """
        Thread-safe method to update the text display.
        Handles both background timer calls and real server alerts.
        """
        # 1. Handle the "NoneType" error immediately
        if text is None:
            # If text is None, this is likely a background heartbeat/timer call.
            # We just return and do nothing so we don't spam the GUI or crash.
            return 

        try:
            self.monitor_log.config(state='normal')
            
            timestamp = time.strftime('%H:%M:%S')
            
            # Use strip() safely on both inputs
            clean_id = str(robot_id).strip()
            clean_text = str(text).strip()
            
            full_message = f"[{timestamp}] {clean_id} | {clean_text}\n"

            # 2. Logical Tagging (Safe check for upper())
            tag = None
            upper_text = clean_text.upper()
            if "UNAUTHORIZED" in upper_text:
                tag = "UNAUTH"
            elif any(x in upper_text for x in ["CONNECTED", "ACTIVE"]):
                tag = "ACTIVE"
            elif any(x in upper_text for x in ["STALE", "DISCONNECTED", "LOST"]):
                tag = "STALE"

            self.monitor_log.insert(tk.END, full_message, tag)
            self.monitor_log.see(tk.END)
            self.monitor_log.config(state='disabled')
            
        except Exception as e:
            print(f"[GUI ERROR] Failed to display message: {e}")
            # Ensure we don't leave the log widget locked if we crash
            self.monitor_log.config(state='disabled')




# --- Application Entry Point ---
if __name__ == "__main__":
    root = tk.Tk()
    app = IdsGUI(root)

    # MainLoop keeps the window open and processes the .after() queue
    root.mainloop()

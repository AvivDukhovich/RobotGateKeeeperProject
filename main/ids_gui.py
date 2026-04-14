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

        # Start the listener thread so the UI remains responsive while waiting for data
        self.start_network_thread()

    def update_status(self, text):
        """
        Thread-safe method to update the text display with new alerts.

        Args:
            text (str): The decrypted message received from the monitor service.
        """
        self.monitor_log.config(
            state='normal')  # Temporarily enable for writing
        timestamp = time.strftime('%H:%M:%S')
        full_message = f"[{timestamp}] {text}\n"

        # Logical Tagging: Assign colors based on message content
        tag = None
        if "UNAUTHORIZED" in text:
            tag = "UNAUTH"
        elif "[ACTIVE]" in text:
            tag = "ACTIVE"
        elif "[STALE]" in text:
            tag = "STALE"

        # Insert at the end of the log and auto-scroll
        self.monitor_log.insert(tk.END, full_message, tag)
        self.monitor_log.see(tk.END)
        self.monitor_log.config(state='disabled')  # Set back to read-only

    def start_network_thread(self):
        """
        Spawns a background daemon thread to run the socket server.
        Ensures the UI doesn't 'freeze' while the program waits for network data.
        """
        # Requirement: Concurrency (Multi-threading)
        # daemon=True ensures the thread closes immediately when the GUI window is shut
        net_thread = threading.Thread(target=self.run_server, daemon=True)
        net_thread.start()

    def run_server(self):
        """
        Hosts the local IPC (Inter-Process Communication) server.
        Listens for, decrypts, and routes incoming security alerts to the UI.
        """

        # Initialize the same encryption engine used by the monitor
        sec = SecureSocket(key=SECRET_KEY)
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Allow immediate re-binding of the port if the app restarts
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            # Bind to '0.0.0.0' to accept alerts from other laptops on the network
            server.bind(('0.0.0.0', SERVER_PORT))
            server.listen(5)
            print(f"[*] Command Center Active. Listening for remote sensors...")
        except Exception as e:
            print(f"Bind Error: {e}")
            return

        while True:
            try:
                # Accept incoming alert from the background monitor script
                client, addr = server.accept()
                data = client.recv(4096)
                if data:
                    # Decrypt the sensitive payload
                    message = sec.decrypt_message(data)

                    # THREAD SAFETY: Use .after() to schedule UI updates on the main thread.
                    # Tkinter is not thread-safe; you cannot update the UI directly from run_server.
                    self.root.after(0, self.update_status, message)
                client.close()
            except Exception as e:
                print(f"Dashboard Server Loop Error: {e}")


# --- Application Entry Point ---
if __name__ == "__main__":
    root = tk.Tk()
    app = IdsGUI(root)

    # MainLoop keeps the window open and processes the .after() queue
    root.mainloop()

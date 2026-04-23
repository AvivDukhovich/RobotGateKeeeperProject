"""
RobotGateKeeper - Main Execution Module
This script orchestrates the IDS engine, the network server, and the GUI.
It allows the system to operate as either a Master Command Center (ROBOT_1)
or a Secondary Remote Sensor (ROBOT_2+) based on the config.
"""

import signal
import tkinter as tk
from command_center_server import CommandCenterServer
from ids_engine import IDSEngine
from ids_gui import IdsGUI
from database_manager import DatabaseManager
from log_manager import LogManager
from notification_manager import NotificationManager
from config import LOG_FILE, ROBOT_ID


def main():
    # --- 1. Initialize Managers ---
    db = DatabaseManager()
    logger = LogManager(LOG_FILE)
    notifier = NotificationManager("Farminator_protector")

    # --- 2. Start Local IDS Engine ---
    engine = IDSEngine("usb")
    engine.start_monitoring()

    # --- 3. GUI Setup ---
    root = tk.Tk()
    gui = IdsGUI(root)

    # --- 4. Shutdown Logic ---
    def on_closing():
        print(f"[*] Shutting down {ROBOT_ID}...")

        # Only stop server if it was actually created (Master only)
        if ROBOT_ID == "ROBOT_1":
            server.running = False

        engine.stop()
        root.after(100, root.destroy)

    # Register shutdown handlers
    root.protocol("WM_DELETE_WINDOW", on_closing)
    signal.signal(signal.SIGINT, lambda s, f: on_closing())

    # --- 5. Master vs Secondary Logic ---
    # --- 5. Master vs Secondary Logic ---
    if ROBOT_ID == "ROBOT_1":
        print("[*] Starting Master Command Center Server...")

        # CHANGE: Pass the 'gui' object directly, not a callback.
        # The order must match: (gui, db, logger, notifier)
        server = CommandCenterServer(gui, db, logger, notifier)
        server.start()

        # Add a safe reference to the server for shutdown logic
        server_instance = server
    else:
        print(
            f"[*] Secondary Node ({ROBOT_ID}) - Hiding GUI and skipping Server.")
        root.withdraw()
        server_instance = None  # No server on secondary nodes
        # --- 6. Main Loop ---
    try:
        root.mainloop()
    except KeyboardInterrupt:
        on_closing()


if __name__ == "__main__":
    main()

"""
RobotGateKeeper - Main Execution Module
This script orchestrates the IDS engine, the network server, and the GUI.
It allows the system to operate as either a Master Command Center (ROBOT_1)
or a Secondary Remote Sensor (ROBOT_2+) based on the config.
"""
import signal
import threading
import tkinter as tk
import time
from command_center_server import CommandCenterServer
from ids_engine import IDSEngine
from ids_gui import IdsGUI
from database_manager import DatabaseManager
from log_manager import LogManager
from notification_manager import NotificationManager
from config import LOG_FILE, ROBOT_ID, CONNECTION_MODE

def main():
    # --- 1. Initialize Managers ---
    db = DatabaseManager()
    logger = LogManager(LOG_FILE)
    notifier = NotificationManager("Farminator_protector")

    # --- 2. GUI Setup ---
    # Initialize the GUI first so the server has a valid object to talk to
    root = tk.Tk()
    gui = IdsGUI(root)

    # Variables for shutdown scope
    server = None
    engine = IDSEngine(CONNECTION_MODE)

    # --- 3. Shutdown Logic ---
    def on_closing():
        nonlocal server
        print(f"\n[*] Shutting down {ROBOT_ID}...")
        if server:
            server.running = False
        engine.stop()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    signal.signal(signal.SIGINT, lambda s, f: on_closing())

    # --- 4. Master vs Secondary Logic ---
    if ROBOT_ID == "ROBOT_1":
        print("[*] Starting Master Command Center Server...")
        server = CommandCenterServer(gui, db, logger, notifier)
        server.start() 
        time.sleep(1) 
    else:
        root.withdraw()

    # --- 5. Start Local IDS Engine ---
    # Wrap this in a thread so the GUI mainloop can actually start!
    threading.Thread(target=engine.start_monitoring, daemon=True).start()

    # --- 6. Main Loop ---
    print(f"[*] {ROBOT_ID} System Ready. GUI Launching...")
    root.mainloop()

if __name__ == "__main__":
    main()
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
    # --- 1. Master-Only Initialization ---
    server = None
    gui = None
    root = None

    if ROBOT_ID == "ROBOT_1":
        # Only ROBOT_1 needs the DB, Logger, and GUI components
        db = DatabaseManager()
        logger = LogManager(LOG_FILE)
        notifier = NotificationManager("Farminator_protector")
        
        root = tk.Tk()
        gui = IdsGUI(root)
        
        print("[*] Starting Master Command Center Server...")
        server = CommandCenterServer(gui, db, logger, notifier)
        gui.set_server_reference(server) # Link server to GUI for history fetching
        server.start()
        time.sleep(1)
    else:
        # ROBOT_2+ (Sensor Mode) doesn't need a GUI or local DB
        print(f"[*] Initializing {ROBOT_ID} in SENSOR MODE (Headless)...")
        notifier = None # Or initialize if you want PC 2 to send its own push alerts

    # --- 2. Initialize IDS Engine ---
    # The engine is common to both, but ROBOT_2 will send data to ROBOT_1's IP
    engine = IDSEngine(CONNECTION_MODE)

    # --- 3. Shutdown Logic ---
    def on_closing():
        print(f"\n[*] Shutting down {ROBOT_ID}...")
        engine.stop()
        if server:
            server.running = False
        if root:
            root.destroy()
        exit(0)

    # Handle OS signals (Ctrl+C)
    signal.signal(signal.SIGINT, lambda s, f: on_closing())

    # --- 4. Start Local IDS Engine ---
    # We run this in a thread so it doesn't block the GUI on Master
    # or the script execution on Sensor nodes
    threading.Thread(target=engine.start_monitoring, daemon=True).start()

    # --- 5. Execution Loop ---
    if ROBOT_ID == "ROBOT_1":
        print(f"[*] {ROBOT_ID} Master System Ready. GUI Launching...")
        root.protocol("WM_DELETE_WINDOW", on_closing)
        root.mainloop()
    else:
        print(f"[*] {ROBOT_ID} Sensor Node Active. Monitoring hardware...")
        # Keep the script alive since there is no GUI loop
        while True:
            time.sleep(1)

if __name__ == "__main__":
    main()
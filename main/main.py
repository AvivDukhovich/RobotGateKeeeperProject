import sys
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
    # Initialize Managers
    db = DatabaseManager()
    logger = LogManager(LOG_FILE)
    notifier = NotificationManager("Farminator_protector")

    # Start the Local IDS Engine
    engine = IDSEngine("usb") 
    engine.start_monitoring()

    # Initialize the Tkinter Root and the GUI
    root = tk.Tk()  
    gui = IdsGUI(root)

    # --- SHUTDOWN LOGIC (Defined inside main to access variables) ---
    def on_closing():
        print(f"[*] Shutting down {ROBOT_ID}...")
        
        # Only stop server if it was actually created
        if ROBOT_ID == "ROBOT_1":
            server.running = False  
        
        engine.stop()           
        root.after(100, root.destroy)

    # Register the shutdown handlers BEFORE starting loops
    root.protocol("WM_DELETE_WINDOW", on_closing)
    signal.signal(signal.SIGINT, lambda s, f: on_closing())

    # --- MASTER vs SECONDARY LOGIC ---
    if ROBOT_ID == "ROBOT_1":
        print("[*] Starting Master Command Center Server...")
        server = CommandCenterServer(db, logger, notifier, gui_callback=gui.update_status)
        server.start()
    else:
        print(f"[*] Secondary Node ({ROBOT_ID}) - Hiding GUI and skipping Server.")
        # HIDE THE WINDOW but keep the process alive
        root.withdraw() 

    # --- RUN LOOP ---
    try:
        root.mainloop() 
    except KeyboardInterrupt:
        on_closing()

if __name__ == "__main__":
    main()
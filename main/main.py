import sys
import signal
import tkinter as tk
from command_center_server import CommandCenterServer
from ids_engine import IDSEngine
from ids_gui import IdsGUI
from database_manager import DatabaseManager
from log_manager import LogManager
from notification_manager import NotificationManager
from config import LOG_FILE

def main():
    # 1. Initialize Managers
    db = DatabaseManager()
    logger = LogManager(LOG_FILE)
    notifier = NotificationManager("Farminator_protector")

    # 4. Start the Local IDS Engine
    engine = IDSEngine("usb") # You can change to "wifi" if needed
    engine.start_monitoring()


    # 2. Initialize the Tkinter Root and the GUI
    root = tk.Tk()  # Create the actual window object
    gui = IdsGUI(root) # Pass the root to your class

    # 3. Start the Central Server
    # Note: We use gui.update_status (or whatever your method name is)
    server = CommandCenterServer(db, logger, notifier, gui_callback=gui.update_status)
    server.start()

    

    # 5. Run GUI Loop
    root.mainloop() # Using the standard Tkinter loop

    def on_closing():
        print("[*] Shutting down RobotGateKeeper...")
        
        # 1. Stop the background logic first
        server.running = False  # Tells the listener loop to stop
        engine.stop()           # (Assuming you have a stop method in IDSEngine)
        
        # 2. Wait a tiny bit for threads to notice
        root.after(100, root.destroy)

        # This handles clicking the "X" button on the window
        root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # This handles Ctrl+C in the terminal
    signal.signal(signal.SIGINT, lambda s, f: on_closing())

    try:
        root.mainloop()
    except KeyboardInterrupt:
        on_closing()

if __name__ == "__main__":
    main()
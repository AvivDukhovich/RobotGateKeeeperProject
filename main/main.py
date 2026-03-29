import time
import keyboard
import socket
from log_manager import LogManager
from NetworkMonitor import NetworkMonitor
from database_manager import DatabaseManager
from SecureSocket import SecureSocket
from config import LOG_FILE, SECRET_KEY, SERVER_PORT
from notification_manager import NotificationManager

ALLOWED_IPS = {"192.168.43.104"}

def send_alert_to_gui(message):
    sec = SecureSocket(key=SECRET_KEY)
    encrypted = sec.encrypt_message(message)
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(2) # Don't wait forever
        s.connect(('127.0.0.1', SERVER_PORT))
        s.sendall(encrypted)

def main():
    logger = LogManager(LOG_FILE)
    monitor = NetworkMonitor()
    db = DatabaseManager()

    notifier = NotificationManager("Farminator_protector")

    if not monitor.connect_to_hub():
        logger.log("FAILED to connect to REV Control Hub")
        return

    logger.log("Successfully connected. Monitoring Active. Press 'S' to stop.")
    known_devices = set()

    # Flag to control the outer loop
    running = True

    while running:
        # 1. Check for 'S' BEFORE scanning
        if keyboard.is_pressed('s'):
            logger.log("Shutdown initiated...")
            break

        # 2. Perform the network scan
        devices = monitor.get_connected_devices() # Now returns [(ip, status), ...]
        
        for ip, net_status in devices:
            # We want to log if it's a NEW device OR if an old device changed status
            device_key = f"{ip}_{net_status}" 
            
            if device_key not in known_devices:
                known_devices.add(device_key)
                
                auth_status = "AUTHORIZED" if ip in ALLOWED_IPS else "UNAUTHORIZED"
                
                # Create a detailed message for the GUI
                # Example: "[ACTIVE] AUTHORIZED device detected: 192.168.43.104"
                alert_msg = f"[{net_status}] {auth_status}: {ip}"

                if auth_status == "UNAUTHORIZED":
                    notifier.send_alert(alert_msg)
                
                logger.log(alert_msg)
                db.log_event(ip, f"{auth_status} ({net_status})")
                send_alert_to_gui(alert_msg)

        # 3. RESPONSIVE SLEEP: Instead of time.sleep(5)
        # We wait for 5 seconds total, but check for 'S' every 0.1 seconds
        for _ in range(50): 
            if keyboard.is_pressed('s'):
                logger.log("Shutdown initiated during wait...")
                running = False # Tell the outer loop to stop
                break # Exit the 50-step wait loop
            time.sleep(0.1) 

    print("Program exited successfully")

if __name__ == "__main__":
    main()
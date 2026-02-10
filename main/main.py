import time
from log_manager import LogManager
from network_monitor import NetworkMonitor
from database_manager import DatabaseManager
from config import LOG_FILE

def main():
    logger = LogManager(LOG_FILE)
    monitor = NetworkMonitor()
    db = DatabaseManager()

    if not monitor.connect_to_hub():
        logger.log("FAILED to connect to REV Control Hub")
        return

    logger.log("Successfully connected to REV Control Hub")

    # Track devices we've already seen
    known_devices = set()

    logger.log("Starting continuous network monitoring...")

    while True:
        devices = monitor.get_connected_devices()
        print("SCAN RESULT:", devices)

        for ip in devices:
            if ip not in known_devices:
                known_devices.add(ip)
                logger.log(f"New device connected: {ip}")
                db.log_event(ip, "CONNECTED")

        time.sleep(5)  # scan every 5 seconds

if __name__ == "__main__":
    main()

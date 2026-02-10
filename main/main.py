import time
from log_manager import LogManager
from network_monitor import NetworkMonitor
from database_manager import DatabaseManager
from config import LOG_FILE

ALLOWED_IPS = {
    "192.168.43.10",  # Programming laptop
    "192.168.43.1",   # Control Hub itself
}


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

                if ip in ALLOWED_IPS:
                    logger.log(f"✅ Authorized device connected: {ip}")
                    db.log_event(ip, "AUTHORIZED")
                else:
                    logger.log(f"🚨 WARNING! UNKNOWN DEVICE DETECTED: {ip}")
                    db.log_event(ip, "UNAUTHORIZED")

        time.sleep(5)


if __name__ == "__main__":
    main()

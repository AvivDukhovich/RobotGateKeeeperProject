# --- MAIN EXECUTION (The Prototype Test) ---
from LogManager import LogManager
from NetworkMonitor import NetworkMonitor

if __name__ == "__main__":
    logger = LogManager()
    monitor = NetworkMonitor()

    if monitor.connect_to_hub():
        logger.log_event("Successfully connected to REV Control Hub.")

        print("Scanning for devices on the Hub's network...")
        devices = monitor.get_connected_devices()

        if devices:
            for ip in devices:
                logger.log_event(f"Detected device on network: {ip}")
        else:
            print("No other devices found on the Hub Wi-Fi.")
    else:
        logger.log_event("FAILED to connect to Hub. Is Wi-Fi on?")
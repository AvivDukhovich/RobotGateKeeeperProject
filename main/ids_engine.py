"""
RobotGateKeeper - Main Monitoring Service

This script acts as a real-time Intrusion Detection System (IDS) for the 
REV Control Hub. It monitors connected devices via ADB, cross-references 
them against a whitelist, and alerts the user of unauthorized connections 
via encrypted sockets, local logs, and app notifications.
"""

import time
import socket
from log_manager import LogManager
from network_monitor import NetworkMonitor
from database_manager import DatabaseManager
from secure_socket import SecureSocket
from config import LOG_FILE, SECRET_KEY, SERVER_PORT, HUB_IP, COMMAND_CENTER_IP, ROBOT_ID
from notification_manager import NotificationManager

# Devices allowed on the Robot Network (Admin Laptop and the Hub itself)
ALLOWED_IPS = {"192.168.43.104", HUB_IP}


def send_alert_to_gui(message):
    """
    Encrypts and transmits security alerts to the remote Command Center.
    """

    try:
        # 1. Prefix the message with the ID: "SENSOR_NAME | ACTUAL_MESSAGE"
        tagged_message = f"{ROBOT_ID} | {message}"

        sec = SecureSocket(key=SECRET_KEY)
        encrypted = sec.encrypt_message(tagged_message)

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(2)
            # 2. Connect to the Command Center IP instead of 127.0.0.1
            s.connect((COMMAND_CENTER_IP, SERVER_PORT))
            s.sendall(encrypted)

    except (ConnectionRefusedError, socket.timeout):
        pass
    except Exception as e:
        print(f"Error communicating with Command Center: {e}")


def main():
    """
    Main execution loop.
    Handles initialization, real-time scanning, and state management.
    """
    # Initialize Core Management Components
    logger = LogManager(LOG_FILE)
    monitor = NetworkMonitor()
    db = DatabaseManager()
    notifier = NotificationManager("Farminator_protector")

    # Establish initial ADB connection to the REV Control Hub
    if not monitor.connect_to_hub():
        logger.log(
            "CRITICAL: FAILED to connect to REV Control Hub. Check Wi-Fi/ADB Path.")
        return

    logger.log(
        "Aegis Shield Active. Monitoring Robot Subnet. Press 'S' to Terminate.")

    # Track the current state of devices to manage 'New Connection' alerts
    # Stores identifiers in the format: "IP_STATUS" (e.g., "192.168.43.107_ACTIVE")
    known_devices = set()
    running = True

    while running:

        # 1. Fetch live network neighbors using NUD (Neighbor Unreachability Detection)
        # Returns a list of tuples: [(ip, status), ...]
        devices = monitor.get_connected_devices()

        # Temporary set to track current scan results for ghost-cleanup
        current_scan_keys = set()

        for ip, net_status in devices:
            device_key = f"{ip}_{net_status}"
            current_scan_keys.add(device_key)

            # 2. Logic for New Device Detection or Status Changes
            if device_key not in known_devices:
                known_devices.add(device_key)

                # Check against the authorized whitelist
                auth_status = "AUTHORIZED" if ip in ALLOWED_IPS else "UNAUTHORIZED"
                alert_msg = f"[{net_status}] {auth_status}: {ip}"

                # 3. Defensive Response Actions
                if auth_status == "UNAUTHORIZED":
                    # Windows Desktop Notification
                    notifier.send_alert(alert_msg, PC_ID)

                logger.log(alert_msg)              # Write to text log
                # Update SQL/Database
                db.log_event(ip, f"{auth_status} ({net_status})")
                # Send encrypted update to GUI
                send_alert_to_gui(alert_msg)

        # 4. State Management: Flush devices no longer present in the scan
        # This prevents 'ghost' devices from staying in the 'known' set indefinitely
        known_devices = {k for k in known_devices if k in current_scan_keys}

        time.sleep(2)

    print("GateKeeper Service Terminated Successfully.")


if __name__ == "__main__":
    main()

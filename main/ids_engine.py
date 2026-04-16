"""
IDSEngine - Local Hardware Monitoring & Intrusion Detection
This module acts as the "eyes" of the system. It continuously polls the 
REV Control Hub for active network connections, compares them against 
a whitelist (ALLOWED_IPS), and reports state changes to the Command Center.

Detection Logic:
- New Connection: Occurs when an IP appears in the Hub's table that wasn't there previously.
- Device Lost: Occurs when a previously tracked IP disappears from the Hub's table.
- Authorization: Checks every new IP against the config.py whitelist.
"""

import time
import socket
import threading
from network_monitor import NetworkMonitor
from secure_socket import SecureSocket
from config import SECRET_KEY, SERVER_PORT, COMMAND_CENTER_IP, ROBOT_ID, ALLOWED_IPS

class IDSEngine:
    def __init__(self, mode="usb"):
        """
        Initializes the monitoring engine.
        
        Args:
            mode (str): The connection method to the Hub ('usb' or 'wifi').
        """
        self.monitor = NetworkMonitor(mode=mode)
        self.mode = mode
        self.sec = SecureSocket(key=SECRET_KEY)
        self.known_devices = set()
        self.running = True

    def start_monitoring(self):
        """
        Establishes a connection to the Hub hardware and launches the 
        background polling thread.
        """
        if self.monitor.connect_to_hub():
            print(f"[*] IDS Engine started via {self.mode.upper()} for {ROBOT_ID}")
            threading.Thread(target=self._loop, daemon=True).start()
        else:
            print(f"[!] IDS failed to connect to Hub via {self.mode.upper()}")

    def _loop(self):
        """
        Internal background loop that polls the Hub for device status.
        Uses set-difference logic to detect connection/disconnection events.
        """
        # Tracks the state of the network from the previous poll
        last_active_devices = set() 

        while self.running:
            try:
                # 1. Query the Hub for currently connected IP addresses
                current_devices = self.monitor.get_connected_devices()
                current_ips = {ip for ip, status in current_devices}
                
                # 2. Detect DISCONNECTS (IP was present in last_active but is now gone)
                for ip in last_active_devices:
                    if ip not in current_ips:
                        print(f"[!] DEVICE LOST: {ip}")
                        self._report(f"DISCONNECTED: {ip}")
                
                # 3. Detect NEW CONNECTIONS (IP is present now but wasn't in last_active)
                for ip in current_ips:
                    if ip not in last_active_devices:
                        is_auth = ip in ALLOWED_IPS
                        status_str = "AUTHORIZED" if is_auth else "UNAUTHORIZED"
                        print(f"[*] NEW DEVICE: {ip} ({status_str})")
                        self._report(f"CONNECTED: {ip} ({status_str})")

                # 4. Synchronize state for the next polling cycle
                last_active_devices = current_ips

                time.sleep(2) # Interval between scans
                
            except Exception as e:
                print(f"[ERROR] Engine Loop Error: {e}")
                time.sleep(2)

    def _report(self, message):
        """
        Encrypts and sends a security alert to the Command Center Server.
        
        Args:
            message (str): The status update to be transmitted.
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(2)
                # Connect to the Master PC defined in config.py
                s.connect((COMMAND_CENTER_IP, SERVER_PORT))
                
                # Fetch target info for logging/verification
                actual_target = s.getpeername()

                # Package as "ROBOT_NAME | MESSAGE" for server parsing
                payload = f"{ROBOT_ID} | {message}"
                
                # Encrypt the payload before sending it over the wire
                s.sendall(self.sec.encrypt_message(payload))
                print(f"[SUCCESS] Alert sent: {message}")
        except Exception as e:
            print(f"[ENGINE ERROR] Connection failed: {e}")

    def stop(self):
        """Gracefully terminates the background polling loop."""
        print(f"[*] Stopping IDS Engine loop...")
        self.running = False
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
        
    def wait_for_hub(self):
        """Infinite loop that blocks until the Control Hub is found."""
        print(f"[*] {ROBOT_ID}: Waiting for Control Hub link...")
        while self.running:
            try:
                self.monitor.get_connected_devices()
                handshake_msg = "Control Hub Connected"
                print(f"[SUCCESS] {ROBOT_ID}: {handshake_msg}")
                self._report(handshake_msg)
                return True # Exit the wait loop and start monitoring
            except Exception:
                time.sleep(2)
        return False

    def _loop(self):
        """Background loop: Only reports NEW unauthorized connections."""
        # We still track last_active_devices so we know what is "New" vs "Already There"
        last_active_devices = set() 
        
        while self.running:
            try:
                current_devices = self.monitor.get_connected_devices()
                
                # Link Check: If ADB fails, crash the loop to trigger the 'Link Lost' logic
                if current_devices is None: 
                    raise ConnectionError("Lost contact with Control Hub")

                current_ips = {ip for ip, status in current_devices}
                
                # --- 1. DISCONNECTS: IGNORED ---
                # We no longer loop through last_active_devices to find missing IPs.
                # This silences ALL "Device Lost" or "Disconnected" alerts.

                # --- 2. NEW CONNECTIONS: FILTERED ---
                for ip in current_ips:
                    # ONLY report if it's a NEW sighting AND not on the whitelist
                    if ip not in last_active_devices and ip not in ALLOWED_IPS:
                        self._report(f"CONNECTED: {ip} (UNAUTHORIZED)")
                        print(f"[!] INTRUDER ALERT: {ip}")

                # Update the state for the next scan
                last_active_devices = current_ips
                time.sleep(2)

            except Exception as e:
                # This still allows the PC to report when the USB cable is pulled
                raise e

    def start_monitoring(self):
        """The Supervisor: Now documents disconnections in the DB/Logs."""
        # Track if we were previously connected so we don't spam 'Link Lost' 
        # while we are already searching.
        was_connected = False 

        while self.running:
            try:
                # 1. SEARCHING
                print(f"[*] {ROBOT_ID} IDS Engine: Searching for Hub...", end='\r')
                self.monitor.get_connected_devices()
                
                # 2. HANDSHAKE (Only on fresh connection)
                msg = "Control Hub Connected"
                print(f"\n[SUCCESS] {ROBOT_ID}: {msg}")
                self._report(msg)
                
                was_connected = True # Set the flag
                
                # 3. MONITORING (Blocks here)
                self._loop() 

            except Exception as e:
                # 4. DISCONNECT REPORTING
                if was_connected:
                    # This is the line that documents it in your Logs and DB!
                    disconnect_msg = "CRITICAL: Physical Link Lost (USB/ADB Disconnected)"
                    self._report(disconnect_msg)
                    was_connected = False # Reset flag so we don't spam the server
                
                print(f"\n[!] {ROBOT_ID}: Link lost. Cleaning up and retrying...")
                time.sleep(3)

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
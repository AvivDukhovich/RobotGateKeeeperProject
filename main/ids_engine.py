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
        print(f"[*] {ROBOT_ID}: Searching for Control Hub...")
        while self.running:
            devices = self.monitor.get_connected_devices()
            
            # devices is None if ADB failed or timed out
            # devices is [] if ADB worked but no one is on the network
            if devices is not None:
                # We only print success ONCE and then exit the loop
                print(f"[SUCCESS] {ROBOT_ID}: Control Hub Connected.")
                
                # Try to tell PC 1. If this fails, we catch it inside _report
                self._report("Control Hub Connected")
                return True 
            
            time.sleep(2)
        return False
            
        return False

    def _loop(self):
        last_active_devices = set() 
        while self.running:
            try:
                current_devices = self.monitor.get_connected_devices()
                
                if current_devices is None:
                    # ADB timed out - wait 5 seconds and try again
                    print("[!] Hardware busy. Pausing...")
                    time.sleep(5)
                    continue

                current_ips = {ip for ip, status in current_devices}
                
                for ip in current_ips:
                    # Intruder detection logic
                    if ip not in last_active_devices and ip not in ALLOWED_IPS:
                        print(f"[!] INTRUDER ALERT: {ip}")
                        self._report(f"INTRUDER: {ip}")

                last_active_devices = current_ips
                
                # SLEEP LONGER: 5 seconds gives the Hub's CPU a break
                time.sleep(5) 

            except Exception as e:
                print(f"[LOOP ERROR] {e}")
                raise e # Triggers 'Link Lost' logic in start_monitoring

    def start_monitoring(self):
        """The Supervisor: Validates connection before entering the monitor loop."""
        was_connected = False 

        while self.running:
            try:
                # 1. SEARCHING - Now actually checking the return value
                print(f"[*] {ROBOT_ID} IDS Engine: Searching for Hub...", end='\r')
                devices = self.monitor.get_connected_devices()
                
                # If it's None, ADB failed/timed out. Do NOT proceed.
                if devices is None:
                    time.sleep(2)
                    continue

                # 2. HANDSHAKE (Only on fresh connection)
                if not was_connected:
                    msg = "Control Hub Connected"
                    print(f"\n[SUCCESS] {ROBOT_ID}: {msg}")
                    self._report(msg)
                    was_connected = True
                
                # 3. MONITORING (Blocks here)
                # Pass the initial 'devices' to _loop so it doesn't have to poll again immediately
                self._loop() 

            except Exception as e:
                # 4. DISCONNECT REPORTING
                if was_connected:
                    disconnect_msg = "CRITICAL: Physical Link Lost (USB/ADB Disconnected)"
                    print(f"\n[!] {ROBOT_ID}: {disconnect_msg}")
                    self._report(disconnect_msg)
                    was_connected = False
                
                time.sleep(3)

    def get_local_ip(self):
        """Helper to grab the actual network IP, not 127.0.0.1"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                # We use a public IP to 'probe' which interface is active
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except Exception:
            return "Unknown-IP"

    def _report(self, message):
        """Encrypted reporting with True IP detection."""
        # 1. Prepare the payload ONCE
        real_ip = self.get_local_ip()
        payload = f"{ROBOT_ID} | IP:{real_ip} | {message}"

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(5.0) 
                
                # Connect to the Master Command Center
                s.connect((COMMAND_CENTER_IP, SERVER_PORT))
                
                # 2. Send the ALREADY PREPARED payload (don't overwrite it!)
                encrypted_data = self.sec.encrypt_message(payload)
                s.sendall(encrypted_data)
                
                print(f"[SUCCESS] Alert sent (via {real_ip}): {message}")
                
        except Exception as e:
            # We print the error but keep the engine running
            print(f"[ENGINE ERROR] Reporting failed: {e}")

    def stop(self):
        """Gracefully terminates the background polling loop."""
        print(f"[*] Stopping {ROBOT_ID} IDS Engine loop...")
        self.running = False
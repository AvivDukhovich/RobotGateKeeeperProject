import time
import socket
import threading
from network_monitor import NetworkMonitor
from secure_socket import SecureSocket
from config import SECRET_KEY, SERVER_PORT, COMMAND_CENTER_IP, ROBOT_ID, ALLOWED_IPS

class IDSEngine:
    def __init__(self, mode="usb"):
        self.monitor = NetworkMonitor(mode=mode)
        self.mode = mode
        self.sec = SecureSocket(key=SECRET_KEY)
        self.known_devices = set()
        self.running = True

    def start_monitoring(self):
        if self.monitor.connect_to_hub():
            print(f"[*] IDS Engine started via {self.mode.upper()} for {ROBOT_ID}")
            threading.Thread(target=self._loop, daemon=True).start()
        else:
            print(f"[!] IDS failed to connect to Hub via {self.mode.upper()}")

    def _loop(self):
        # We'll use a dictionary to track currently active IPs
        last_active_devices = set() 

        while self.running:
            try:
                # 1. Get current active devices from the Hub
                current_devices = self.monitor.get_connected_devices()
                current_ips = {ip for ip, status in current_devices}
                
                # 2. Detect DISCONNECTS (Were there before, but not now)
                for ip in last_active_devices:
                    if ip not in current_ips:
                        print(f"[!] DEVICE LOST: {ip}")
                        self._report(f"DISCONNECTED: {ip}")
                
                # 3. Detect NEW CONNECTIONS
                for ip in current_ips:
                    if ip not in last_active_devices:
                        is_auth = ip in ALLOWED_IPS
                        status_str = "AUTHORIZED" if is_auth else "UNAUTHORIZED"
                        print(f"[*] NEW DEVICE: {ip} ({status_str})")
                        self._report(f"CONNECTED: {ip} ({status_str})")

                # 4. Update the tracker for the next cycle
                last_active_devices = current_ips

                time.sleep(2) # Poll every 2 seconds (adjust as needed)
                
            except Exception as e:
                print(f"[ERROR] Engine Loop Error: {e}")
            
            time.sleep(2)

    def _report(self, message):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(2)
                s.connect((COMMAND_CENTER_IP, SERVER_PORT))
                
                # --- ADD THIS LINE ---
                actual_target = s.getpeername()
                # ---------------------

                payload = f"{ROBOT_ID} | {message}"
                s.sendall(self.sec.encrypt_message(payload))
                print(f"[SUCCESS] Alert sent: {message}")
        except Exception as e:
            print(f"[ENGINE ERROR] Connection failed: {e}")


    def stop(self):
            """Stops the background polling loop."""
            print(f"[*] Stopping IDS Engine loop...")
            self.running = False
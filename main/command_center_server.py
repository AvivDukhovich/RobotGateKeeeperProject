import socket
import threading
from secure_socket import SecureSocket
from config import SECRET_KEY, SERVER_PORT

class CommandCenterServer:
    def __init__(self, db_manager, log_manager, notification_manager, gui_callback=None):
        self.sec = SecureSocket(key=SECRET_KEY)
        self.db = db_manager
        self.logger = log_manager
        self.notifier = notification_manager
        self.gui_callback = gui_callback
        self.running = True

    def start(self):
        # Initial thread to listen for incoming connections
        thread = threading.Thread(target=self._run_listener, daemon=True)
        thread.start()
        print(f"[*] Command Center Server listening on port {SERVER_PORT}")

    def _run_listener(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind(('127.0.0.1', 8989))
            server.listen(5)
            server.settimeout(1.0) # <--- CRITICAL: Don't block forever
            
            while self.running:
                try:
                    # print("[SERVER] Polling for connections...", flush=True)
                    client_socket, addr = server.accept()
                    print(f"[SERVER] Caught connection from {addr}!", flush=True)
                    
                    client_thread = threading.Thread(
                        target=self._handle_client, 
                        args=(client_socket, addr),
                        daemon=True
                    )
                    client_thread.start()
                except socket.timeout:
                    continue # This allows the thread to yield and loop back
                except Exception as e:
                    print(f"[SERVER ERROR] {e}")

    def _handle_client(self, client_socket, addr):
        """Dedicated function to handle a specific client's data"""
        try:
            with client_socket:
                data = client_socket.recv(4096)
                if data:
                    message = self.sec.decrypt_message(data)
                    # We pass message AND the IP address (addr[0])
                    self._process_message(message, addr[0])
        except Exception as e:
            print(f"[CLIENT HANDLER ERROR] from {addr}: {e}")

    def _process_message(self, decrypted_data, sender_ip): # <--- ADD sender_ip HERE
        """Processes the decrypted string and triggers alerts/UI"""
        try:
            # Splits "ROBOT_1 | CONNECTED: ..."
            robot_id, content = decrypted_data.split(" | ", 1)
            
            # 1. Update GUI via callback
            if self.gui_callback:
                self.gui_callback(robot_id, content)

            # 2. Trigger Phone Notification (The "ntfy" part)
            if "UNAUTHORIZED" in content or "CONNECTED" in content:
                print(f"[NOTIFY] Sending ntfy alert for {robot_id}...", flush=True)
                self.notifier.send_alert(f"Security Alert: {robot_id}", content)
                
            # Log to console for verification
            print(f"[LOG] [{robot_id} @ {sender_ip}] {content}", flush=True)

        except Exception as e:
            print(f"[ERROR] Logic failure in _process_message: {e}")
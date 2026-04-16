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
            server.bind(('0.0.0.0', 8989))
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
                    print(f"[DEBUG] Raw data received from {addr}: {data}") # <--- ADD THIS
                    message = self.sec.decrypt_message(data)
                    print(f"[DEBUG] Decrypted: {message}") # <--- AND THIS
                    self._process_message(message, addr[0])
        except Exception as e:
            print(f"[CLIENT ERROR]: {e}")

    def _process_message(self, decrypted_data, sender_ip):
        try:
            # 1. Parse
            if " | " in decrypted_data:
                robot_id, content = decrypted_data.split(" | ", 1)
            else:
                robot_id = "REMOTE"
                content = decrypted_data

            # 2. LOG IMMEDIATELY (This fixes your empty logs)
            if self.logger:
                self.logger.log_event(f"[{robot_id}] {content}")
            
            if self.db:
                self.db.insert_alert(robot_id, content, sender_ip)

            # 3. UPDATE GUI via after() to be thread-safe
            if self.gui_callback:
                # We use the GUI's root to schedule the update
                # Assuming your gui_callback is bound to gui.update_status
                # We need to make sure update_status is called on the main thread
                self.gui_callback.__self__.root.after(0, lambda: self.gui_callback(robot_id, content))

        except Exception as e:
            print(f"[SERVER ERROR] Process failed: {e}")
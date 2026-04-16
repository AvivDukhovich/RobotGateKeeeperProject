"""
CommandCenterServer - Network Distribution & Alert Hub
This module implements a multi-threaded TCP server designed to receive, 
decrypt, and route security alerts from remote sensor nodes. 

It serves as the central processing unit for the Master node, ensuring 
data is simultaneously pushed to the GUI, local logs, the SQLite database, 
and mobile notifications via ntfy.sh.
"""

import socket
import threading
from secure_socket import SecureSocket
from config import SECRET_KEY, SERVER_PORT

class CommandCenterServer:
    def __init__(self, db_manager, log_manager, notification_manager, gui_callback=None):
        """
        Initializes the server with the necessary managers for data routing.
        
        Args:
            db_manager: Instance for SQLite data persistence.
            log_manager: Instance for flat-file logging.
            notification_manager: Instance for mobile push alerts.
            gui_callback: Reference to the GUI update function (e.g., IdsGUI.update_status).
        """
        self.sec = SecureSocket(key=SECRET_KEY)
        self.db = db_manager
        self.logger = log_manager
        self.notifier = notification_manager
        self.gui_callback = gui_callback
        self.running = True

    def start(self):
        """Spawns the listener thread to allow non-blocking network operations."""
        thread = threading.Thread(target=self._run_listener, daemon=True)
        thread.start()
        print(f"[*] Command Center Server listening on port {SERVER_PORT}")

    def _run_listener(self):
        """
        Main listener loop. Binds to all interfaces and accepts incoming 
        connections from secondary nodes.
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            # Allow immediate reuse of the port after shutdown
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind(('0.0.0.0', 8989))
            server.listen(5)
            server.settimeout(1.0) # Prevents thread lock during shutdown
            
            while self.running:
                try:
                    client_socket, addr = server.accept()
                    print(f"[SERVER] Caught connection from {addr}!", flush=True)
                    
                    # Each client gets a dedicated thread to prevent blocking
                    client_thread = threading.Thread(
                        target=self._handle_client, 
                        args=(client_socket, addr),
                        daemon=True
                    )
                    client_thread.start()
                except socket.timeout:
                    continue 
                except Exception as e:
                    print(f"[SERVER ERROR] {e}")

    def _handle_client(self, client_socket, addr):
        """Handles the reception and decryption of data from a single client."""
        try:
            with client_socket:
                data = client_socket.recv(4096)
                if data:
                    # Decrypt using the shared project SECRET_KEY
                    message = self.sec.decrypt_message(data)
                    self._process_message(message, addr[0])
        except Exception as e:
            print(f"[CLIENT ERROR]: {e}")

    def _process_message(self, decrypted_data, sender_ip):
        """
        The routing engine. Parses the raw string and triggers all active 
        alerting/logging channels.
        
        Format Expected: "ROBOT_ID | ALERT_CONTENT"
        """
        try:
            # 1. Parse incoming data
            if " | " in decrypted_data:
                robot_id, content = decrypted_data.split(" | ", 1)
            else:
                robot_id = "REMOTE"
                content = decrypted_data

            # 2. UPDATE GUI (Thread-safe injection)
            # Uses .after() to ensure the Tkinter main thread handles the draw call
            if self.gui_callback:
                self.gui_callback.__self__.root.after(0, lambda: self.gui_callback(robot_id, content))

            # 3. PHONE NOTIFICATION (ntfy)
            # Sends high-priority push alerts for unauthorized access or new connections
            if self.notifier:
                try:
                    if "UNAUTHORIZED" in content or "CONNECTED" in content:
                        title = f"Security Alert: {robot_id}"
                        self.notifier.send_alert(title, content)
                except Exception as ntfy_e:
                    print(f"[!] Notification failed: {ntfy_e}")

            # 4. LOG TO FILE
            if self.logger:
                self.logger.log(f"[{robot_id}] {content}")

            # 5. SAVE TO DATABASE
            # Records the event in SQLite for later review and analysis
            if self.db:
                db_event_str = f"[{robot_id}] {content}"
                self.db.log_event(sender_ip, db_event_str)

        except Exception as e:
            print(f"[SERVER ERROR] Process failed: {e}")
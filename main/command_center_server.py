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
import time
from secure_socket import SecureSocket
from config import SECRET_KEY, SERVER_PORT


class CommandCenterServer:
    def __init__(self, gui, db_manager, logger, notifier):
        self.gui = gui
        self.db = db_manager
        self.logger = logger
        self.notifier = notifier

        # Centralized State: Source of Truth for all robots
        # { "ROBOT_ID": {"ip": str, "last_seen": float, "status": str} }
        self.active_nodes = {}

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(('0.0.0.0', SERVER_PORT))
        self.server_socket.listen(5)

        # Link the GUI to this server instance
        self.gui.set_server_reference(self)

    def start(self):
        """Starts the main server listener loop in a background thread."""
        threading.Thread(target=self._listen_loop, daemon=True).start()

    def _listen_loop(self):
        print(f"[*] Master Server listening on port {SERVER_PORT}...")
        while True:
            client_sock, addr = self.server_socket.accept()
            # Each connection gets a dedicated handler thread
            threading.Thread(target=self._handle_client, args=(
                client_sock, addr), daemon=True).start()

    def _handle_client(self, client_sock, addr):
        sender_ip = addr[0]

        try:
            # 1. Receive the raw encrypted bytes from the network
            # 1024 bytes is plenty for our small status strings
            encrypted_data = client_sock.recv(1024)

            if encrypted_data:
                # 2. Initialize your encryption tool with the key
                crypto = SecureSocket(key=SECRET_KEY)

                # 3. Decrypt the bytes into a string
                decrypted_data = crypto.decrypt_message(encrypted_data)

                # 4. Process as usual
                self._process_message(decrypted_data, sender_ip)

        except Exception as e:
            print(f"[SERVER ERROR] Failed to handle client {sender_ip}: {e}")
        finally:
            client_sock.close()

    def _process_message(self, data, ip):
        """The core logic gate of the system."""
        try:
            # 1. Parsing Gate
            robot_id, content = data.split(" | ", 1)
            content_upper = content.strip().upper()
        except ValueError:
            return  # Drop malformed packets

        # 2. State Management (Update internal dictionary)
        status = self._determine_status(content_upper)
        self.active_nodes[robot_id] = {
            "ip": ip,
            "last_seen": time.time(),
            "status": status
        }

        # 3. Execution Branching
        if "HEARTBEAT" in content_upper:
            # Heartbeats only refresh the UI 'Network Hub' state
            self.gui.refresh_network_hub(self.active_nodes)
        else:
            # Security Events (UNAUTHORIZED, CONNECTED, etc.)
            self._handle_security_event(robot_id, content, ip, status)

    def _determine_status(self, content):
        if "UNAUTHORIZED" in content:
            return "CRITICAL"
        if "STALE" in content or "LOST" in content:
            return "STALE"
        return "ACTIVE"

    def _handle_security_event(self, robot_id, content, ip, status):
        # 1. Update GUI (Live Monitor)
        self.gui.add_to_monitor(robot_id, content, status)

        # 2. Update Database (Matches your DatabaseManager.log_event)
        full_description = f"[{robot_id}] {content}"
        self.db.log_event(ip, full_description)

        # 3. Update Text Logs (FIX: Changed from log_event to log)
        # Matches your LogManager.log(message)
        self.logger.log(f"{robot_id}@{ip}: {content}")

        # 4. Notify
        if status == "CRITICAL":
            self.notifier.send_push(f"SECURITY BREACH: {robot_id} at {ip}")

    def get_active_nodes(self):
        return self.active_nodes
